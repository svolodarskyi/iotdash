# Sprint 4 — Manual QA Checklist

> **Sprint Goal:** Verify soak test infrastructure, production images, simulator, monitoring, and CI/CD pipeline.

---

## Prerequisites

```bash
# Local environment running
docker compose up -d
docker compose ps   # all services healthy

# Python deps for simulator
pip install aiomqtt

# Terraform installed (for infra validation)
terraform --version  # >= 1.5
```

---

## 1. Production Docker Images

### 1.1 Backend Production Build

```bash
docker build -f backend/Dockerfile.prod -t iotdash-backend:test ./backend
```

- [ ] Build completes without errors
- [ ] Image uses multi-stage build (check with `docker history iotdash-backend:test` — no gcc/build tools in final layer)
- [ ] Image runs:
  ```bash
  docker run --rm -p 8001:8000 \
    -e DATABASE_URL=postgresql://iotdash:iotdash_dev@host.docker.internal:5432/iotdash \
    -e INFLUXDB_URL=http://host.docker.internal:8086 \
    iotdash-backend:test
  ```
- [ ] `curl localhost:8001/api/health` returns `{"status":"ok"}`
- [ ] No `--reload` in process list (`docker exec <id> ps aux` — should show gunicorn master + workers)
- [ ] Stop container, clean up

### 1.2 Frontend Production Build

```bash
docker build -f frontend/Dockerfile.prod -t iotdash-frontend:test ./frontend
```

- [ ] Build completes without errors (TypeScript compilation + Vite build)
- [ ] Image runs:
  ```bash
  docker run --rm -p 8080:80 iotdash-frontend:test
  ```
- [ ] `curl -I localhost:8080` returns `200 OK` with nginx headers
- [ ] `curl localhost:8080` returns HTML (index.html)
- [ ] `curl localhost:8080/nonexistent-route` returns index.html (SPA fallback working)
- [ ] `curl -I localhost:8080/assets/` — check for cache headers (`Cache-Control: public, immutable`)
- [ ] Stop container, clean up

### 1.3 Soak Compose Override

```bash
docker compose -f docker-compose.yml -f docker-compose.soak.yml config --quiet
```

- [ ] Config merges without errors
- [ ] Verify merged config shows:
  ```bash
  docker compose -f docker-compose.yml -f docker-compose.soak.yml config | grep -A2 "mem_limit\|memory"
  ```
  - [ ] InfluxDB has 3G memory limit
  - [ ] EMQX has 1G memory limit
  - [ ] Backend uses `Dockerfile.prod`
  - [ ] Frontend uses `Dockerfile.prod`
  - [ ] Mailhog has `profiles: [disabled]`
  - [ ] All services have `restart: always`

---

## 2. Device Simulator

### 2.1 Local Test (10 devices)

```bash
python tools/soak_simulator.py --devices 10 --interval 5 --broker localhost --port 1883 --ramp-rate 10
```

- [ ] Simulator starts without errors
- [ ] Shows "Starting soak simulator: 10 devices @ 5.0s interval" message
- [ ] All 10 devices connect (first STATS line shows `connected=10`)
- [ ] Stats print every 60 seconds with msg/s > 0
- [ ] Verify data reaches InfluxDB:
  ```bash
  docker exec influxdb influx query \
    --org iotorg --token mytoken123 \
    'from(bucket:"iot") |> range(start:-1m) |> filter(fn:(r) => r.device_id =~ /soak-device/) |> count()' 2>/dev/null
  ```
- [ ] Ctrl+C triggers graceful shutdown with "FINAL STATS" line
- [ ] Final stats show total messages sent, average rate, errors

### 2.2 CLI Arguments

- [ ] `--prefix custom` produces device IDs like `custom-device-0000`
- [ ] `--ramp-rate 2` produces slower ramp (should take ~5s for 10 devices)
- [ ] `--help` shows all available arguments

### 2.3 Reconnect Behavior

```bash
# Start simulator
python tools/soak_simulator.py --devices 5 --interval 5 --broker localhost &
SIM_PID=$!

# Wait for connections
sleep 10

# Restart EMQX to force disconnects
docker restart emqx

# Wait for reconnect
sleep 30

# Check stats — should show reconnects > 0, connected=5
# Press Ctrl+C or kill $SIM_PID
```

- [ ] Simulator logs "disconnected... retrying" messages
- [ ] Devices reconnect after EMQX comes back
- [ ] Stats show `reconnects > 0`
- [ ] Connected count returns to 5

---

## 3. Monitoring Scripts

### 3.1 soak_monitor.sh

```bash
# Run once locally (set output to temp file)
SOAK_METRICS_FILE=/tmp/soak-test-metrics.csv bash tools/soak_monitor.sh
```

- [ ] Script runs without errors (note: `free` and `top` commands differ on macOS — test on Linux or skip)
- [ ] CSV file created with header row
- [ ] Second run appends data row (not another header)
- [ ] CSV has 21 columns: timestamp through docker_restarts_grafana
- [ ] Container memory values are numeric (not empty)
- [ ] EMQX connections value > 0 (if simulator is running)

### 3.2 soak_alerter.sh

```bash
# Run with no webhook (logs only)
ALERT_WEBHOOK_URL="" bash tools/soak_alerter.sh
```

- [ ] Script runs without errors
- [ ] Outputs "All checks passed" if everything is healthy
- [ ] Stop a container and re-run:
  ```bash
  docker stop grafana
  bash tools/soak_alerter.sh
  # Should report "Container 'grafana' is NOT running"
  docker start grafana
  ```
- [ ] Reports stopped container
- [ ] With `SOAK_MIN_CONNECTIONS=99999`, reports "EMQX connections dropped"

---

## 4. Terraform Validation

```bash
cd infra/soak-test
```

### 4.1 Configuration

- [ ] `terraform.tfvars.example` exists with documented example values
- [ ] All variables have descriptions in `variables.tf`
- [ ] `admin_ssh_public_key` and `allowed_ssh_cidr` have no defaults (must be provided)

### 4.2 Init & Plan (no apply)

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with test values (won't apply, just validate)

terraform init
```

- [ ] Init downloads azurerm provider successfully
- [ ] `terraform validate` passes
- [ ] `terraform plan` shows ~6 resources to create (with valid Azure credentials):
  - Resource group
  - VNet
  - Subnet
  - NSG
  - NIC + NSG association
  - Public IP
  - VM

### 4.3 Cloud-init Template

- [ ] `cloud-init.yaml` is valid YAML
- [ ] Contains Docker installation steps
- [ ] Contains repo clone step
- [ ] Contains docker compose up command
- [ ] Contains systemd service for simulator
- [ ] Contains cron setup for monitor + alerter
- [ ] Contains InfluxDB retention policy command
- [ ] Contains Docker log rotation config

### 4.4 Teardown Script

- [ ] `infra/soak-test/teardown.sh` is executable
- [ ] Script prompts for confirmation before destroying
- [ ] Typing anything other than "yes" aborts

---

## 5. GitHub Actions Workflows

### 5.1 soak-deploy.yml

- [ ] File exists at `.github/workflows/soak-deploy.yml`
- [ ] Trigger: `workflow_dispatch` with inputs (vm_size, device_count, publish_interval)
- [ ] Job 1 (`build-and-push`):
  - [ ] Logs into GHCR
  - [ ] Builds backend with `Dockerfile.prod`
  - [ ] Builds frontend with `Dockerfile.prod`
  - [ ] Pushes both with `latest` + SHA tags
  - [ ] Uses build cache (`type=gha`)
- [ ] Job 2 (`deploy`):
  - [ ] Depends on `build-and-push`
  - [ ] SSH into VM using secrets
  - [ ] Pulls new images, restarts compose, restarts simulator

### 5.2 soak-collect.yml

- [ ] File exists at `.github/workflows/soak-collect.yml`
- [ ] Triggers: `workflow_dispatch` + weekly schedule (Monday 06:00 UTC)
- [ ] Downloads CSV via SCP
- [ ] Uploads as artifact with 90-day retention
- [ ] Generates step summary with data point count and last 5 entries

### 5.3 Required Secrets

Verify these secrets are documented (to be set in repo Settings → Secrets):

- [ ] `SOAK_VM_HOST` — VM public IP
- [ ] `SOAK_VM_SSH_KEY` — private SSH key for VM access

---

## 6. Documentation

- [ ] `docs/planning/CHEAPEST-SOAK-TEST.md` has "Production Soak Test: 1000 Devices" section
- [ ] Section includes file table referencing all new files
- [ ] Quick start guides for Terraform and GitHub Actions
- [ ] `docs/planning/TECH-LEAD-PLAYBOOK.md` Sprint 4 updated with soak test focus
- [ ] Sprint cadence table updated

---

## 7. End-to-End Demo Flow

This is the full flow to verify the soak test setup works locally:

```bash
# 1. Start the full stack with soak overrides
docker compose -f docker-compose.yml -f docker-compose.soak.yml up -d --build

# 2. Wait for services to be healthy
docker compose -f docker-compose.yml -f docker-compose.soak.yml ps

# 3. Run simulator with 10 devices (local test)
python tools/soak_simulator.py --devices 10 --interval 5 --broker localhost &

# 4. Wait 2 minutes for data to flow

# 5. Verify data in InfluxDB
docker exec influxdb influx query \
  --org iotorg --token mytoken123 \
  'from(bucket:"iot") |> range(start:-5m) |> filter(fn:(r) => r.device_id =~ /soak/) |> group() |> count()'

# 6. Check Grafana shows data
open http://localhost:3000

# 7. Run monitor script
SOAK_METRICS_FILE=/tmp/test-metrics.csv bash tools/soak_monitor.sh
cat /tmp/test-metrics.csv

# 8. Run alerter script
bash tools/soak_alerter.sh

# 9. Graceful shutdown
kill %1  # stop simulator
docker compose -f docker-compose.yml -f docker-compose.soak.yml down
```

- [ ] All steps complete without errors
- [ ] InfluxDB has soak device data
- [ ] Grafana dashboard shows metrics
- [ ] Monitor CSV has valid data
- [ ] Alerter reports healthy status

---

## 8. Troubleshooting

### Simulator can't connect to MQTT

```bash
# Check EMQX is running and healthy
docker exec emqx emqx ctl status

# Check port is accessible
nc -zv localhost 1883

# Check EMQX logs for connection errors
docker logs emqx --tail 20
```

### Monitor script fails on macOS

The `free`, `top`, and `df` commands have different syntax on macOS vs Linux. The monitor and alerter scripts are designed for Linux (the soak VM). For local testing on macOS, expect some commands to fail — this is expected.

### Frontend Dockerfile.prod build fails

```bash
# Check if TypeScript compilation succeeds locally first
cd frontend && npm run build

# Common issue: TypeScript errors that are ignored by dev server but fail in CI
# Fix the TS errors, then rebuild the image
```

### docker-compose.soak.yml merge issues

```bash
# Validate the merged config
docker compose -f docker-compose.yml -f docker-compose.soak.yml config

# Look for:
# - Missing volume declarations
# - Port conflicts (frontend maps 5173:80 in soak, 5173:5173 in dev)
# - Image vs build conflicts
```
