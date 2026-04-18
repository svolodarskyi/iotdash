# IoTDash — Architecture Document

> **Version:** 0.1.0-draft
> **Date:** 2026-04-12

---

## 1. System Context Diagram

```
                  ┌─────────────┐
                  │  IoT Device  │ (N devices per org)
                  └──────┬──────┘
                         │ MQTT (TLS in prod)
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    IoTDash Platform (Azure)                       │
│                                                                  │
│  ┌────────┐    ┌──────────┐    ┌──────────┐    ┌─────────────┐  │
│  │  EMQX  │───▶│ Telegraf  │───▶│ InfluxDB │◀───│   Grafana   │  │
│  │ (MQTT) │    │ (Bridge)  │    │  (TSDB)  │    │ (Dashboards)│  │
│  └────────┘    └──────────┘    └──────────┘    └──────┬──────┘  │
│                                                       │ embed   │
│                                                       ▼         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                     Web Application                        │  │
│  │  ┌─────────────────┐         ┌────────────────────────┐   │  │
│  │  │    Frontend      │◀─API──▶│       Backend           │   │  │
│  │  │    (React)       │        │      (FastAPI)          │   │  │
│  │  └─────────────────┘         └───────────┬────────────┘   │  │
│  └──────────────────────────────────────────┼────────────────┘  │
│                                             │                    │
│                                    ┌────────▼────────┐           │
│                                    │   PostgreSQL     │           │
│                                    └─────────────────┘           │
│                                                                  │
│  ┌─────────────┐  ┌────────────────┐  ┌──────────────────────┐  │
│  │  Key Vault  │  │  Log Analytics │  │  Email Service       │  │
│  └─────────────┘  └────────────────┘  └──────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
         ▲                                        │
         │ HTTPS                                  │ Email
    ┌────┴────┐                             ┌─────▼─────┐
    │  Client  │ (Browser)                  │   Client   │ (Inbox)
    └─────────┘                             └───────────┘
```

---

## 2. MQTT Topic Architecture

### 2.1 Topic Scheme

```
{device_id}/{direction}/{message_type}
```

| Segment | Description | Examples |
|---------|-------------|----------|
| `{device_id}` | Unique device identifier | `sensor01`, `temp-hub-003` |
| `{direction}` | Direction of communication | `from` (device → platform), `to` (platform → device) |
| `{message_type}` | Type of payload | `message`, `error`, `status`, `command`, `config` |

### 2.2 Topic Examples

```
# Device → Platform (from)
sensor01/from/message          # Normal telemetry data
sensor01/from/error            # Device error reports
sensor01/from/status           # Heartbeat / status updates

# Platform → Device (to)
sensor01/to/command             # Commands sent to device (reboot, recalibrate)
sensor01/to/config              # Configuration updates pushed to device

# Wildcard subscriptions
sensor01/from/#                 # All messages FROM sensor01
sensor01/#                      # All traffic for sensor01
+/from/message                  # All telemetry from all devices
+/from/error                    # All errors from all devices
+/from/#                        # All device-to-platform traffic
```

### 2.3 Telegraf Subscription Configuration

```toml
# ── Input: subscribe to all device messages ──────────
[[inputs.mqtt_consumer]]
  servers = ["tcp://emqx:1883"]
  topics  = [
    "+/from/message",    # Telemetry data (temperature, humidity, etc.)
    "+/from/error",      # Device errors
    "+/from/status",     # Device status/heartbeat
  ]
  qos = 0
  data_format = "json"
  topic_tag = "topic"

  # Extract tags from topic: {device_id}/{direction}/{message_type}
  [[inputs.mqtt_consumer.topic_parsing]]
    topic = "+/+/+"
    tags  = "device_id/direction/message_type"
```

### 2.4 Payload Schemas

**Telemetry Message** (`{device_id}/from/message`):
```json
{
  "temperature": 22.5,
  "humidity": 65.2,
  "timestamp": "2026-04-12T10:30:00Z"
}
```

**Error Report** (`{device_id}/from/error`):
```json
{
  "error_code": "SENSOR_TIMEOUT",
  "message": "Temperature sensor not responding",
  "severity": "warning",
  "timestamp": "2026-04-12T10:30:00Z"
}
```

**Status/Heartbeat** (`{device_id}/from/status`):
```json
{
  "online": true,
  "uptime_seconds": 86400,
  "firmware_version": "1.2.3",
  "battery_pct": 85,
  "timestamp": "2026-04-12T10:30:00Z"
}
```

**Command** (`{device_id}/to/command`):
```json
{
  "action": "reboot",
  "params": {},
  "request_id": "cmd-abc123"
}
```

### 2.5 InfluxDB Data Organization

With tag-based multi-tenancy and the new topic scheme:

```
Bucket: iot

Measurement: mqtt_consumer (default from Telegraf)
  Tags:
    - device_id      (from topic: sensor01)
    - direction       (from topic: from/to)
    - message_type    (from topic: message/error/status)
    - topic           (full topic string)
  Fields:
    - temperature     (float, from telemetry)
    - humidity        (float, from telemetry)
    - error_code      (string, from error)
    - online          (bool, from status)
    - ... (dynamic from JSON payload)
```

**Flux query example — temperature for a specific device:**
```flux
from(bucket: "iot")
  |> range(start: -1h)
  |> filter(fn: (r) => r.device_id == "sensor01")
  |> filter(fn: (r) => r.message_type == "message")
  |> filter(fn: (r) => r._field == "temperature")
```

**Flux query example — all errors across devices:**
```flux
from(bucket: "iot")
  |> range(start: -24h)
  |> filter(fn: (r) => r.message_type == "error")
```

---

## 3. Component Communication Matrix

| From | To | Protocol | Port | Auth | Network |
|------|----|----------|------|------|---------|
| IoT Device | EMQX | MQTT(S) | 1883 (8883 TLS) | Device credentials (Phase 2) | Public |
| Client Browser | Web App | HTTPS | 443 | JWT cookie | Public |
| Client Browser | Grafana | HTTPS | 443 | Anonymous (org-scoped) | Public |
| Web App Backend | PostgreSQL | TCP | 5432 | Password | Internal |
| Web App Backend | Grafana API | HTTP | 3000 | Service account token | Internal |
| Web App Backend | InfluxDB API | HTTP | 8086 | Token | Internal |
| Telegraf | EMQX | MQTT | 1883 | — | Internal |
| Telegraf | InfluxDB | HTTP | 8086 | Token | Internal |
| Grafana | InfluxDB | HTTP | 8086 | Token | Internal |
| Grafana | Email Service | SMTP/API | — | API key | Outbound |

---

## 4. Multi-Tenancy Model

### 4.1 Isolation Boundaries

```
┌─────────────────────────────────────────────┐
│              Platform Admin                  │
│  - Full access to all Grafana orgs          │
│  - Full access to PostgreSQL                │
│  - Manages EMQX, InfluxDB, Telegraf        │
└──────────────────┬──────────────────────────┘
                   │ creates & manages
        ┌──────────┼──────────┐
        ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│  Org A   │ │  Org B   │ │  Org C   │
│          │ │          │ │          │
│ Grafana  │ │ Grafana  │ │ Grafana  │
│ Org #2   │ │ Org #3   │ │ Org #4   │
│          │ │          │ │          │
│ Devices: │ │ Devices: │ │ Devices: │
│ - dev01  │ │ - dev05  │ │ - dev09  │
│ - dev02  │ │ - dev06  │ │ - dev10  │
│          │ │          │ │          │
│ Users:   │ │ Users:   │ │ Users:   │
│ - alice  │ │ - bob    │ │ - carol  │
│ - dave   │ │          │ │ - eve    │
└──────────┘ └──────────┘ └──────────┘
```

### 4.2 Isolation per Layer

| Layer | Isolation Mechanism |
|-------|-------------------|
| **MQTT** | Topic prefix `{device_id}/` — devices only see their own topics. ACL enforcement in EMQX (Phase 2). |
| **InfluxDB** | Tag-based: queries filter by `device_id`. Devices are mapped to orgs in PostgreSQL. |
| **Grafana** | Separate Grafana org per client. Dashboard variables filter by `device_id`. |
| **Web App** | JWT contains `organisation_id`. All API queries scoped to user's org. |
| **PostgreSQL** | `organisation_id` FK on all tenant-scoped tables. Backend enforces filtering. |

---

## 5. Grafana Embedding Architecture

### 5.1 Embed URL Construction

Backend constructs URLs for the frontend:

```
https://grafana.iotdash.example.com/d-solo/{dashboard_uid}/{dashboard_slug}
  ?orgId={grafana_org_id}
  &panelId={panel_id}
  &var-device_id={device_code}
  &from=now-1h
  &to=now
  &refresh=10s
  &theme=light
  &kiosk
```

### 5.2 Frontend Embed Component

```
┌─────────────────────────────────────┐
│  Dashboard Page                      │
│                                     │
│  ┌───────────────┐ ┌─────────────┐ │
│  │ Device Picker  │ │ Time Range  │ │
│  └───────────────┘ └─────────────┘ │
│                                     │
│  ┌─────────────────────────────────┐│
│  │ iframe: Temperature (Live)      ││
│  │ src=grafana.../d-solo/...       ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌──────────────┐ ┌──────────────┐ │
│  │ iframe:       │ │ iframe:      │ │
│  │ Current Temp  │ │ Latest Read  │ │
│  └──────────────┘ └──────────────┘ │
│                                     │
│  ┌─────────────────────────────────┐│
│  │ Alert Status Bar                ││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
```

---

## 6. Alert System Architecture

### 6.1 Alert Lifecycle

```
User creates alert in Web App
        │
        ▼
   ┌─────────┐
   │ Web App  │  POST /api/alerts
   │ Backend  │
   └────┬─────┘
        │
        ├──▶ Save to PostgreSQL (alerts table)
        │
        ├──▶ Grafana API: Create/Update Alert Rule
        │    POST /api/v1/provisioning/alert-rules
        │    {
        │      orgId: N,
        │      folderUID: "alerts",
        │      ruleGroup: "device-alerts",
        │      condition: "B",
        │      data: [
        │        { refId: "A", query: <flux query for device+metric> },
        │        { refId: "B", condition: threshold_expression }
        │      ]
        │    }
        │
        └──▶ Grafana API: Ensure Contact Point + Notification Policy
             POST /api/v1/provisioning/contact-points
             {
               name: "alert-{alert_id}",
               type: "email",
               settings: { addresses: "user@example.com" }
             }
```

### 6.2 Alert State Machine

```
PENDING  ──(Grafana synced)──▶  ACTIVE
   │                              │
   │                      (threshold breached)
   │                              │
   │                              ▼
   │                          FIRING  ──(email sent)──▶  NOTIFIED
   │                              │
   │                      (condition resolved)
   │                              │
   │                              ▼
   │                          RESOLVED
   │
   └──(user disables)──▶  DISABLED
   └──(user deletes)───▶  DELETED (Grafana rule also deleted)
```

---

## 7. Deployment Architecture (Azure)

### 7.1 Container Apps Environment

```
Azure Container Apps Environment: cae-iotdash-{env}
│
│  Shared: VNet, Log Analytics, Azure Files
│
├── ca-webapp (External Ingress)
│   ├── Image: criotdash.azurecr.io/webapp:latest
│   ├── Port: 8000
│   ├── Env: DATABASE_URL, JWT_SECRET, GRAFANA_URL, GRAFANA_TOKEN, ...
│   ├── Scale: 1-3 (HTTP concurrent requests)
│   └── Health: /api/health
│
├── ca-grafana (External Ingress)
│   ├── Image: criotdash.azurecr.io/grafana:latest
│   ├── Port: 3000
│   ├── Env: GF_* settings from Key Vault
│   ├── Scale: 1 (fixed)
│   ├── Volume: grafana-data (Azure Files)
│   └── Health: /api/health
│
├── ca-emqx (External Ingress — TCP)
│   ├── Image: emqx/emqx:5.8
│   ├── Port: 1883 (MQTT), 18083 (dashboard — admin only)
│   ├── Scale: 1 (fixed)
│   └── Volume: emqx-data (Azure Files)
│
├── ca-telegraf (No Ingress)
│   ├── Image: telegraf:1.33
│   ├── Config: telegraf.conf mounted
│   ├── Scale: 1 (fixed)
│   └── Depends: EMQX, InfluxDB
│
└── ca-influxdb (Internal Ingress)
    ├── Image: influxdb:2.7
    ├── Port: 8086
    ├── Scale: 1 (fixed)
    └── Volume: influxdb-data (Azure Files)

External:
├── Azure Database for PostgreSQL Flexible Server
│   └── iotdash database
├── Azure Key Vault (all secrets)
├── Azure Container Registry (Docker images)
└── Azure Communication Services (email)
```

### 7.2 Network Topology

```
Internet
    │
    ├──(HTTPS)──▶ ca-webapp ──(internal)──▶ PostgreSQL
    │                │                        InfluxDB
    │                │                        Grafana API
    │
    ├──(HTTPS)──▶ ca-grafana ──(internal)──▶ InfluxDB
    │
    ├──(MQTT/TCP)──▶ ca-emqx
    │
    │              ca-telegraf ──(internal)──▶ InfluxDB
    │                  │
    │                  └──(internal)──▶ EMQX
    │
    └──(internal)──▶ ca-influxdb
```

---

## 8. Local Development Setup

### 8.1 docker-compose.yml (Target)

```
services:
  emqx:        # MQTT Broker
  telegraf:     # MQTT → InfluxDB bridge
  influxdb:     # Time-series DB
  grafana:      # Dashboards
  postgres:     # Application DB (NEW)
  backend:      # FastAPI app (NEW)
  frontend:     # React dev server (NEW)
```

### 8.2 Developer Workflow

```
1. git clone → cd iotdash
2. cp .env.example .env  (fill in local dev secrets)
3. docker compose up -d
4. cd backend && alembic upgrade head  (run migrations)
5. cd backend && uvicorn app.main:app --reload  (or via docker)
6. cd frontend && npm run dev
7. python fake_device.py  (generate test data)
8. Open http://localhost:5173  (frontend)
```

---

*This document is a companion to [`PLANNING.md`](./PLANNING.md). See also [`API-SPEC.md`](./API-SPEC.md) for the full API specification.*
