# Cheapest Soak Test Setup: 200 Devices, Several Weeks

## Goal

Simulate 200 IoT devices publishing telemetry for 2-4 weeks continuously. Observe memory leaks, disk growth, connection stability, and failure modes. Spend as little money as possible.

---

## Reality Check: 200 Devices Is Tiny

| Metric | Value (assuming 30s publish interval) |
|--------|---------------------------------------|
| Concurrent MQTT connections | 200 |
| Messages/second | ~7 msg/s |
| Messages/day | ~576,000 |
| Estimated data/day (InfluxDB) | ~50-100 MB |
| Estimated data/4 weeks | ~2-3 GB |
| CPU needed (all services) | <1 vCPU sustained |
| RAM needed (all services) | ~3-4 GB |

EMQX handles 200 connections without breaking a sweat. This entire stack fits on a single small VM.

---

## Option 1: Single Azure VM — Everything on One Box (~€17-32/mo)

**The cheapest cloud option.** One VM runs the full docker-compose stack. The device simulator runs on the same VM or from your laptop.

### Setup

```bash
# B2s: 2 vCPU, 4 GB RAM — tight but workable
# B2ms: 2 vCPU, 8 GB RAM — comfortable
az vm create \
  -g rg-iotdash-test \
  -n vm-soak-test \
  --image Ubuntu2404 \
  --size Standard_B2s \
  --admin-username azureuser \
  --generate-ssh-keys \
  --os-disk-size-gb 32 \
  --public-ip-sku Basic

# Open only what's needed
az vm open-port -g rg-iotdash-test -n vm-soak-test --port 22 --priority 100
az vm open-port -g rg-iotdash-test -n vm-soak-test --port 1883 --priority 110
az vm open-port -g rg-iotdash-test -n vm-soak-test --port 8080 --priority 120  # frontend
```

```bash
# SSH in, install Docker, clone repo, start everything
ssh azureuser@<public-ip>

sudo apt update && sudo apt install -y docker.io docker-compose-plugin git
sudo usermod -aG docker azureuser
# re-login

git clone <repo-url> iotdash && cd iotdash
docker compose up -d

# Run simulator (200 devices, on the same VM)
python fake_device.py --devices 200 --interval 30
```

### Cost Breakdown

| Resource | SKU | EUR/mo |
|----------|-----|--------|
| VM | B2s (2 vCPU, 4 GB) | ~€32 |
| OS Disk | Standard SSD 32 GB (E4) | ~€2 |
| Public IP | Basic (dynamic) | ~€3 |
| **Total** | | **~€37** |

Or with a spot instance (can be evicted but 60-90% cheaper):

| Resource | SKU | EUR/mo |
|----------|-----|--------|
| VM (Spot) | B2s spot | ~€6-10 |
| OS Disk | Standard SSD 32 GB | ~€2 |
| Public IP | Basic | ~€3 |
| **Total** | | **~€11-15** |

> **Spot risk:** Azure can reclaim the VM with 30s notice. For a soak test this is usually fine — if evicted, re-create and restart. Data on the disk persists if you use a separate data disk.

### Making B2s (4 GB RAM) Work

4 GB is tight for all services. Tune memory limits:

```yaml
# docker-compose.override.yml for soak test
services:
  emqx:
    deploy:
      resources:
        limits:
          memory: 512M

  influxdb:
    deploy:
      resources:
        limits:
          memory: 1G

  grafana:
    deploy:
      resources:
        limits:
          memory: 256M

  postgres:
    deploy:
      resources:
        limits:
          memory: 256M
    command: postgres -c shared_buffers=64MB -c work_mem=4MB

  telegraf:
    deploy:
      resources:
        limits:
          memory: 128M

  backend:
    deploy:
      resources:
        limits:
          memory: 256M

  frontend:
    deploy:
      resources:
        limits:
          memory: 128M

  # drop mailhog — not needed for soak test
  mailhog:
    profiles: ["disabled"]
```

Total allocated: ~2.5 GB, leaving ~1.5 GB for OS + simulator.

If it's too tight, go **B2ms (8 GB, ~€55/mo)** or **B2als_v2 (4 GB, ~€27/mo)**.

---

## Option 2: Your Own Machine — Free

**Cheapest possible: €0.** If you have a machine (laptop, desktop, old PC, Raspberry Pi 4) that can stay on for several weeks.

```bash
# Just run docker compose locally
docker compose up -d

# Simulator in a separate terminal
python fake_device.py --devices 200 --interval 30
```

**Requirements:**
- 4+ GB RAM free for Docker
- ~5 GB disk over 4 weeks
- Stable power + network

**Downside:** Your machine is tied up, power costs, no public IP for external access.

---

## Option 3: Azure Container Instance — Single Container Group (~€25/mo)

ACI lets you run a container group (= mini pod) without a VM. No cluster overhead. Pay per second.

```bash
# Upload docker-compose to ACI (limited compose support)
# Better: build a single all-in-one image with supervisord

az container create \
  -g rg-iotdash-test \
  -n aci-soak-test \
  --image criotdash.azurecr.io/iotdash-allinone:latest \
  --cpu 2 --memory 4 \
  --ports 1883 8080 \
  --ip-address Public \
  --restart-policy Always
```

| Resource | Cost |
|----------|------|
| ACI (2 vCPU, 4 GB, 24/7 for 30 days) | ~€25 |

**Catch:** ACI has limited docker-compose support. You'd need to either build a single all-in-one image or use multiple container groups (which gets more expensive).

Not worth the hassle vs a simple VM.

---

## Option 4: GitHub Codespaces — Free Tier Abuse (Not Recommended)

Free tier gives 120 core-hours/month. A 2-core machine = 60 hours. Not enough for weeks of testing. Don't bother.

---

## Recommendation

| Option | Cost/mo | Effort | Reliability |
|--------|---------|--------|-------------|
| **Your machine** | €0 | 5 min | Medium (power/network) |
| **Azure VM B2s spot** | ~€12 | 15 min | Low (eviction risk) |
| **Azure VM B2s** | ~€37 | 15 min | High |
| **Azure VM B2ms** | ~€58 | 15 min | High, more headroom |
| **ACI** | ~€25 | 1 hour | Medium (compose limits) |

**Best balance: Azure VM B2s at ~€37/mo.** Straightforward, reliable, easy to SSH into and inspect. If you're comfortable with potential eviction (just restart), spot brings it down to ~€12.

---

## Device Simulator Script

Extend `fake_device.py` to handle 200 concurrent devices efficiently using asyncio:

```python
# fake_device_soak.py
import asyncio
import json
import random
import time
from datetime import datetime

import aiomqtt  # pip install aiomqtt

BROKER = "localhost"  # or VM public IP
PORT = 1883
DEVICE_COUNT = 200
PUBLISH_INTERVAL = 30  # seconds


async def simulate_device(device_id: str):
    """Single device: connect once, publish forever."""
    async with aiomqtt.Client(BROKER, PORT, identifier=device_id) as client:
        print(f"[{device_id}] connected")
        while True:
            payload = json.dumps({
                "temperature": round(random.uniform(18.0, 35.0), 1),
                "humidity": round(random.uniform(30.0, 80.0), 1),
                "battery": round(random.uniform(2.8, 4.2), 2),
                "ts": datetime.utcnow().isoformat(),
            })
            await client.publish(f"{device_id}/from/message", payload)

            # Occasional status message
            if random.random() < 0.05:
                status = json.dumps({"status": "online", "uptime": random.randint(0, 86400)})
                await client.publish(f"{device_id}/from/status", status)

            # Occasional error
            if random.random() < 0.01:
                error = json.dumps({"error": "sensor_timeout", "sensor": "dht22"})
                await client.publish(f"{device_id}/from/error", error)

            await asyncio.sleep(PUBLISH_INTERVAL + random.uniform(-5, 5))


async def main():
    devices = [f"device_{i:04d}" for i in range(DEVICE_COUNT)]

    # Stagger connections over 60 seconds to avoid thundering herd
    tasks = []
    for i, device_id in enumerate(devices):
        task = asyncio.create_task(simulate_device(device_id))
        tasks.append(task)
        if i % 10 == 0:
            await asyncio.sleep(1)  # 10 devices per second

    print(f"All {DEVICE_COUNT} devices launched")
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
```

```bash
pip install aiomqtt
python fake_device_soak.py
```

Run this on the same VM, or from your laptop pointed at the VM's public IP.

---

## What to Monitor During the Soak Test

### Automated (cron every 5 min, append to CSV)

```bash
# /opt/iotdash/monitor.sh
#!/bin/bash
TS=$(date -u +%Y-%m-%dT%H:%M:%S)
CSV=/opt/iotdash/soak-metrics.csv

# System
CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}')
MEM_USED=$(free -m | awk '/Mem:/{print $3}')
MEM_TOTAL=$(free -m | awk '/Mem:/{print $2}')
DISK_USED=$(df -m /var/lib/docker | awk 'NR==2{print $3}')
DISK_TOTAL=$(df -m /var/lib/docker | awk 'NR==2{print $2}')

# Docker per-container memory (MB)
EMQX_MEM=$(docker stats emqx --no-stream --format '{{.MemUsage}}' | cut -d'/' -f1)
INFLUX_MEM=$(docker stats influxdb --no-stream --format '{{.MemUsage}}' | cut -d'/' -f1)

# EMQX connections
EMQX_CONNS=$(curl -s -u admin:public http://localhost:18083/api/v5/stats | \
  python3 -c "import sys,json; print(json.load(sys.stdin).get('connections.count',0))" 2>/dev/null || echo "N/A")

# InfluxDB disk
INFLUX_DISK=$(docker exec influxdb du -sm /var/lib/influxdb2/engine 2>/dev/null | cut -f1 || echo "N/A")

echo "$TS,$CPU,$MEM_USED,$MEM_TOTAL,$DISK_USED,$DISK_TOTAL,$EMQX_MEM,$INFLUX_MEM,$EMQX_CONNS,$INFLUX_DISK" >> $CSV
```

```bash
# crontab
*/5 * * * * /opt/iotdash/monitor.sh
```

### What to Watch For

| Symptom | Likely Cause | Action |
|---------|-------------|--------|
| EMQX memory growing steadily | Session/queue leak | Check `emqx ctl clients list`, tune session expiry |
| InfluxDB disk growing faster than expected | No retention policy | Set `influx bucket update --retention 30d` |
| OOM kills (check `dmesg`) | Container memory limits too tight | Increase limits or VM size |
| EMQX connection count < 200 | Devices disconnecting | Check EMQX logs for `kicked` or `timeout` |
| CPU pegged at 100% | Telegraf or InfluxDB write pressure | Increase publish interval or batch size |
| Disk full | Logs or InfluxDB data | Set up log rotation, add retention policy |

### Set a Retention Policy (Important)

Without this, InfluxDB keeps data forever and disk will fill up:

```bash
docker exec influxdb influx bucket update \
  --name iot \
  --retention 30d \
  --org iotorg \
  --token mytoken123
```

---

## Quick Start (Copy-Paste)

```bash
# 1. Create VM (~2 min)
az group create -n rg-soak -l westeurope
az vm create -g rg-soak -n vm-soak --image Ubuntu2404 \
  --size Standard_B2s --admin-username azureuser \
  --generate-ssh-keys --os-disk-size-gb 32
az vm open-port -g rg-soak -n vm-soak --port 1883 --priority 110
az vm open-port -g rg-soak -n vm-soak --port 8080 --priority 120

# 2. SSH in
ssh azureuser@$(az vm show -g rg-soak -n vm-soak -d --query publicIps -o tsv)

# 3. Install & run (~3 min)
sudo apt update && sudo apt install -y docker.io docker-compose-plugin git python3-pip
sudo usermod -aG docker $USER && newgrp docker
git clone <repo> iotdash && cd iotdash
docker compose up -d

# 4. Wait for services to be healthy (~1 min)
docker compose ps

# 5. Set retention policy
docker exec influxdb influx bucket update --name iot --retention 30d --org iotorg --token mytoken123

# 6. Install simulator deps & run
pip install aiomqtt
nohup python3 fake_device_soak.py > /tmp/simulator.log 2>&1 &

# 7. Set up monitoring cron
chmod +x /opt/iotdash/monitor.sh
echo "*/5 * * * * /opt/iotdash/monitor.sh" | crontab -

# 8. Done. Check back in a few days.
# Download metrics:  scp azureuser@<ip>:/opt/iotdash/soak-metrics.csv .
# Teardown when done: az group delete -n rg-soak --yes
```

**Total time to set up: ~10 minutes. Total cost for 4 weeks: ~€37.**

---

## Production Soak Test: 1000 Devices @ 5s Intervals (~200 msg/s)

The above options were exploratory. The production soak test uses **1000 devices at 5-second publish intervals** on a **D2s_v5 VM (2 vCPU, 8 GB RAM, no CPU credit throttling)**. This section documents the full IaC + CI/CD + monitoring setup.

### Cost

| Resource | SKU | EUR/mo |
|----------|-----|--------|
| VM | Standard_D2s_v5 (2 vCPU, 8 GB) | ~€100 |
| OS Disk | Premium SSD 128 GB (P10) | ~€17 |
| Public IP | Basic (dynamic) | ~€3 |
| **Total** | | **~€110-130** |

~EUR 4/day. **Destroy when done!**

### Files Created

| File | Purpose |
|------|---------|
| `infra/soak-test/main.tf` | Terraform provider + resource group + VNet |
| `infra/soak-test/vm.tf` | VM, NIC, NSG, public IP |
| `infra/soak-test/variables.tf` | Configurable inputs |
| `infra/soak-test/outputs.tf` | VM IP, SSH command, service URLs |
| `infra/soak-test/cloud-init.yaml` | Automated VM setup (Docker, repo clone, stack start) |
| `infra/soak-test/terraform.tfvars.example` | Example variable values |
| `infra/soak-test/teardown.sh` | Destroy all resources |
| `docker-compose.soak.yml` | Memory limits + tuning for 8 GB VM |
| `backend/Dockerfile.prod` | Multi-stage build, gunicorn + uvicorn workers |
| `frontend/Dockerfile.prod` | Multi-stage build, nginx serving static files |
| `telegraf.soak.conf` | Telegraf tuned for ~200 msg/s throughput |
| `tools/soak_simulator.py` | Async 1000-device MQTT simulator |
| `tools/soak_monitor.sh` | Metrics collection (cron every 5 min) |
| `tools/soak_alerter.sh` | Threshold alerting (cron every 15 min) |
| `.github/workflows/soak-deploy.yml` | CI/CD: build images, push to ACR, deploy to VM (auto on push to main) |
| `.github/workflows/soak-collect.yml` | Collect metrics CSV as GitHub Actions artifact |

### Quick Start with Terraform

```bash
cd infra/soak-test
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your SSH key and IP

terraform init
terraform plan    # ~6 resources
terraform apply   # Creates VM, installs everything via cloud-init

# Wait ~5 min for cloud-init to finish, then:
ssh azureuser@$(terraform output -raw vm_public_ip)
```

### Quick Start with GitHub Actions

1. Set repository secrets: `SOAK_VM_HOST`, `SOAK_VM_SSH_KEY`, `ACR_LOGIN_SERVER`, `ACR_USERNAME`, `ACR_PASSWORD`
2. Run the `Soak Test — Build & Deploy` workflow manually, or push to main (auto-triggers for relevant paths)
3. Images build, push to ACR (`criotdashsoak.azurecr.io`), deploy to VM automatically

**DNS hostname:** `iotdash-soak.eastus.cloudapp.azure.com` (free Azure DNS label, no custom domain needed)

### Monitoring

Metrics are collected every 5 minutes to `/opt/iotdash/soak-metrics.csv` with columns:
timestamp, CPU%, RAM, disk, per-container memory, EMQX connections, message rate,
InfluxDB disk, restart counts.

Alerts fire every 15 minutes for: container restarts, disk > 80%, RAM > 90%,
EMQX connections dropped, InfluxDB unhealthy. Configure `ALERT_WEBHOOK_URL` for
Slack or ntfy.sh notifications.

### Performance Test Phases

1. **Baseline (Day 1):** Establish normal operating parameters — expect 30-50% CPU, 5-6 GB RAM, ~200 msg/s
2. **Stability Soak (Days 2-14):** Watch for memory growth, compaction storms, connection exhaustion, log disk growth
3. **Stress Tests (Day 14+):** Connection storms, service restarts, memory pressure, network partitions
4. **Capacity Ceiling (Day 14+):** Gradually increase from 1000 → 1500 → 2000+ devices until breaking point
