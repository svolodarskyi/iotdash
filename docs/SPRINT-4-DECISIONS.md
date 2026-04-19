# Sprint 4 — Technical Decisions

> **Sprint Goal:** Deploy the full IoTDash stack to Azure for a multi-week soak test with 1000 simulated devices at 5-second intervals (~200 msg/s). Find memory leaks, disk growth patterns, connection instability, and breaking points.

---

## D1: Single VM Over Container Apps for Soak Test

**Decision:** Run the entire stack on a single Azure VM (D2s_v5) via docker-compose instead of Azure Container Apps or AKS.

**Why:** A soak test needs to simulate real sustained load at minimum cost. Container Apps adds complexity (TCP ingress for MQTT, managed storage, networking) that isn't needed for a test environment. A single VM with docker-compose is faster to provision, easier to debug (SSH in and inspect), and costs ~EUR 4/day vs ~EUR 8-15/day for equivalent Container Apps setup.

**Revisit:** After soak test results inform the production architecture decision.

---

## D2: D2s_v5 Over B-series VMs

**Decision:** Use `Standard_D2s_v5` (2 vCPU, 8 GB RAM) instead of B2s or B2ms.

**Why:** B-series VMs use CPU credits — under sustained ~200 msg/s load, they'd exhaust credits within hours and throttle to baseline (20-30% of vCPU). The D2s_v5 provides consistent 2 vCPU performance without throttling, which is essential for meaningful soak test data. The cost difference is ~EUR 60/month more, but the results are trustworthy.

---

## D3: Azure Container Registry for Docker Images

**Decision:** Push production Docker images to Azure Container Registry (`criotdashsoak.azurecr.io`) instead of GHCR.

**Why:** ACR is in the same Azure region as the soak VM, so image pulls are fast and free (no egress charges). Basic SKU costs ~EUR 5/month but provides private registry with admin auth. The CI/CD pipeline (GitHub Actions) builds images, pushes to ACR, then deploys to the VM via SSH.

**Note:** Initially planned GHCR for free public pulls, but ACR was chosen for Azure-native integration and simpler auth with the VM's docker login.

---

## D4: Production Dockerfiles Separate from Dev

**Decision:** Create `Dockerfile.prod` alongside existing `Dockerfile` for both backend and frontend, rather than using build args or multi-target Dockerfiles.

**Why:** The dev and prod images are fundamentally different:
- Backend: dev uses `uvicorn --reload` with source mount; prod uses `gunicorn` with baked-in code
- Frontend: dev uses `vite dev` with HMR; prod uses multi-stage `npm build` → nginx

Separate files keep each simple and readable. The soak compose override (`docker-compose.soak.yml`) references `Dockerfile.prod` via the `build.dockerfile` key.

---

## D5: Gunicorn with Uvicorn Workers for Backend

**Decision:** Use `gunicorn` with `uvicorn.workers.UvicornWorker` (2 workers) for the production backend.

**Why:** Gunicorn provides process management (pre-fork model, graceful restarts, worker lifecycle) that raw `uvicorn` lacks. Two workers match the 2 vCPU VM. Uvicorn workers give us async support for the FastAPI endpoints. This is the FastAPI-recommended production setup.

---

## D6: Nginx for Frontend Production Serving

**Decision:** Multi-stage frontend build: `npm run build` → nginx serving static files.

**Why:** Vite's dev server is not production-grade (no gzip, no caching headers, no SPA fallback without middleware). Nginx is a proven static file server with minimal memory footprint (~5 MB), handles SPA routing via `try_files`, and adds gzip + cache headers for static assets.

---

## D7: aiomqtt for Async Device Simulator

**Decision:** Use `aiomqtt` (async wrapper around paho-mqtt) for the soak simulator instead of spawning 1000 threads with paho-mqtt.

**Why:** 1000 concurrent MQTT connections with threads would consume ~2 GB of memory (2 MB stack per thread) and cause thread scheduling overhead. asyncio handles 1000 connections in a single thread with ~100 MB memory. `aiomqtt` provides clean async context managers and reconnect semantics.

---

## D8: Staggered Device Ramp-Up (5 devices/sec)

**Decision:** Stagger device connections at 5 per second (~3.3 minutes to reach 1000) instead of connecting all at once.

**Why:** Connecting 1000 MQTT clients simultaneously creates a thundering herd: EMQX TCP accept queue fills up, kernel connection table thrashes, and many connections timeout. Staggered ramp is how real deployments scale (devices boot at different times). It also lets us observe EMQX behavior under gradual load.

---

## D9: CSV-Based Metrics Collection Over InfluxDB Self-Monitoring

**Decision:** Collect soak test meta-metrics (CPU, RAM, container memory, EMQX stats) into a CSV file via cron, rather than writing them into InfluxDB or a separate monitoring database.

**Why:** The soak test is *testing* InfluxDB — writing monitoring data into the system under test would confound results. A flat CSV is:
- Zero additional dependencies
- Easy to download (`scp` or GitHub Actions artifact)
- Analyzable with any tool (Excel, Python, R)
- Won't be affected if InfluxDB has issues

---

## D10: systemd for Simulator Lifecycle

**Decision:** Run the soak simulator as a systemd service (`soak-simulator.service`) instead of nohup, tmux, or docker container.

**Why:** systemd provides automatic restart on failure, boot-time startup, clean logging via `journalctl`, and graceful shutdown propagation. The simulator runs outside Docker because it simulates external devices connecting to the broker — putting it in docker-compose would bypass the network stack we're trying to test.

---

## D11: 14-Day InfluxDB Retention Policy

**Decision:** Set InfluxDB retention to 14 days (336 hours) for the soak test.

**Why:** At ~200 msg/s with 4 metrics each, we generate ~3 GB/day of InfluxDB data. On a 128 GB disk (shared with OS, Docker images, logs), 14 days gives ~42 GB of time-series data, leaving comfortable headroom. This also lets us observe compaction behavior on data aging out.

**Production:** Will likely be 30-90 days depending on customer tier.

---

## D12: Docker Log Rotation via daemon.json

**Decision:** Configure Docker daemon-level log rotation (50 MB max, 3 files per container) via `/etc/docker/daemon.json` in cloud-init.

**Why:** Without log rotation, container logs under sustained load can fill the disk within days. EMQX and Telegraf are particularly verbose. Daemon-level config applies to all containers automatically, unlike per-container log config in docker-compose which can be missed.

---

## D13: Memory Limits Tuned for 8 GB VM

**Decision:** Set per-container memory limits totaling ~6 GB, leaving ~2 GB for OS + simulator:

| Container | Limit |
|-----------|-------|
| InfluxDB  | 3 GB  |
| EMQX      | 1 GB  |
| Backend   | 512 MB |
| Postgres  | 512 MB |
| Grafana   | 512 MB |
| Telegraf  | 256 MB |
| Frontend  | 256 MB |

**Why:** Without limits, InfluxDB will eagerly consume all available memory for page cache and compaction buffers, starving other services. These limits reflect expected workload: InfluxDB is the heaviest writer, EMQX manages 1000 connections, and the others are relatively lightweight. The ~2 GB OS headroom covers the simulator (~100 MB), kernel buffers, and swap safety margin.
