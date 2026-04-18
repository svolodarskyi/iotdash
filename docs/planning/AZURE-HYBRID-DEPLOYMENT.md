# Azure Hybrid Deployment: VM + Container Apps

## Motivation

The default all-Container-Apps approach has friction points for **EMQX** and **InfluxDB**:

| Problem | Detail |
|---------|--------|
| **TCP ingress limitations** | Container Apps TCP ingress is still limited — no native MQTT support, TLS termination for raw TCP is awkward |
| **Persistent storage performance** | Azure Files (SMB) mounted into Container Apps has high latency for write-heavy workloads like InfluxDB |
| **EMQX clustering** | EMQX peer discovery and cluster formation needs stable IPs / DNS — difficult in Container Apps' ephemeral model |
| **Cost predictability** | A single B2s/B2ms VM with both services can be cheaper than two always-on container apps + premium Azure Files |
| **Operational simplicity** | InfluxDB and EMQX both benefit from local SSD, simple restarts, and straightforward backup scripts |

---

## Architecture Overview

```
                         ┌─────────────────────────────────┐
                         │        Azure VM (Ubuntu)        │
                         │   ┌───────────┐ ┌────────────┐ │
  IoT Devices ──MQTTS───▶│   │   EMQX    │ │  InfluxDB  │ │
       (TCP:8883)        │   │  :1883     │ │  :8086     │ │
                         │   │  :8883 TLS │ │            │ │
                         │   └─────┬──────┘ └─────▲──────┘ │
                         │         │              │        │
                         │   ┌─────▼──────────────┘─┐     │
                         │   │     Telegraf          │     │
                         │   │  (MQTT → InfluxDB)    │     │
                         │   └───────────────────────┘     │
                         └──────────┬──────────────────────┘
                                    │ VNet (private)
                         ┌──────────▼──────────────────────┐
                         │  Container Apps Environment     │
                         │                                 │
                         │  ┌──────────┐  ┌─────────────┐  │
  Clients ──HTTPS───────▶│  │ Frontend │  │ Backend API │  │
                         │  │ (Nginx)  │  │  (FastAPI)  │  │
                         │  └──────────┘  └──────┬──────┘  │
                         │                       │         │
                         │  ┌────────────────────▼──────┐  │
                         │  │        Grafana            │  │
                         │  │  (embedded dashboards)    │  │
                         │  └───────────────────────────┘  │
                         └─────────────────────────────────┘
                                    │
                         ┌──────────▼──────────────────────┐
                         │  Azure Database for PostgreSQL  │
                         │  (Flexible Server)              │
                         └─────────────────────────────────┘
```

---

## Component Placement

### VM (Ubuntu 22.04 / 24.04 LTS)

| Service | Why on VM |
|---------|-----------|
| **EMQX** | Needs raw TCP listener on :8883 for MQTTS. Stable IP for IoT devices. Clustering later is straightforward with a second VM. |
| **InfluxDB** | Write-heavy workload benefits from local managed disk (Premium SSD). No Azure Files latency penalty. |
| **Telegraf** | Runs alongside both — subscribes to local EMQX, writes to local InfluxDB. Zero network hop. |

**Suggested VM size:** `Standard_B2ms` (2 vCPU, 8 GB RAM) — sufficient for moderate IoT load. Scale to `Standard_D2s_v5` if needed.

### Container Apps

| Service | Why on Container Apps |
|---------|----------------------|
| **Frontend** | Static SPA served by Nginx. Stateless, scales to zero when idle. HTTPS ingress is native. |
| **Backend API** | Stateless FastAPI. Auto-scales 0→N based on HTTP traffic. Easy CD from ACR. |
| **Grafana** | Mostly stateless (provisioned dashboards). Needs HTTPS ingress for iframe embedding. Single replica is fine. |

### Managed Service

| Service | Why managed |
|---------|-------------|
| **PostgreSQL** | Azure Database for PostgreSQL Flexible Server — automated backups, HA, patching. No reason to self-host. |

---

## Network & Security Design

### VNet Layout

```
VNet: vnet-iotdash-prod  (10.0.0.0/16)
│
├── Subnet: snet-vm          (10.0.1.0/24)   ← VM
├── Subnet: snet-cae         (10.0.2.0/24)   ← Container Apps Environment (delegated)
├── Subnet: snet-postgres    (10.0.3.0/24)   ← PostgreSQL Flexible Server (delegated)
└── Subnet: snet-endpoints   (10.0.4.0/24)   ← Private Endpoints (if needed later)
```

### NSG Rules (Network Security Groups)

**VM NSG (`nsg-vm`):**

| Priority | Direction | Port | Source | Purpose |
|----------|-----------|------|--------|---------|
| 100 | Inbound | 8883 | Internet | MQTTS from IoT devices |
| 110 | Inbound | 8086 | snet-cae | InfluxDB from Backend/Grafana |
| 120 | Inbound | 1883 | snet-cae | MQTT from Backend (command publishing) |
| 130 | Inbound | 22 | Your IP only | SSH management (or use Bastion) |
| 200 | Inbound | * | * | **DENY all other** |
| 100 | Outbound | 443 | Internet | OS updates, EMQX license check |
| 200 | Outbound | * | VNet | Allow VNet-internal |

**Container Apps NSG (`nsg-cae`):**

| Priority | Direction | Port | Source | Purpose |
|----------|-----------|------|--------|---------|
| 100 | Inbound | 443 | Internet | HTTPS for Frontend, Backend, Grafana |
| 200 | Inbound | * | * | DENY all other |
| 100 | Outbound | 8086, 1883 | snet-vm | Reach InfluxDB & EMQX |
| 110 | Outbound | 5432 | snet-postgres | Reach PostgreSQL |

### Traffic Flows (Secured)

```
IoT Device ──MQTTS (TLS 1.2+)──▶ VM Public IP:8883 ──▶ EMQX
                                     (NSG: port 8883 only)

Client Browser ──HTTPS──▶ Container Apps (Frontend)
                              │
                              ├──HTTPS──▶ Backend API ──private──▶ PostgreSQL
                              │              │
                              │              ├──private──▶ InfluxDB (VM:8086)
                              │              └──private──▶ EMQX (VM:1883) [commands]
                              │
                              └──HTTPS──▶ Grafana ──private──▶ InfluxDB (VM:8086)
```

---

## Securing the MQTT Broker (EMQX)

### Layer 1: Transport — TLS

```
# /etc/emqx/emqx.conf (relevant snippet)
listeners.ssl.default {
  bind = "0.0.0.0:8883"
  ssl_options {
    certfile = "/etc/emqx/certs/server.pem"
    keyfile  = "/etc/emqx/certs/server-key.pem"
    cacertfile = "/etc/emqx/certs/ca.pem"
    verify = verify_peer          # optional: mutual TLS for devices
    fail_if_no_peer_cert = false  # set true for mTLS
  }
}

# Disable plain TCP listener on public interface
listeners.tcp.default {
  bind = "127.0.0.1:1883"   # localhost only — for Telegraf
}
```

**Certificate options:**
- **Let's Encrypt** via certbot (free, auto-renew) — needs a DNS name for the VM
- **Azure Key Vault certificates** — managed renewal, pull via VM extension
- **Self-signed CA** — for mTLS with IoT devices (you control both ends)

### Layer 2: Authentication

**Option A — Username/Password (simplest):**
```
# Built-in database auth
authentication = [
  {
    mechanism = password_based
    backend = built_in_database
    password_hash_algorithm { name = bcrypt }
  }
]
```
Each device gets a unique username (= `device_id`) and strong password, provisioned via EMQX REST API when a device is registered in the platform.

**Option B — JWT Auth (stateless):**
```
authentication = [
  {
    mechanism = jwt
    from = password
    algorithm = hmac-based
    secret = "${JWT_SECRET}"
    verify_claims = { "device_id" = "${username}" }
  }
]
```
Backend issues short-lived JWTs to devices. No credential storage on broker.

**Option C — mTLS Client Certificates (strongest):**
Each device gets a unique client certificate signed by your CA. EMQX extracts the CN as the client identity. Best for high-security deployments but harder to provision.

### Layer 3: Authorization (ACL)

```
authorization {
  sources = [
    {
      type = built_in_database
      enable = true
    }
  ]
  no_match = deny      # deny by default
}
```

When registering a device, Backend calls EMQX API to set ACL rules:

```json
// POST /api/v5/authorization/sources/built_in_database/rules/users
{
  "username": "sensor01",
  "rules": [
    { "action": "publish", "topic": "sensor01/from/+",  "permission": "allow" },
    { "action": "subscribe", "topic": "sensor01/to/+",  "permission": "allow" },
    { "action": "all",     "topic": "#",                "permission": "deny"  }
  ]
}
```

This ensures `sensor01` can **only** publish to `sensor01/from/*` and subscribe to `sensor01/to/*`.

### Layer 4: Rate Limiting

```
# Per-client rate limits in emqx.conf
force_shutdown {
  max_message_queue_len = 1000
  max_heap_size = "32MB"
}

listeners.ssl.default {
  max_conn_rate = "100/s"      # connection rate limit
  messages_rate = "100/s"      # per-client publish rate
  bytes_rate = "1MB/s"         # per-client bandwidth
}
```

---

## Securing InfluxDB

```bash
# InfluxDB only listens on private interface
INFLUXDB_HTTP_BIND_ADDRESS=10.0.1.x:8086   # VM private IP only
```

- **No public exposure** — only reachable from VNet (VM localhost + Container Apps subnet)
- **API token auth** — all-access token stored in Azure Key Vault, injected as env var
- Optionally enable InfluxDB TLS for in-transit encryption within VNet

---

## Securing Container Apps ↔ VM Communication

**Option A — VNet Integration (recommended):**
- Container Apps Environment is deployed into `snet-cae`
- VM is in `snet-vm`
- All communication is private IP, never leaves VNet
- NSG rules restrict which ports are open between subnets

**Option B — Private Endpoint (if using managed InfluxDB later):**
- Create private endpoints in `snet-endpoints`
- DNS resolution via Azure Private DNS Zone

**Option C — Service Connector with Managed Identity:**
- For PostgreSQL: use Azure AD / Entra ID authentication instead of password
- Eliminates password rotation concerns

---

## Secret Management

| Secret | Storage | Injection |
|--------|---------|-----------|
| InfluxDB API token | Azure Key Vault | VM: Key Vault VM extension → env file. Container Apps: secret reference |
| PostgreSQL password | Azure Key Vault | Container Apps secret → env var. Or use Managed Identity + Entra auth |
| JWT signing key | Azure Key Vault | Backend container secret |
| Grafana admin password | Azure Key Vault | Grafana container secret |
| EMQX dashboard password | Azure Key Vault | VM env file |
| EMQX device credentials | EMQX built-in DB | Provisioned via EMQX REST API from Backend |
| TLS certificates | Azure Key Vault or Let's Encrypt | VM: certbot or KV VM extension |

**No secrets in code, no secrets in docker-compose, no secrets in Terraform state.**

---

## VM Setup (Cloud-Init / Ansible)

```yaml
# cloud-init.yml (simplified)
packages:
  - docker.io
  - docker-compose-plugin
  - certbot

write_files:
  - path: /opt/iotdash/docker-compose.yml
    content: |
      services:
        emqx:
          image: emqx/emqx:5.8
          restart: always
          ports:
            - "8883:8883"           # MQTTS (public)
            - "127.0.0.1:1883:1883" # MQTT (local only)
            - "127.0.0.1:18083:18083" # Dashboard (local only)
          volumes:
            - emqx_data:/opt/emqx/data
            - /etc/emqx/certs:/etc/emqx/certs:ro
          environment:
            EMQX_DASHBOARD__DEFAULT_PASSWORD: ${EMQX_ADMIN_PW}

        influxdb:
          image: influxdb:2.7
          restart: always
          ports:
            - "10.0.1.x:8086:8086"  # private IP only
          volumes:
            - influx_data:/var/lib/influxdb2
          environment:
            DOCKER_INFLUXDB_INIT_MODE: setup
            DOCKER_INFLUXDB_INIT_ORG: iotorg
            DOCKER_INFLUXDB_INIT_BUCKET: iot
            DOCKER_INFLUXDB_INIT_ADMIN_TOKEN: ${INFLUX_TOKEN}

        telegraf:
          image: telegraf:1.33
          restart: always
          volumes:
            - ./telegraf.conf:/etc/telegraf/telegraf.conf:ro
          depends_on:
            - emqx
            - influxdb

      volumes:
        emqx_data:
        influx_data:

runcmd:
  - systemctl enable docker
  - cd /opt/iotdash && docker compose up -d
```

---

## Backup Strategy

| Data | Method | Frequency |
|------|--------|-----------|
| InfluxDB | `influx backup` to Azure Blob Storage via cron | Daily + before upgrades |
| EMQX config & built-in DB | `emqx ctl data export` to Azure Blob | Daily |
| PostgreSQL | Azure automated backups (Flexible Server) | Continuous (PITR) |
| VM disk | Azure Backup (VM snapshot) | Weekly |

```bash
# /opt/iotdash/backup.sh (cron daily 2 AM)
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d-%H%M)
BLOB_CONTAINER="backups"

# InfluxDB
docker exec influxdb influx backup /tmp/backup-$TIMESTAMP
docker cp influxdb:/tmp/backup-$TIMESTAMP /tmp/influx-backup-$TIMESTAMP
az storage blob upload-batch -s /tmp/influx-backup-$TIMESTAMP \
  -d $BLOB_CONTAINER/influxdb/$TIMESTAMP --account-name stiotdash

# EMQX
docker exec emqx emqx ctl data export
docker cp emqx:/opt/emqx/data/backup /tmp/emqx-backup-$TIMESTAMP
az storage blob upload-batch -s /tmp/emqx-backup-$TIMESTAMP \
  -d $BLOB_CONTAINER/emqx/$TIMESTAMP --account-name stiotdash

# Cleanup
rm -rf /tmp/influx-backup-$TIMESTAMP /tmp/emqx-backup-$TIMESTAMP
```

---

## Cost Estimate (EUR/month, West Europe)

| Resource | SKU | Est. Cost |
|----------|-----|-----------|
| VM (EMQX + InfluxDB + Telegraf) | B2ms (2 vCPU, 8 GB) | ~€55 |
| Managed Disk (Premium SSD 64 GB) | P6 | ~€8 |
| Container Apps — Frontend | 0.25 vCPU, 0.5 GB, scale 0-2 | ~€5-15 |
| Container Apps — Backend | 0.5 vCPU, 1 GB, scale 1-3 | ~€15-30 |
| Container Apps — Grafana | 0.5 vCPU, 1 GB, scale 1 | ~€15 |
| PostgreSQL Flexible Server | Burstable B1ms | ~€13 |
| Key Vault | Standard | ~€1 |
| **Total** | | **~€110-140** |

Compare with all-Container-Apps approach: similar compute cost but +€20-40/month for Azure Files premium shares (InfluxDB + EMQX persistent volumes).

---

## Pros & Cons

### Pros

- **Real TCP ingress** — EMQX gets a proper public IP with port 8883, no Container Apps TCP workarounds
- **Disk performance** — InfluxDB on local Premium SSD, not Azure Files SMB
- **Simpler EMQX ops** — direct SSH access for debugging, clustering, config changes
- **Telegraf co-located** — zero-latency MQTT→InfluxDB path, no cross-network hops
- **Predictable cost** — VM is flat-rate, no surprise consumption billing for data-plane services
- **Easy TLS** — certbot on VM is standard, well-documented

### Cons

- **VM patching** — you own OS updates (mitigate: enable Azure Update Manager / unattended-upgrades)
- **No auto-scale for MQTT** — single VM is a ceiling (mitigate: vertical scale or add a second VM + EMQX cluster)
- **Split deployment** — two deployment targets instead of one (mitigate: single Terraform config manages both)
- **No scale-to-zero** — VM runs 24/7 even if no devices are connected

---

## Migration Path from Dev → This Architecture

1. **Terraform** — provision VNet, subnets, NSGs, VM, Container Apps Environment, PostgreSQL
2. **VM provisioning** — cloud-init installs Docker, pulls images, starts EMQX + InfluxDB + Telegraf
3. **Container Apps** — deploy Frontend, Backend, Grafana from ACR images
4. **DNS** — `mqtt.iotdash.example.com` → VM public IP, `app.iotdash.example.com` → Container Apps
5. **TLS** — certbot on VM for MQTTS cert, Container Apps handles HTTPS natively
6. **Secrets** — populate Key Vault, wire references into Container Apps and VM env
7. **Backend config** — point `INFLUXDB_URL` to `http://10.0.1.x:8086`, `MQTT_BROKER_HOST` to `10.0.1.x`
8. **Test** — fake_device.py targeting `mqtts://mqtt.iotdash.example.com:8883`

---

## Future Considerations

- **EMQX clustering** — add a second VM, EMQX auto-clusters via `static` or `dns` discovery
- **InfluxDB → Azure Data Explorer** — if time-series volume outgrows single-node InfluxDB
- **Azure Bastion** — replace direct SSH with Bastion for zero-trust VM access
- **Azure Monitor agent** — ship VM metrics/logs to Log Analytics alongside Container Apps telemetry
- **Managed Identity everywhere** — eliminate stored credentials for Azure-to-Azure communication