# Sprint 4 — Features Delivered

> **Sprint Goal:** Deploy the full IoTDash stack to Azure for a multi-week soak test with 1000 simulated devices at 5-second intervals (~200 msg/s).

---

## Accomplished

### Infrastructure as Code (Terraform)

- **Terraform module** (`infra/soak-test/`) provisions complete Azure environment:
  - Resource group `rg-iotdash-soak`
  - VNet + single subnet
  - NSG with rules for SSH (restricted to caller IP + open for GitHub Actions), HTTP (80), MQTT (1883), backend (8000), frontend (5173), Grafana (3000), EMQX Dashboard (18083)
  - Public IP (Basic SKU, dynamic) with DNS label `iotdash-soak.eastus.cloudapp.azure.com`
  - D2s_v5 VM (2 vCPU, 8 GB RAM, no CPU credit throttling)
  - 128 GB Premium SSD OS disk
- **Cloud-init** automates VM setup on first boot: Docker installation, repo clone, stack startup, simulator launch, cron installation, InfluxDB retention policy, Docker log rotation
- **Teardown script** (`infra/soak-test/teardown.sh`) with confirmation prompt
- **Example tfvars** for quick onboarding
- Total: ~6 Azure resources provisioned

### Production Docker Images

- **Backend** (`backend/Dockerfile.prod`): multi-stage build, Python 3.12 slim base, gunicorn with 2 uvicorn workers, no source mount, no --reload
- **Frontend** (`frontend/Dockerfile.prod`): multi-stage build, Node 20 Alpine → nginx Alpine, gzip compression, static asset caching (1y immutable), SPA routing via try_files, `/api/` reverse proxy to backend container, nginx listens on port 5173
- Both images pushed to ACR as `criotdashsoak.azurecr.io/iotdash-backend` and `criotdashsoak.azurecr.io/iotdash-frontend`

### Docker Compose Soak Override

- **`docker-compose.soak.yml`** overrides dev compose with:
  - Memory limits tuned for 8 GB VM (EMQX 1G, InfluxDB 3G, Grafana 512M, Postgres 512M, Telegraf 256M, Backend 512M, Frontend 256M)
  - Production images for backend + frontend (no source mounts)
  - Telegraf config override (`telegraf.soak.conf`)
  - InfluxDB WAL tuning for sustained writes
  - Mailhog disabled via `profiles: [disabled]`
  - All services: `restart: always`

### Telegraf Soak Configuration

- **`telegraf.soak.conf`**: tuned for ~200 msg/s throughput
  - `metric_batch_size = 10000`, `metric_buffer_limit = 100000`
  - `flush_interval = 5s` with `collection_jitter = 1s`
  - `content_encoding = gzip` for InfluxDB writes
  - Internal metrics input for detecting dropped messages
  - `max_undelivered_messages = 10000` on MQTT consumer

### Async Device Simulator

- **`tools/soak_simulator.py`**: asyncio + aiomqtt simulator
  - CLI args: `--devices`, `--interval`, `--broker`, `--port`, `--ramp-rate`, `--prefix`
  - 1000 devices with staggered connection (5 devices/sec = ~3.3 min ramp)
  - Each device publishes: temperature, humidity, battery, engine_rpm (matching `fake_device.py` schema — time-based drift + noise generators)
  - 5% chance of status message, 1% chance of error condition per publish cycle
  - Exponential backoff reconnect (1s → 60s max) on disconnect
  - Graceful shutdown on SIGINT/SIGTERM with final stats
  - Live stats every 60s: connected count, msg/s, total sent, errors, reconnects
  - Runs as systemd service on the soak VM

### Monitoring & Alerting

- **`tools/soak_monitor.sh`** (cron every 5 min):
  - Collects 21 metrics per row → `/opt/iotdash/soak-metrics.csv`
  - System: CPU%, RAM used/total, disk used/total
  - Per-container memory: emqx, influxdb, telegraf, backend, postgres, grafana
  - EMQX: connection count, message rate (via REST API)
  - InfluxDB: engine disk usage (MB)
  - Docker: restart count per container (crash loop detection)

- **`tools/soak_alerter.sh`** (cron every 15 min):
  - Checks: container restarts, container running status, disk > 80%, RAM > 90%, EMQX connections below threshold, InfluxDB health endpoint
  - Sends alerts via webhook (Slack or ntfy.sh) or logs only if no webhook configured
  - Configurable via `ALERT_WEBHOOK_URL` and `SOAK_MIN_CONNECTIONS` env vars

### CI/CD (GitHub Actions)

- **`soak-deploy.yml`** (manual trigger):
  - Inputs: vm_size, device_count, publish_interval
  - Builds backend + frontend Docker images with Docker Buildx
  - Pushes to ACR with `latest` + commit SHA tags
  - GitHub Actions build cache (`type=gha`) for fast rebuilds
  - SSH deploys to soak VM: git pull, image pull, compose restart, simulator restart
  - Auto-triggers on push to main (backend/frontend/compose/telegraf/workflow paths)

- **`soak-collect.yml`** (manual + weekly schedule):
  - SCP downloads `soak-metrics.csv` from VM
  - Uploads as GitHub Actions artifact (90-day retention)
  - Generates summary in GitHub Actions step summary (data points, date range, last 5 entries)

### Documentation

- Updated `docs/planning/CHEAPEST-SOAK-TEST.md` with 1000-device section, file references, quick start guides
- Updated `docs/planning/TECH-LEAD-PLAYBOOK.md` Sprint 4 section with soak test focus
- Sprint 4 decisions, features, and manual QA documents

---

## Business Value

- **Risk reduction:** Multi-week soak test reveals memory leaks, disk growth, and connection instability *before* committing to a production architecture
- **Cost data:** Establishes actual resource consumption per 1000 devices — informs production sizing and pricing
- **Capacity planning:** Stress tests find the breaking point of a D2s_v5 — determines when to scale up or out
- **Production readiness:** Production Dockerfiles, CI/CD pipeline, and monitoring scripts carry forward to production deployment
- **Reproducibility:** Terraform + cloud-init = one command to recreate the entire test environment

---

## Gaps Remaining

- **No production deployment** — soak test is a staging environment, not customer-facing
- **No HTTPS** — soak VM uses HTTP (acceptable for internal testing)
- **No MQTT auth** — EMQX allows anonymous connections (acceptable for soak test)
- **No secrets management** — hardcoded InfluxDB tokens and Grafana passwords (acceptable for short-lived test infra)
- **No automated analysis** — soak-metrics.csv must be analyzed manually (Excel, Python notebook)
- **~~Frontend VITE_API_URL baked at build time~~** — RESOLVED: frontend now uses empty `VITE_API_URL` (relative URLs) with nginx `/api/` reverse proxy to backend
- **Simulator runs outside Docker** — intentional (tests external connectivity) but means it's not managed by compose
- **No Terraform state backend** — uses local state (fine for single operator, needs remote state for team use)
