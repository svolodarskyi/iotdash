# Plan: Soak Test Deployment — IaC, CI/CD, Performance Testing

## Context

We need to deploy the full IoTDash stack to Azure for a soak test: **1000 simulated devices at 5-second publish intervals (~200 msg/s)** running for 2-4 weeks. The goal is to find memory leaks, disk growth patterns, connection instability, and breaking points before committing to a production architecture.

The cheapest approach is a **single Azure VM (D2s_v5)** running the entire stack via docker-compose, with the device simulator running on the same box. Total cost: ~€75-85/month.

We'll build Terraform for the infrastructure, a GitHub Actions pipeline for image builds and deployment, an async device simulator, and an automated metrics collection + alerting system.

### Decisions Made

- **VM:** Standard_D2s_v5 (2 vCPU, 8 GB) — no CPU credit throttling, guaranteed full performance 24/7
- **Image Registry:** Azure Container Registry (Basic tier, ~€5/mo) — same cloud, fast pulls from VM, reusable for production later
- **Repo:** Public — cloud-init can clone directly, no PAT required

---

## Deliverables

### 1. Terraform — Provision Infrastructure

**Directory:** `infra/soak-test/`

**Files:**
- `infra/soak-test/main.tf` — provider config, resource group
- `infra/soak-test/acr.tf` — Azure Container Registry (Basic SKU)
- `infra/soak-test/vm.tf` — VM, NIC, NSG, public IP, OS disk
- `infra/soak-test/variables.tf` — vm_size, location, admin SSH key, acr_name, etc.
- `infra/soak-test/outputs.tf` — VM public IP, SSH command, ACR login server
- `infra/soak-test/cloud-init.yaml` — cloud-init template (install Docker, clone repo, start stack)
- `infra/soak-test/terraform.tfvars.example` — example variable values

**Resources provisioned:**
- Resource group `rg-iotdash-soak`
- Azure Container Registry `criotdashsoak` (Basic SKU)
- VNet + subnet (simple, single subnet for soak test)
- NSG: allow SSH (restricted to caller's IP), 1883 (MQTT), 8000 (backend), 5173 (frontend), 3000 (grafana)
- Public IP (Basic SKU, dynamic)
- VM: `Standard_D2s_v5` (2 vCPU, 8 GB, no CPU credit throttling)
- OS Disk: Premium SSD 128 GB

**VM → ACR authentication:** VM gets a system-assigned Managed Identity with `AcrPull` role on the registry. No passwords needed for `docker pull`.

**Cloud-init will:**
- Install docker, docker-compose-plugin, git, python3, pip
- Log in to ACR using Managed Identity (`az acr login`)
- Clone the repo
- Copy `docker-compose.yml` + `docker-compose.soak.yml` (override)
- Run `docker compose -f docker-compose.yml -f docker-compose.soak.yml up -d`
- Install the monitoring cron job
- Set InfluxDB retention policy (14d)

### 2. Docker Compose Soak Override

**File:** `docker-compose.soak.yml`

Overrides the dev compose with:
- Image references point to ACR (`criotdashsoak.azurecr.io/iotdash-backend:latest`, `criotdashsoak.azurecr.io/iotdash-frontend:latest`)
- Memory limits tuned for 8 GB VM (EMQX 1G, InfluxDB 3G, Grafana 512M, Postgres 512M, Telegraf 256M, Backend 512M, Frontend 256M)
- Telegraf config override: batch_size=10000, flush_interval=5s
- InfluxDB WAL tuning for sustained writes
- Mailhog disabled
- Restart policies: `always`
- Production-like Dockerfiles (no --reload, no dev server)

### 3. Production Dockerfiles

**Files:**
- `backend/Dockerfile.prod` — multi-stage, no --reload, gunicorn with uvicorn workers
- `frontend/Dockerfile.prod` — multi-stage build: npm run build → nginx serving static files

### 4. Async Device Simulator

**File:** `tools/soak_simulator.py`

- asyncio + aiomqtt
- CLI args: `--devices`, `--interval`, `--broker`, `--port`, `--ramp-rate`
- 1000 devices, 5s interval, staggered connection (5 devices/sec = ~3 min ramp)
- Each device publishes: temperature, humidity, battery, engine_rpm (matching existing fake_device.py schema)
- 5% chance of status message, 1% chance of error per cycle
- Graceful shutdown on SIGINT (logs final stats)
- Reconnect logic: exponential backoff on disconnect
- Prints live stats every 60s: connected count, msg/s, errors

### 5. Monitoring & Metrics Collection

**File:** `tools/soak_monitor.sh`

Cron job (every 5 min) that appends to `/opt/iotdash/soak-metrics.csv`:
- Timestamp
- System: CPU%, RAM used/total, disk used/total
- Per-container: memory usage (emqx, influxdb, telegraf, backend, postgres, grafana)
- EMQX: connection count, message rate (via EMQX REST API)
- InfluxDB: engine disk usage, series count
- Docker: restart counts per container (detects crash loops)

**File:** `tools/soak_alerter.sh`

Companion script (also cron, every 15 min) that:
- Checks if any container restarted unexpectedly
- Checks if disk usage > 80%
- Checks if EMQX connections dropped below threshold
- Checks if RAM > 90%
- Sends a simple webhook/email alert (curl to a Slack webhook or ntfy.sh)

### 6. GitHub Actions CI/CD

**File:** `.github/workflows/soak-deploy.yml`

Triggered: manual (`workflow_dispatch`) with inputs for vm_size and device_count

Steps:
1. Authenticate to Azure using service principal (OIDC or secret)
2. Build backend and frontend Docker images
3. Push to Azure Container Registry (`criotdashsoak.azurecr.io`)
4. SSH into the soak VM (using stored SSH key)
5. Pull new images from ACR (VM authenticates via Managed Identity)
6. Restart docker-compose
7. Start/restart the simulator

**File:** `.github/workflows/soak-collect.yml`

Triggered: manual or scheduled (weekly)

Steps:
1. SSH into VM
2. Download `soak-metrics.csv`
3. Upload as GitHub Actions artifact
4. (Optional) post summary to PR/issue

### 7. Teardown Script

**File:** `infra/soak-test/teardown.sh`

```
terraform destroy -auto-approve
```

Plus a reminder in the README: this costs ~€2.50/day, destroy when done.

---

## Cost Estimate

| Resource | SKU | EUR/mo |
|----------|-----|--------|
| VM | D2s_v5 (2 vCPU, 8 GB) | ~€70 |
| OS Disk | Premium SSD 128 GB (P10) | ~€15 |
| Public IP | Basic (dynamic) | ~€3 |
| Azure Container Registry | Basic | ~€5 |
| **Total** | | **~€93** |

---

## Performance Test Strategy

### Phase 1: Baseline (Day 1)

**Goal:** Establish normal operating parameters with 1000 devices @ 5s.

| Metric | How to measure | Expected baseline |
|--------|---------------|-------------------|
| CPU usage | `top` / monitor.sh | 30-50% sustained |
| RAM usage (total) | `free -m` | 5-6 GB of 8 GB |
| EMQX memory | `docker stats` | 200-400 MB |
| InfluxDB memory | `docker stats` | 1-2 GB |
| EMQX connections | EMQX REST API `/api/v5/stats` | 1000 |
| Msg throughput | EMQX REST API `/api/v5/stats` | ~200 msg/s |
| InfluxDB write latency | InfluxDB `/health` + Telegraf internal metrics | <100ms p99 |
| Disk growth rate | `du` on influxdb volume | ~3 GB/day |

### Phase 2: Stability Soak (Days 2-14)

**Goal:** Find slow-growing problems.

| What to watch | Failure mode | Detection |
|--------------|-------------|-----------|
| EMQX memory growth | Session state leak, retained messages accumulating | Linear upward trend in EMQX memory over days |
| InfluxDB compaction storms | Write stalls during compaction | CPU spikes + write latency spikes (correlate in CSV) |
| Telegraf buffer overflow | Dropped messages when InfluxDB is slow | Telegraf internal metrics: `metrics_dropped` counter |
| PostgreSQL connection exhaustion | Backend not releasing connections | Backend errors in logs, pg_stat_activity count |
| Docker log disk growth | Container logs filling disk | `du /var/lib/docker/containers/` |
| Device reconnect storms | Network blip → all 1000 reconnect at once | EMQX connection count spike + CPU spike |

### Phase 3: Stress Tests (Day 14+, manual)

Run these one at a time, observe recovery:

| Test | How | What to observe |
|------|-----|----------------|
| **Connection storm** | Kill simulator, restart (1000 reconnect at once) | Time to re-establish all connections, EMQX CPU spike |
| **InfluxDB restart** | `docker restart influxdb` | Telegraf buffering behavior, data loss check |
| **EMQX restart** | `docker restart emqx` | Device reconnect behavior, message loss during restart |
| **Memory pressure** | Run `stress --vm 1 --vm-bytes 2G` for 5 min | OOM kill priority, which container dies first |
| **Disk full simulation** | Fill disk to 95%, observe behavior | Which service fails first, recovery after cleanup |
| **Network partition** | `tc netem` add 500ms latency + 10% packet loss | MQTT keepalive timeouts, reconnect storms |
| **Sustained burst** | Temporarily set interval to 1s (1000 msg/s) | Where the pipeline saturates first |
| **Backend under load** | Hit API with 50 concurrent requests while devices publish | Does the data plane (MQTT→InfluxDB) degrade? |

### Phase 4: Capacity Ceiling (Day 14+, manual)

Gradually increase device count to find the breaking point of this VM:

```
1000 devices → 1500 → 2000 → 2500 → ...
```

At each step, wait 30 min and record: CPU, RAM, msg/s, write latency. Stop when InfluxDB write latency exceeds 500ms or OOM kills start.

---

## Accesses Needed From You

### Azure

| What | Why | How to provide |
|------|-----|----------------|
| **Azure subscription ID** | Terraform needs it to provision resources | Run `az account show --query id -o tsv` and share the output |
| **Azure tenant ID** | Service principal authentication | Run `az account show --query tenantId -o tsv` |
| **Service principal** (or permission to create one) | Terraform + GitHub Actions auth to Azure | Either create one: `az ad sp create-for-rbac --name sp-iotdash-soak --role Contributor --scopes /subscriptions/<sub-id>` and share the JSON output, or give me permission to create it |
| **SSH public key** | VM access | Share your `~/.ssh/id_rsa.pub` (or I'll generate a keypair) |

### GitHub

| What | Why | How to provide |
|------|-----|----------------|
| **Repo push access** | Push Terraform, CI/CD workflow, simulator code | Confirm the repo is at github.com/\<your-org\>/iotdash and I have push access, or I push to a branch for PR |
| **GitHub Actions enabled** | CI/CD pipeline runs | Usually enabled by default; confirm at repo Settings → Actions |
| **Repository secrets** (5 values) | GitHub Actions authenticates to Azure + VM | After I write the workflow, you set these in repo Settings → Secrets: `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, `SOAK_VM_SSH_KEY` |

### Optional (Nice to Have)

| What | Why |
|------|-----|
| **Slack webhook URL or ntfy.sh topic** | Alerter script sends notifications when something breaks during soak test |
| **Custom domain** (e.g. `soak.iotdash.dev`) | Cleaner than raw IP; not required for testing |

---

## File Summary

| File | Action | Purpose |
|------|--------|---------|
| `infra/soak-test/main.tf` | Create | Terraform provider + resource group |
| `infra/soak-test/acr.tf` | Create | Azure Container Registry |
| `infra/soak-test/vm.tf` | Create | VM, NIC, NSG, public IP, Managed Identity |
| `infra/soak-test/variables.tf` | Create | Configurable inputs |
| `infra/soak-test/outputs.tf` | Create | VM IP, SSH command, ACR login server |
| `infra/soak-test/cloud-init.yaml` | Create | Automated VM setup |
| `infra/soak-test/terraform.tfvars.example` | Create | Example values |
| `docker-compose.soak.yml` | Create | Memory limits, ACR images, tuning |
| `backend/Dockerfile.prod` | Create | Production backend image |
| `frontend/Dockerfile.prod` | Create | Production frontend image (nginx) |
| `tools/soak_simulator.py` | Create | 1000-device async MQTT simulator |
| `tools/soak_monitor.sh` | Create | Metrics collection cron script |
| `tools/soak_alerter.sh` | Create | Threshold alerting script |
| `.github/workflows/soak-deploy.yml` | Create | CI/CD: build, push to ACR, deploy to VM |
| `.github/workflows/soak-collect.yml` | Create | Collect metrics CSV as artifact |
| `telegraf.soak.conf` | Create | Telegraf config tuned for high throughput |
| `docs/planning/CHEAPEST-SOAK-TEST.md` | Edit | Add 1000-device @ 5s section, reference new files |

---

## Verification

1. **Terraform:** `cd infra/soak-test && terraform init && terraform plan` — should show ~8 resources (RG, ACR, VNet, subnet, NSG, PIP, NIC, VM)
2. **ACR push:** `az acr build --registry criotdashsoak --image iotdash-backend:test ./backend -f backend/Dockerfile.prod` — should succeed
3. **Docker build:** `docker build -f backend/Dockerfile.prod -t iotdash-backend:test ./backend` — should succeed locally
4. **Simulator:** Run locally against local docker-compose with 10 devices @ 5s — verify messages appear in InfluxDB
5. **CI/CD:** Trigger `soak-deploy` workflow manually — should build images, push to ACR, SSH into VM, deploy
6. **Monitoring:** After 30 min, check `soak-metrics.csv` has entries with all columns populated
7. **Stress test:** Run connection storm test, verify EMQX recovers to 1000 connections within 5 min
