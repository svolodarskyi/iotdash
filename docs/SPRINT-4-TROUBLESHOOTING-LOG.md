# Sprint 4 — Troubleshooting Log

> **Date:** 2026-04-17 / 2026-04-18
> **VM:** `13.82.138.72` / `iotdash-soak.eastus.cloudapp.azure.com` (Standard_D2as_v6, eastus)

---

## Issue 1: Frontend Not Reachable (http://13.82.138.72:5173)

### Symptom

After Terraform provisioned the VM and cloud-init completed, navigating to `http://13.82.138.72:5173` returned "site can't be reached" (connection refused).

### Investigation

1. **SSH into VM to check cloud-init status:**

   ```bash
   ssh -i ~/.ssh/iotdash-soak azureuser@13.82.138.72 'cloud-init status'
   # Result: status: done
   ```

2. **Checked if any containers were running:**

   ```bash
   docker ps
   # Result: empty — no containers running at all
   ```

3. **Checked cloud-init logs:**

   ```bash
   sudo tail -50 /var/log/cloud-init-output.log
   ```

   Found the root cause:

   ```
   fatal: could not read Username for 'https://github.com': No such device or address
   ```

### Root Cause

The GitHub repository (`https://github.com/svolodarskyi/iotdash.git`) was **private**. Cloud-init tried to `git clone` via HTTPS without credentials, which failed silently (cloud-init continued but the repo was never cloned). No `/opt/iotdash` directory existed, so `docker compose up` never ran.

### Fix

1. **Made the GitHub repo public** (user action)
2. **Manually cloned the repo on the VM:**

   ```bash
   sudo rm -rf /opt/iotdash   # Remove empty directory left by failed clone
   sudo git clone https://github.com/svolodarskyi/iotdash.git /opt/iotdash
   ```

3. **Started the docker compose stack:**

   ```bash
   cd /opt/iotdash
   sudo docker compose -f docker-compose.yml -f docker-compose.soak.yml up -d --build
   ```

### Lesson Learned

If the repo is private, cloud-init needs a GitHub deploy key or PAT embedded in the clone URL. For soak testing, making the repo public was the simplest fix.

---

## Issue 2: Frontend Container Port Conflict (port 5173 already allocated)

### Symptom

After cloning the repo and running `docker compose up`, all containers started **except frontend**, which failed with:

```
Error response from daemon: failed to set up container networking:
driver failed programming external connectivity on endpoint frontend:
Bind for 0.0.0.0:5173 failed: port is already allocated
```

### Investigation

1. **Checked what was using port 5173:**

   ```bash
   sudo ss -tlnp | grep 5173
   sudo lsof -i :5173
   # Both returned nothing — no process was listening on 5173
   ```

2. **Checked container status:**

   ```bash
   docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
   # frontend showed "Created" status (never started)
   ```

3. **Inspected the container's port bindings:**

   ```bash
   docker inspect frontend --format "{{json .HostConfig.PortBindings}}"
   ```

   Output:
   ```json
   {"5173/tcp":[{"HostIp":"","HostPort":"5173"}],"80/tcp":[{"HostIp":"","HostPort":"5173"}]}
   ```

   **Two different container ports (5173 and 80) were both mapped to host port 5173.**

4. **Identified the source — Docker Compose port merging:**

   - `docker-compose.yml` (base) defined:
     ```yaml
     frontend:
       ports:
         - "5173:5173"   # Vite dev server
     ```

   - `docker-compose.soak.yml` (override) defined:
     ```yaml
     frontend:
       ports:
         - "5173:80"     # nginx serves on port 80
     ```

   Docker Compose **merges** port arrays from override files rather than replacing them. So the resulting config had both `5173:5173` AND `5173:80`, meaning host port 5173 was double-bound.

5. **First attempted fix — restart Docker daemon:**

   ```bash
   sudo systemctl restart docker
   docker compose -f docker-compose.yml -f docker-compose.soak.yml up -d
   ```

   This worked temporarily (Docker cleared the ghost port binding), but the underlying double-mapping issue remained.

### Root Cause

Docker Compose merges `ports` arrays across base and override files. Both `5173:5173` (base, for Vite dev server) and `5173:80` (soak override, for nginx) ended up in the final config. Docker tried to bind host port 5173 twice — once for container port 5173 and once for container port 80 — causing the conflict.

### Fix

Two changes to eliminate the conflict:

1. **Changed `frontend/Dockerfile.prod`** — nginx now listens on port 5173 instead of port 80:

   ```diff
   - listen 80;
   + listen 5173;
   ```

   ```diff
   - EXPOSE 80
   + EXPOSE 5173
   ```

2. **Removed the `ports` override from `docker-compose.soak.yml`** — the base mapping `5173:5173` now works for both dev (Vite) and prod (nginx on 5173):

   ```diff
     frontend:
       image: ${ACR_LOGIN_SERVER:-criotdashsoak.azurecr.io}/iotdash-frontend:latest
       build:
         context: ./frontend
         dockerfile: Dockerfile.prod
   -   ports:
   -     - "5173:80"
       volumes: []
   ```

After this fix, only one port mapping exists (`5173:5173` from the base compose), and nginx inside the container listens on 5173 to match.

### Lesson Learned

Docker Compose override files **merge** list-type fields (`ports`, `volumes`, `environment`) rather than replacing them. When overriding a service's port mappings, either:
- Match the same container port as the base file (so the merge is harmless)
- Use `!override` (Compose v2.24+) to replace instead of merge
- Avoid duplicate host port bindings across base and override

---

## Issue 3: Docker Restart Cleared Ghost Port Binding

### Symptom

After the initial port conflict error, checking `ss` and `lsof` showed nothing listening on port 5173, yet Docker still reported "port already allocated" when trying to start the frontend container.

### Root Cause

Docker's internal port allocation table had a stale entry from the failed container creation. Even though no process was listening, Docker's proxy tracked the port as allocated.

### Fix

```bash
sudo systemctl restart docker
```

This cleared Docker's internal port allocation state. After restarting the daemon, all containers (including frontend) started successfully.

### Note

This was a temporary workaround — the real fix was eliminating the double port mapping (Issue 2 above). Without fixing the root cause, the conflict would recur on every `docker compose up`.

---

## Issue 4: Simulator and Monitoring Not Running After Manual Clone

### Symptom

After manually cloning the repo and starting docker compose, the soak simulator and monitoring cron jobs were not running. These were supposed to be set up by cloud-init.

### Root Cause

Cloud-init runs once on first boot. Since the `git clone` step failed (Issue 1), all subsequent cloud-init steps that depended on the repo also failed:
- Python venv creation (partially succeeded — created `.venv` but no packages installed)
- Systemd service for simulator (not created)
- Cron jobs for monitoring/alerting (not created)
- InfluxDB retention policy (not set)

### Fix

Manually ran the setup steps that cloud-init would have done:

1. **Created Python venv and installed dependencies:**

   ```bash
   sudo python3 -m venv /opt/iotdash/.venv
   sudo /opt/iotdash/.venv/bin/pip install aiomqtt pyyaml
   ```

2. **Created systemd service for simulator:**

   ```bash
   sudo cat > /etc/systemd/system/soak-simulator.service <<EOF
   [Unit]
   Description=IoTDash Soak Test Simulator
   After=docker.service
   Requires=docker.service

   [Service]
   Type=simple
   ExecStartPre=/bin/sleep 60
   ExecStart=/opt/iotdash/.venv/bin/python /opt/iotdash/tools/soak_simulator.py --devices 1000 --interval 5 --broker localhost --port 1883
   Restart=on-failure
   RestartSec=30

   [Install]
   WantedBy=multi-user.target
   EOF

   sudo systemctl daemon-reload
   sudo systemctl enable soak-simulator
   sudo systemctl start soak-simulator
   ```

3. **Set up monitoring cron jobs:**

   ```bash
   sudo chmod +x /opt/iotdash/tools/soak_monitor.sh /opt/iotdash/tools/soak_alerter.sh
   sudo crontab -l 2>/dev/null; \
     echo "*/5 * * * * /opt/iotdash/tools/soak_monitor.sh"; \
     echo "*/15 * * * * /opt/iotdash/tools/soak_alerter.sh") | sudo crontab -
   ```

4. **Scheduled InfluxDB 14-day retention policy** (with 90s delay for services to fully start).

---

## Issue 5: CI/CD SSH Timeout — GitHub Actions Runners Blocked by NSG

### Symptom

GitHub Actions workflow `soak-deploy.yml` failed at the SSH deploy step with `ssh: connect to host ... port 22: Connection timed out`.

### Root Cause

The NSG only allowed SSH from the developer's IP (`137.186.245.80/32`). GitHub Actions runners use unpredictable IPs across wide Azure/Microsoft CIDR ranges. Even adding broad CIDR ranges (`4.152.0.0/14`, `13.64.0.0/11`, `20.0.0.0/9`, etc.) did not reliably cover all runner IPs.

### Fix

Added NSG rule `SSH-GitHubActions` (priority 110) with `source_address_prefix = "*"` — SSH open to all IPs. This is safe because the VM uses SSH key authentication only (no password login). Updated Terraform `vm.tf` accordingly.

---

## Issue 6: Git Safe Directory Error on VM

### Symptom

CI/CD pipeline SSH'd into the VM and ran `git pull`, which failed with:

```
fatal: detected dubious ownership in repository at '/opt/iotdash'
```

### Root Cause

Cloud-init cloned the repo as `root`, but the CI/CD pipeline ran as `azureuser`. Git refused to operate on a repo owned by a different user.

### Fix

1. Ran `git config --global --add safe.directory /opt/iotdash` as azureuser on the VM.
2. Updated `cloud-init.yaml` to run the same command during first boot.
3. Updated CI/CD workflow to use `sudo` for all docker commands (azureuser isn't in docker group until re-login after cloud-init).

---

## Issue 7: Git Permission Denied — /opt/iotdash Owned by Root

### Symptom

After fixing safe.directory, `git pull` failed with:

```
error: cannot open '.git/FETCH_HEAD': Permission denied
```

### Root Cause

All files in `/opt/iotdash` were owned by `root:root` because cloud-init runs as root.

### Fix

```bash
sudo chown -R azureuser:azureuser /opt/iotdash
```

Updated cloud-init to set correct ownership after cloning.

---

## Issue 8: Frontend API Calls to localhost:8000 in Production

### Symptom

After deploying to Azure, the frontend loaded but couldn't log in. Browser console showed API calls going to `http://localhost:8000` which doesn't exist on the user's machine.

### Root Cause

`VITE_API_URL` was set to `http://localhost:8000` and baked into the JS bundle at build time. In dev this works (backend is on localhost), but in production the backend is on the VM's IP.

### Fix

Three changes:
1. Changed `frontend/src/lib/api.ts` to default `VITE_API_URL` to empty string `''` (relative URLs).
2. Added nginx `/api/` reverse proxy in `frontend/Dockerfile.prod` to forward API calls to the backend container.
3. Removed `VITE_API_URL` build arg from `Dockerfile.prod` and CI/CD workflow.

Now the frontend makes requests to `/api/...` (same origin), and nginx proxies them to `backend:8000` inside the Docker network.

---

## Final Verification

After all fixes, verified all endpoints returned HTTP 200:

```bash
curl -s -o /dev/null -w "%{http_code}" http://iotdash-soak.eastus.cloudapp.azure.com        # 200 — Frontend (port 80)
curl -s -o /dev/null -w "%{http_code}" http://iotdash-soak.eastus.cloudapp.azure.com:5173   # 200 — Frontend (direct)
curl -s -o /dev/null -w "%{http_code}" http://iotdash-soak.eastus.cloudapp.azure.com:8000   # 200 — Backend API
curl -s -o /dev/null -w "%{http_code}" http://iotdash-soak.eastus.cloudapp.azure.com:3000   # 200 — Grafana
curl -s -o /dev/null -w "%{http_code}" http://iotdash-soak.eastus.cloudapp.azure.com:18083  # 200 — EMQX Dashboard
```

All 7 containers running:

```
NAMES      STATUS                        PORTS
frontend   Up                            0.0.0.0:5173->5173/tcp
backend    Up                            0.0.0.0:8000->8000/tcp
telegraf   Up                            8092/udp, 8125/udp, 8094/tcp
grafana    Up                            0.0.0.0:3000->3000/tcp
postgres   Up (healthy)                  0.0.0.0:5432->5432/tcp
influxdb   Up (healthy)                  0.0.0.0:8086->8086/tcp
emqx       Up (healthy)                  0.0.0.0:1883->1883/tcp, 0.0.0.0:18083->18083/tcp
```

---

## Summary of Changes Made During Troubleshooting

| File | Change |
|------|--------|
| `frontend/Dockerfile.prod` | nginx listens on 5173 instead of 80; added `/api/` reverse proxy to backend; removed `VITE_API_URL` build arg |
| `frontend/src/lib/api.ts` | Default `VITE_API_URL` changed from `http://localhost:8000` to `''` (relative URLs) |
| `docker-compose.soak.yml` | Removed `ports: "5173:80"` from frontend override; added `ports: ["80:5173"]` for clean URL access |
| `.github/workflows/soak-deploy.yml` | Added `push` trigger on main; removed `script_stop`; added `sudo` for docker commands; removed `VITE_API_URL` build-arg |
| `infra/soak-test/vm.tf` | Added SSH-GitHubActions NSG rule (source `*`); added HTTP port 80 NSG rule; added DNS label |
| `infra/soak-test/cloud-init.yaml` | Added `git config --global --add safe.directory /opt/iotdash` for azureuser |
| `.gitignore` | Removed `docs` entry (was preventing all docs from being tracked) |
