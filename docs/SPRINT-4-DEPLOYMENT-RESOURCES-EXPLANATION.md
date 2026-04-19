# Sprint 4 — Deployment Resources Explanation

> What each piece of infrastructure does, why it exists, and how the pieces connect.

---

## The Big Picture

The soak test infrastructure is a single Azure VM running the entire IoTDash stack via docker-compose, with 1000 simulated MQTT devices publishing sensor data at 5-second intervals. The goal is to stress the system at ~200 messages/second for 2-4 weeks and observe memory leaks, disk growth, and failure modes.

```
┌─────────────────────────────────────────────────────────────────┐
│  Azure Resource Group: rg-iotdash-soak-eastus                   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  VM: vm-iotdash-soak (Standard_D2as_v6, 2 vCPU, 8 GB)  │   │
│  │                                                          │   │
│  │  Docker Compose Stack:                                   │   │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │   │
│  │  │  EMQX   │→│ Telegraf  │→│ InfluxDB │→│  Grafana   │  │   │
│  │  │  :1883  │ │          │ │  :8086   │ │  :3000     │  │   │
│  │  └────▲────┘ └──────────┘ └──────────┘ └────────────┘  │   │
│  │       │                                                  │   │
│  │  ┌────┴──────────┐  ┌──────────┐  ┌──────────────────┐  │   │
│  │  │ Soak Simulator│  │ Postgres │  │ Backend (FastAPI)│  │   │
│  │  │ (systemd)     │  │  :5432   │  │  :8000           │  │   │
│  │  │ 1000 devices  │  └──────────┘  └──────────────────┘  │   │
│  │  └───────────────┘                ┌──────────────────┐  │   │
│  │                                   │ Frontend (nginx) │  │   │
│  │  Cron: soak_monitor.sh (5 min)    │  :5173 → :80     │  │   │
│  │  Cron: soak_alerter.sh (15 min)   └──────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                         │                                       │
│  ┌──────────────────────▼───────────────────────────────────┐   │
│  │  NIC: nic-iotdash-soak                                   │   │
│  │  ├── Private IP: 10.0.1.x (VNet)                        │   │
│  │  └── Public IP: 13.82.138.72                             │   │
│  │      DNS: iotdash-soak.eastus.cloudapp.azure.com          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                         │                                       │
│  ┌──────────────────────▼───────────────────────────────────┐   │
│  │  NSG: nsg-iotdash-soak                                   │   │
│  │  Inbound rules:                                          │   │
│  │  22(SSH+GHA), 80(HTTP), 1883, 3000, 5173, 8000, 18083    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  ACR: criotdashsoak.azurecr.io                           │   │
│  │  Stores production Docker images for backend + frontend  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Azure Resources — What Each One Does

### 1. Resource Group (`rg-iotdash-soak-eastus`)

**What it is:** A logical container that holds all Azure resources for the soak test.

**Why it exists:** Azure requires every resource to belong to a resource group. Grouping everything under one RG means a single `az group delete` or `terraform destroy` cleans up everything — no orphaned resources, no surprise bills.

**Analogy:** A labeled folder. Delete the folder, everything inside goes with it.

---

### 2. Virtual Network (`vnet-iotdash-soak`) + Subnet (`snet-iotdash-soak`)

**What it is:** A private network (`10.0.0.0/16`) with one subnet (`10.0.1.0/24`) that the VM sits inside.

**Why it exists:** Azure VMs must be placed in a VNet. The VNet provides network isolation — the VM has a private IP (`10.0.1.x`) that isn't directly reachable from the internet. Only traffic explicitly allowed by the NSG can reach the VM.

**Why only one subnet:** A soak test doesn't need network segmentation. One subnet is sufficient. In production you might separate databases, application servers, and public-facing services into different subnets with different NSG rules.

**Analogy:** The VNet is the building. The subnet is a floor. The VM is a room on that floor.

---

### 3. Network Security Group (`nsg-iotdash-soak`)

**What it is:** A firewall that controls inbound and outbound traffic to the VM at the network level.

**Why it exists:** Without an NSG, the VM's public IP would be exposed to the entire internet. The NSG restricts all inbound traffic to your current IP address (`137.186.245.80/32`) only. No one else can reach any port.

**Rules configured:**

| Port | Service | Source | Why it's open |
|------|---------|--------|---------------|
| 22 | SSH | Your IP + `*` (for GitHub Actions) | Remote access to the VM for debugging, management, and CI/CD |
| 80 | HTTP | `*` | Clean URL access to frontend via nginx |
| 1883 | MQTT (EMQX) | Your IP | So you can connect test MQTT clients from your laptop |
| 3000 | Grafana | Your IP | View dashboards and monitoring data in your browser |
| 5173 | Frontend (nginx) | Your IP | Direct access to the IoTDash web application |
| 8000 | Backend (FastAPI) | Your IP | Direct API access for testing |
| 18083 | EMQX Dashboard | Your IP | Monitor MQTT connections, message rates, client status |

**Security notes:**
- Most rules use `source_address_prefix = your_ip/32`. If your IP changes, update the terraform variable `allowed_ssh_cidr` and re-apply.
- SSH is also open to all IPs (priority 110) for GitHub Actions CI/CD. This is safe because the VM uses SSH key authentication only (no password).
- HTTP (port 80) is open to all IPs — it serves the public-facing frontend.

**Analogy:** A security guard at the building entrance with a guest list. Only your name is on the list.

---

### 4. Public IP (`pip-iotdash-soak`)

**What it is:** A public IPv4 address (`13.82.138.72`) attached to the VM so you can reach it from the internet. A DNS label (`iotdash-soak`) is configured, giving the VM a stable hostname: `iotdash-soak.eastus.cloudapp.azure.com`.

**Why Dynamic + Basic SKU:** Dynamic IPs are free when allocated to a running VM. Basic SKU is the cheapest option. The IP may change if the VM is deallocated and restarted (not rebooted — full stop/start). The DNS label provides a stable hostname that automatically resolves to the current IP, so services remain accessible even if the IP changes.

**DNS label:** Free Azure feature. The format is `<label>.<region>.cloudapp.azure.com`. No custom domain or DNS zone required.

**What it enables:** SSH access, browser access to Grafana/frontend/backend, MQTT client connections from your laptop — all via DNS hostname or IP.

**Analogy:** The building's street address, with a permanent name plate that stays even if the building number changes.

---

### 5. Network Interface (`nic-iotdash-soak`) + NSG Association

**What it is:** The virtual network card of the VM. It has two IP addresses: a private one (inside the VNet) and the public one (from the Public IP resource). The NSG is associated with this NIC.

**Why it exists:** Azure networking is modular — the VM, its network card, its public IP, and its firewall rules are all separate resources that get linked together. This lets you swap out or reconfigure any piece independently (e.g. move the public IP to a different VM).

**The NSG Association** is a separate resource that links the NSG to the NIC. Without it, the firewall rules wouldn't apply.

**Analogy:** The NIC is the ethernet port on the VM. The NSG association is plugging the firewall into that port.

---

### 6. Linux Virtual Machine (`vm-iotdash-soak`)

**What it is:** An Ubuntu 24.04 LTS server running the entire IoTDash stack.

**Spec: Standard_D2as_v6**
- 2 vCPUs (AMD EPYC, no CPU credit throttling)
- 8 GB RAM
- 128 GB Premium SSD OS disk

**Why D2as_v6 (not B-series):** B-series VMs (B2s, B2ms) use CPU credits. Under sustained ~200 msg/s load, they exhaust credits within hours and throttle to 20-30% of a vCPU. The D-series provides consistent performance — essential for meaningful soak test results. We originally planned D2s_v5 (Intel) but the subscription had zero quota for that family; D2as_v6 (AMD) has the same specs and was available.

**Why 128 GB disk:** InfluxDB generates ~3 GB/day of time-series data. With 14-day retention, that's ~42 GB. Plus Docker images (~5 GB), OS (~4 GB), logs, and headroom. 128 GB gives comfortable margin for a multi-week test.

**Why Premium SSD:** InfluxDB does frequent random writes (WAL) and compaction (sequential reads/writes). Premium SSD provides consistent IOPS (500 IOPS for P10). Standard HDD would bottleneck under sustained write load.

**Cloud-init (custom_data):** A script that runs on first boot and automates all setup — see the cloud-init section below.

**SSH access:** Key-based auth only (no password). Uses the RSA 4096 key generated at `~/.ssh/iotdash-soak`.

**Analogy:** The actual computer. Everything else (VNet, NSG, NIC, IP) is just the networking infrastructure around it.

---

### 7. Azure Container Registry (`criotdashsoak`)

**What it is:** A private Docker image registry at `criotdashsoak.azurecr.io`. Stores the production-built backend and frontend Docker images.

**Why it exists:** The CI/CD pipeline (GitHub Actions) builds Docker images and needs somewhere to push them. The soak VM then pulls these images. ACR is in the same Azure region as the VM, so pulls are fast and free (no egress charges within the same region).

**Why Basic SKU:** Cheapest tier (~$5/month). Provides 10 GB storage, which is more than enough for two images. No geo-replication or advanced features needed for a test environment.

**Why admin enabled:** Simplest authentication method — a username/password that can be used in `docker login`. For production, you'd use service principal or managed identity auth. For a short-lived soak test, admin auth is fine.

**How it's used:**
1. GitHub Actions builds `iotdash-backend` and `iotdash-frontend` images from `Dockerfile.prod`
2. Pushes them to `criotdashsoak.azurecr.io/iotdash-backend:latest` and `criotdashsoak.azurecr.io/iotdash-frontend:latest`
3. The VM's `docker-compose.soak.yml` references these images
4. On deploy, the VM pulls the latest images and restarts the stack

**Analogy:** A private app store for your Docker images.

---

## Cloud-Init — What Happens on First Boot

Cloud-init is a script baked into the VM's `custom_data` that runs automatically on first boot. It turns a bare Ubuntu VM into a fully running soak test environment in ~5 minutes, with zero manual SSH intervention.

| Order | Action | Why |
|-------|--------|-----|
| 1 | Install packages (docker, git, python3, jq) | VM starts with just the OS — needs tooling |
| 2 | Configure Docker log rotation | Without this, container logs fill the disk within days under 200 msg/s |
| 3 | `docker login` to ACR | VM needs to pull production images from the private registry |
| 4 | Clone the git repo to `/opt/iotdash` | Gets the docker-compose files, configs, monitoring scripts |
| 5 | `docker compose up -d --build` | Starts the full stack: EMQX, Telegraf, InfluxDB, Grafana, Postgres, backend, frontend |
| 6 | Create Python venv + install aiomqtt | Simulator dependency — can't use system pip on Ubuntu 24.04 |
| 7 | Create systemd service `soak-simulator` | Runs the 1000-device simulator as a managed service (auto-restart, logging via journalctl) |
| 8 | Set up cron jobs | `soak_monitor.sh` every 5 min, `soak_alerter.sh` every 15 min |
| 9 | Set InfluxDB retention to 14 days | Prevents disk from filling indefinitely — old data ages out |

---

## Docker Compose Soak Override — What It Changes

`docker-compose.soak.yml` is layered on top of the base `docker-compose.yml`. It overrides settings for production-like behavior on the 8 GB VM.

| Override | Base (dev) | Soak (prod) | Why |
|----------|-----------|-------------|-----|
| Backend image | Builds from `Dockerfile` (uvicorn --reload) | Builds from `Dockerfile.prod` (gunicorn + uvicorn workers) | No hot-reload overhead, proper process management |
| Frontend image | Builds from `Dockerfile` (vite dev server) | Builds from `Dockerfile.prod` (nginx static files) | ~5 MB memory vs ~200 MB, proper caching headers |
| Source mounts | `./backend:/app`, `./frontend:/app` | `volumes: []` (none) | Code is baked into the image, no host filesystem dependency |
| Memory limits | None (unlimited) | Per-container limits totaling ~6 GB | Prevents InfluxDB from consuming all RAM and OOM-killing others |
| Telegraf config | `telegraf.conf` (1s interval, small batches) | `telegraf.soak.conf` (5s interval, 10000 batch size, gzip) | Tuned for ~200 msg/s throughput without overwhelming InfluxDB |
| Restart policy | `unless-stopped` or none | `always` | Services restart after crashes or VM reboots |
| Mailhog | Running (SMTP catcher) | `profiles: [disabled]` | Not needed, saves ~50 MB RAM |
| InfluxDB | Default WAL settings | WAL tuning (fsync delay, snapshot size, compaction) | Handles sustained write load without stalling |

---

## Production Dockerfiles — What They Build

### `backend/Dockerfile.prod`

```
Stage 1 (builder): python:3.12-slim + gcc + libpq-dev → pip install all deps
Stage 2 (runtime): python:3.12-slim + libpq5 only → copy installed packages + app code
```

- **Multi-stage** keeps the final image small (~150 MB vs ~400 MB with build tools)
- **Gunicorn** with 2 uvicorn workers provides process management (pre-fork, graceful restart, worker lifecycle)
- No `--reload`, no source mount — code is baked in at build time

### `frontend/Dockerfile.prod`

```
Stage 1 (builder): node:20-alpine → npm ci + npm run build (TypeScript → static JS/CSS/HTML)
Stage 2 (runtime): nginx:alpine → copy /app/dist to nginx html root
```

- **Multi-stage** goes from ~1 GB (node_modules) to ~25 MB (just nginx + static files)
- **Nginx** handles: gzip compression, cache headers (1 year for hashed assets), SPA routing (`try_files → /index.html`)
- `VITE_GRAFANA_URL` is baked in at build time via build arg
- API calls use relative URLs (empty `VITE_API_URL`) — nginx proxies `/api/` to the backend container, avoiding build-time dependency on server IP

---

## Monitoring & Alerting — What They Collect

### `soak_monitor.sh` (every 5 min → CSV)

Appends one row of 21 metrics to `/opt/iotdash/soak-metrics.csv`:

| Category | Metrics | Purpose |
|----------|---------|---------|
| System | CPU%, RAM used/total, disk used/total | Detect resource exhaustion trends |
| Per-container memory | emqx, influxdb, telegraf, backend, postgres, grafana (MB) | Detect memory leaks in specific services |
| EMQX | Connection count, message rate | Confirm all 1000 devices are connected, throughput is stable |
| InfluxDB | Engine disk usage (MB) | Track data growth rate, predict when disk fills |
| Docker | Restart count per container | Detect crash loops (OOM kills, panics) |

### `soak_alerter.sh` (every 15 min → webhook)

Checks for failure conditions and sends alerts:

| Check | Threshold | What it catches |
|-------|-----------|-----------------|
| Container restarts | Any restart > 0 | OOM kills, crashes, panics |
| Container status | Not "running" | Complete service failure |
| Disk usage | > 80% | Approaching disk full |
| RAM usage | > 90% | Memory pressure, imminent OOM |
| EMQX connections | < 500 (configurable) | Mass device disconnection |
| InfluxDB health | Not "pass" | Database failure |

---

## CI/CD Pipelines — What They Do

### `soak-deploy.yml` (manual trigger + auto on push to main)

```
Push to main (or click "Run workflow" on GitHub)
        │
        ▼
┌─────────────────────┐     ┌──────────────────────┐
│ Job 1: Build & Push  │     │ Job 2: Deploy         │
│                     │     │ (runs after Job 1)    │
│ 1. Checkout code    │     │ 1. SSH into soak VM   │
│ 2. Login to ACR     │────▶│ 2. git pull latest    │
│ 3. Build backend    │     │ 3. sudo docker pull   │
│ 4. Build frontend   │     │ 4. sudo docker compose│
│ 5. Push to ACR      │     │ 5. Restart simulator  │
└─────────────────────┘     └──────────────────────┘
```

### `soak-collect.yml` (manual or weekly Monday 06:00 UTC)

```
1. SSH into VM
2. SCP download soak-metrics.csv
3. Upload as GitHub Actions artifact (90-day retention)
4. Print summary (data points, date range, last 5 rows)
```

---

## Telegraf Soak Config — What Changed

| Setting | Dev (`telegraf.conf`) | Soak (`telegraf.soak.conf`) | Why |
|---------|----------------------|----------------------------|-----|
| `interval` | 1s | 5s | Matches device publish interval, reduces write frequency |
| `flush_interval` | 1s | 5s | Batch writes to InfluxDB instead of per-message |
| `metric_batch_size` | default (1000) | 10000 | Larger batches = fewer HTTP requests to InfluxDB |
| `metric_buffer_limit` | default (10000) | 100000 | Buffer during InfluxDB compaction pauses |
| `content_encoding` | none | gzip | Reduces network bandwidth for InfluxDB writes |
| `max_undelivered_messages` | default | 10000 | MQTT consumer won't drop messages during slow flushes |
| Internal metrics | none | enabled | Detect `metrics_dropped` counter (Telegraf's own health) |

---

## Device Simulator — How It Works

`tools/soak_simulator.py` uses Python asyncio to run 1000 concurrent MQTT clients in a single process.

**Why asyncio (not threads):** 1000 threads would consume ~2 GB (2 MB stack each) and cause context-switching overhead. Asyncio handles all 1000 connections in ~100 MB with cooperative multitasking.

**Ramp-up:** Connects 5 devices/second (3.3 min to reach 1000). Prevents a thundering herd that would overwhelm EMQX's TCP accept queue.

**Per device, every 5 seconds:**
1. Generate metrics matching `fake_device.py` schema: `temperature`, `humidity`, `engine_rpm`, `battery`
2. 5% chance: add a `status` field (nominal/warning/maintenance_due)
3. 1% chance: add an `error` field (sensor_timeout/calibration_drift/low_signal/overtemp)
4. Publish to `{device_id}/from/message` (QoS 0)

**Reconnect:** On disconnect, exponential backoff from 1s to 60s max. Simulates real device behavior on network interruptions.

**Runs as systemd service:** Auto-start on boot, restart on failure, logs via `journalctl -u soak-simulator`.
