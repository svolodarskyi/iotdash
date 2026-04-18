# IoTDash Platform — Master Planning Document

> **Version:** 0.1.0-draft
> **Date:** 2026-04-12
> **Status:** Planning

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current State Audit](#2-current-state-audit)
3. [Target Architecture](#3-target-architecture)
4. [Gap Analysis](#4-gap-analysis)
5. [Component Specifications](#5-component-specifications)
6. [Data Model](#6-data-model)
7. [Security Architecture](#7-security-architecture)
8. [Azure Infrastructure](#8-azure-infrastructure)
9. [CI/CD Pipeline](#9-cicd-pipeline)
10. [Implementation Phases](#10-implementation-phases)
11. [Open Questions & Decisions](#11-open-questions--decisions)

---

## 1. Executive Summary

**Product:** A multi-tenant IoT monitoring platform where:
- IoT devices publish sensor data via MQTT
- Data flows through Telegraf into InfluxDB
- Grafana renders dashboards, embedded in a custom web application
- Clients log in to the web app to view their organization's devices
- Clients configure alerts in the web app; alerts are applied to Grafana and delivered via email
- The platform admin manages organizations, devices, and Grafana configuration
- Everything runs in Azure Container Apps with CI/CD from GitHub

---

## 2. Current State Audit

### 2.1 What Exists

| Component | Version | Status | Notes |
|-----------|---------|--------|-------|
| **EMQX** (MQTT Broker) | 5.8 | Working | Anonymous access enabled, single listener on 1883 |
| **Telegraf** | 1.33 | Working | Bridges `sensors/+/temperature` to InfluxDB |
| **InfluxDB** | 2.7 | Working | Single org `iotorg`, single bucket `iot` |
| **Grafana** | 11.4.0 | Working | Single org, admin/admin credentials, temperature dashboard provisioned |
| **Fake Device Simulator** | Python | Working | Publishes temperature for `sensor01` to localhost MQTT |
| **Docker Compose** | — | Working | All 4 services on `iot_net` bridge network |

### 2.2 Current Data Flow

```
fake_device.py
    │  (MQTT: sensors/sensor01/temperature)
    ▼
  EMQX (:1883)
    │  (Telegraf subscribes to sensors/+/temperature)
    ▼
 Telegraf
    │  (InfluxDB v2 write API)
    ▼
InfluxDB (:8086)   bucket=iot, org=iotorg
    │
    ▼
 Grafana (:3000)   provisioned datasource + temperature dashboard
```

### 2.3 Current Issues & Risks

| # | Issue | Severity |
|---|-------|----------|
| 1 | **Hardcoded credentials everywhere** — InfluxDB token `mytoken123`, Grafana `admin/admin`, InfluxDB `admin/admin1234` | Critical |
| 2 | **No multi-tenancy** — Single Grafana org, single InfluxDB org/bucket | Blocker |
| 3 | **No web application** — Clients would access Grafana directly | Blocker |
| 4 | **No user management** — No database, no auth | Blocker |
| 5 | **No alert system** — No mechanism for client-defined alerts | Blocker |
| 6 | **No Azure infrastructure** — Local docker-compose only | Blocker |
| 7 | **No CI/CD** — Manual deployment | Blocker |
| 8 | **Grafana datasource UID hardcoded** in dashboard JSON (`P951FEA4DE68E13C5`) | Medium |
| 9 | **EMQX anonymous access** — No device authentication | Medium |
| 10 | **Single sensor type** — Only temperature; topic structure is `sensors/+/temperature` | Low (extensible) |
| 11 | **Stale file `=2.0`** in repo root (likely pip artifact) | Low |

---

## 3. Target Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Azure Container Apps                         │
│                                                                     │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────────────────┐  │
│  │  EMQX    │   │ Telegraf  │   │ InfluxDB │   │    Grafana     │  │
│  │ (MQTT)   │──▶│ (Bridge)  │──▶│  (TSDB)  │◀──│ (Dashboards)   │  │
│  └──────────┘   └──────────┘   └──────────┘   └───────┬────────┘  │
│       ▲                                                │ embed     │
│       │ MQTT                                           ▼           │
│  IoT Devices                                  ┌────────────────┐   │
│                                               │   Web App      │   │
│                                               │  ┌──────────┐  │   │
│                                               │  │ Frontend  │  │   │
│                                               │  │ (React)   │  │   │
│                                               │  └─────┬─────┘  │   │
│                                               │        │ API    │   │
│                                               │  ┌─────▼─────┐  │   │
│                                               │  │ Backend   │  │   │
│                                               │  │ (Python)  │  │   │
│                                               │  └─────┬─────┘  │   │
│                                               └────────┼────────┘   │
│                                                        │            │
│                                               ┌────────▼────────┐   │
│                                               │   PostgreSQL    │   │
│                                               │   (App DB)      │   │
│                                               └─────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Target Data Flow

```
IoT Device
    │  MQTT: sensors/{device_id}/{measurement_type}
    ▼
EMQX (:1883)  ── device auth via username/password or token
    │
    ▼
Telegraf  ── subscribes sensors/#, tags org_id + device_id
    │
    ▼
InfluxDB  ── bucket per org OR tag-based isolation
    │
    ▼
Grafana   ── org per client, dashboards filtered by device_id tag
    │         anonymous access enabled per org for embedding
    │
    ▼ (iframe embed)
Web App Backend  ── serves embed URLs, manages alerts via Grafana API
    │
    ▼
Web App Frontend ── user sees embedded dashboards, configures alerts
    │
    ▼
PostgreSQL ── users, orgs, devices, alert configs, embed URLs
```

### 3.3 Alert Flow

```
User configures alert in Web App
    │
    ▼
Web App Backend
    │  1. Saves alert config to PostgreSQL
    │  2. Calls Grafana Alerting API to create/update alert rule
    │     - scoped to org's datasource + device_id filter
    │     - contact point = email (from user profile)
    ▼
Grafana Alerting Engine
    │  Evaluates alert rules on schedule
    │  Fires notification when threshold breached
    ▼
Email (via SMTP / SendGrid / Azure Communication Services)
    │
    ▼
Client receives email notification
```

---

## 4. Gap Analysis

| # | Gap | Priority | Effort |
|---|-----|----------|--------|
| **G1** | Web Application (Frontend) | P0 | Large |
| **G2** | Web Application (Backend API) | P0 | Large |
| **G3** | PostgreSQL Database + Schema | P0 | Medium |
| **G4** | User Authentication (login/password) | P0 | Medium |
| **G5** | Grafana Multi-Org Setup + Anonymous Embed | P0 | Medium |
| **G6** | Alert Management (Web App → Grafana API) | P0 | Large |
| **G7** | Email Delivery for Alerts | P1 | Small |
| **G8** | Azure Container Apps Infrastructure (Terraform) | P0 | Large |
| **G9** | CI/CD Pipeline (GitHub Actions) | P1 | Medium |
| **G10** | Secrets Management (Azure Key Vault) | P0 | Small |
| **G11** | Admin Tooling / Access to Services in Azure | P1 | Small |
| **G12** | MQTT Device Authentication | P2 | Medium |
| **G13** | Multi-sensor Type Support | P2 | Small |
| **G14** | Grafana Dashboard Templates per Sensor Type | P2 | Medium |
| **G15** | Persistent Storage for InfluxDB + PostgreSQL in Azure | P0 | Medium |

---

## 5. Component Specifications

### 5.1 Web Application — Backend

| Attribute | Decision |
|-----------|----------|
| **Language** | Python (FastAPI) |
| **Why** | Already using Python for fake_device; FastAPI is async, fast, has OpenAPI docs |
| **Responsibilities** | Auth, user/org/device CRUD, alert CRUD, Grafana API proxy, embed URL management |
| **ORM** | SQLAlchemy + Alembic (migrations) |
| **Auth** | Session-based or JWT (password + bcrypt hashing) |
| **Grafana Integration** | Grafana HTTP API (admin service account token) for org management, alert rules, contact points |

**Key API Endpoints:**

```
POST   /api/auth/login
POST   /api/auth/logout
GET    /api/auth/me

GET    /api/organisations
GET    /api/organisations/{id}
GET    /api/organisations/{id}/devices
GET    /api/organisations/{id}/dashboards

GET    /api/devices/{id}
GET    /api/devices/{id}/embed-url

GET    /api/alerts
POST   /api/alerts
PUT    /api/alerts/{id}
DELETE /api/alerts/{id}

# Admin-only
POST   /api/admin/organisations
POST   /api/admin/organisations/{id}/devices
POST   /api/admin/organisations/{id}/dashboards
PUT    /api/admin/grafana/sync   # sync orgs/dashboards to Grafana
```

### 5.2 Web Application — Frontend

| Attribute | Decision |
|-----------|----------|
| **Framework** | React (Vite) |
| **Why** | Wide ecosystem, easy iframe embedding, component libraries |
| **UI Library** | Shadcn/ui or Ant Design (TBD) |
| **State (server)** | TanStack Query (data fetching, caching, mutations) |
| **State (client)** | Zustand (auth state, UI state) |
| **Routing** | TanStack Router (type-safe, file-based routing) |

**Key Pages:**

| Page | Description |
|------|-------------|
| `/login` | Email + password login |
| `/dashboard` | List of organization's devices with embedded Grafana panels |
| `/dashboard/:deviceId` | Full device view with all Grafana panels embedded |
| `/alerts` | List, create, edit, delete alert rules |
| `/alerts/new` | Alert creation form (device, metric, condition, threshold, email) |
| `/admin/*` | Admin panel for managing orgs, devices, users (admin only) |

### 5.3 PostgreSQL Database

Managed via Alembic migrations. See [Section 6](#6-data-model) for schema.

### 5.4 Grafana — Multi-Org Embedding Strategy

**Per-Client Organization Setup (Admin does this):**

1. Admin creates a Grafana organization for each client via Grafana API
2. Admin creates a datasource in that org pointing to InfluxDB (same instance, but queries filtered by device tags)
3. Admin provisions dashboard templates in that org, with `device_id` as a dashboard variable
4. Anonymous access is enabled for that org (`[auth.anonymous]` with org-specific config)
5. Embed URLs use `&orgId=X` and `&var-device_id=Y` parameters

**Grafana Configuration Required:**

```ini
[security]
allow_embedding = true
cookie_samesite = none   # if cross-origin

[auth.anonymous]
enabled = true
org_name = <default org for anonymous>
# Note: for multi-org anonymous, use org-specific auth proxy or
# use Grafana service accounts with viewer tokens per org

[users]
viewers_can_edit = false
```

**Embedding Approach:**
- Use Grafana's iframe embedding with `?orgId=X&panelId=Y&var-device_id=Z&kiosk`
- Backend generates embed URLs per user/device from database records
- Frontend renders `<iframe src="{embed_url}" />` in dashboard components

### 5.5 Alert System Design

**User-Facing Alert Config:**

| Field | Type | Description |
|-------|------|-------------|
| device_id | FK | Which device to monitor |
| metric | string | e.g., `temperature` |
| condition | enum | `above`, `below`, `equal` |
| threshold | float | Trigger value |
| duration | duration | e.g., `5m` (must be above threshold for this long) |
| notification_email | string | Where to send alert |
| enabled | bool | Toggle on/off |

**Backend → Grafana Translation:**

When a user creates/updates an alert, the backend:
1. Saves config to PostgreSQL
2. Calls Grafana Alerting API (`POST /api/v1/provisioning/alert-rules`) for the user's org
3. Creates/updates a contact point with the user's email
4. Creates a notification policy routing alerts to that contact point

### 5.6 MQTT Topic Architecture

**New topic scheme (replaces `sensors/{device_id}/temperature`):**

```
{device_id}/{direction}/{message_type}
```

| Segment | Values | Description |
|---------|--------|-------------|
| `device_id` | `sensor01`, `temp-hub-003`, ... | Unique device identifier |
| `direction` | `from`, `to` | `from` = device→platform, `to` = platform→device |
| `message_type` | `message`, `error`, `status`, `command`, `config`, ... | Extensible payload type |

**Examples:**
```
sensor01/from/message     # Telemetry data (temperature, humidity, etc.)
sensor01/from/error       # Device error reports
sensor01/from/status      # Heartbeat / online status
sensor01/to/command        # Platform sends commands to device
sensor01/to/config         # Push config updates to device
```

**Wildcard subscriptions:**
```
+/from/message            # All telemetry from all devices
+/from/error              # All errors from all devices
+/from/#                  # All device-to-platform traffic
sensor01/#                # All traffic for one device
```

See [`ARCHITECTURE.md` Section 2](./ARCHITECTURE.md#2-mqtt-topic-architecture) for full payload schemas.

### 5.7 EMQX (MQTT Broker)

Current setup needs updates for the new topic scheme:
- Update ACL rules for `{device_id}/{direction}/{message_type}` pattern
- Device authentication (username/password per device, managed in EMQX or via auth plugin) — Phase 2
- ACL enforcement: device `sensor01` can only publish to `sensor01/from/#` — Phase 2
- TLS on port 8883 — Phase 2

### 5.8 Telegraf

Update topic subscription for new scheme:

```toml
[[inputs.mqtt_consumer]]
  servers = ["tcp://emqx:1883"]
  topics  = ["+/from/message", "+/from/error", "+/from/status"]
  qos = 0
  data_format = "json"
  topic_tag = "topic"

  [[inputs.mqtt_consumer.topic_parsing]]
    topic = "+/+/+"
    tags  = "device_id/direction/message_type"
```

### 5.9 InfluxDB

**Multi-tenant isolation strategy — Tag-based (recommended for MVP):**

- Single bucket `iot` with tags: `device_id`, `org_id` (added by Telegraf or MQTT payload)
- Grafana queries filter by `device_id` tag
- Simpler to manage than bucket-per-org
- Adequate isolation for embedded dashboard model (users never write raw queries)

---

## 6. Data Model

### 6.1 Entity Relationship

```
organisations 1───* users
organisations 1───* devices
organisations 1───* grafana_dashboards
devices       1───* alerts
users         1───* alerts (created_by)
```

### 6.2 Table Definitions

```sql
-- Organisations (maps 1:1 to Grafana org)
CREATE TABLE organisations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL UNIQUE,
    grafana_org_id  INTEGER UNIQUE,          -- Grafana's internal org ID
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- Users
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,   -- bcrypt
    full_name       VARCHAR(255),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    role            VARCHAR(50) DEFAULT 'viewer',  -- 'viewer', 'admin'
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- Devices
CREATE TABLE devices (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_code     VARCHAR(255) NOT NULL UNIQUE,  -- e.g. 'sensor01', used in MQTT topic
    name            VARCHAR(255) NOT NULL,          -- human-friendly name
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    device_type     VARCHAR(100),                   -- e.g. 'temperature', 'humidity'
    metadata        JSONB DEFAULT '{}',             -- flexible extra fields
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- Grafana Dashboard Embeds
CREATE TABLE grafana_dashboards (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    title           VARCHAR(255) NOT NULL,
    grafana_uid     VARCHAR(255) NOT NULL,          -- Grafana dashboard UID
    grafana_org_id  INTEGER NOT NULL,               -- Grafana org ID for embed URL
    panel_ids       INTEGER[] DEFAULT '{}',         -- specific panels to embed, empty = full dash
    embed_base_url  TEXT NOT NULL,                   -- base iframe URL
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- Alerts
CREATE TABLE alerts (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id           UUID NOT NULL REFERENCES devices(id),
    created_by          UUID NOT NULL REFERENCES users(id),
    metric              VARCHAR(100) NOT NULL,       -- 'temperature', 'humidity', etc.
    condition           VARCHAR(20) NOT NULL,        -- 'above', 'below'
    threshold           DOUBLE PRECISION NOT NULL,
    duration_seconds    INTEGER DEFAULT 300,         -- how long condition must hold
    notification_email  VARCHAR(255) NOT NULL,
    is_enabled          BOOLEAN DEFAULT true,
    grafana_rule_uid    VARCHAR(255),                -- Grafana alert rule UID (after sync)
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);

-- Audit log (optional, good practice)
CREATE TABLE audit_log (
    id          BIGSERIAL PRIMARY KEY,
    user_id     UUID REFERENCES users(id),
    action      VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id   UUID,
    details     JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT now()
);
```

---

## 7. Security Architecture

### 7.1 Secrets Management

| Secret | Current | Target |
|--------|---------|--------|
| InfluxDB admin password | `admin1234` in docker-compose.yml | Azure Key Vault |
| InfluxDB token | `mytoken123` in docker-compose.yml + telegraf.conf | Azure Key Vault |
| Grafana admin password | `admin` in docker-compose.yml | Azure Key Vault |
| PostgreSQL password | N/A | Azure Key Vault |
| JWT/Session secret | N/A | Azure Key Vault |
| SMTP credentials | N/A | Azure Key Vault |
| Grafana service account token | N/A | Azure Key Vault |

All secrets injected via environment variables from Key Vault references in Container Apps.

### 7.2 Network Security

```
Internet ──▶ Azure Container Apps Environment
              │
              ├── Web App (public ingress, HTTPS)
              │     ├── Frontend (static, served by backend or CDN)
              │     └── Backend API
              │
              ├── EMQX (public ingress on MQTT port for IoT devices)
              │
              ├── Grafana (internal ingress only — NOT public)
              │     └── Accessible only from Web App backend + iframes via backend proxy
              │
              ├── InfluxDB (internal only)
              ├── Telegraf (internal only)
              └── PostgreSQL (internal only — or Azure Database for PostgreSQL)
```

**Key decisions:**
- Grafana: **internal only** or behind auth proxy. For iframe embedding to work from the user's browser, Grafana needs to be reachable from the client. Two options:
  - **Option A (Simpler):** Grafana has public ingress but anonymous access is scoped per org. Risk: Grafana URL is discoverable.
  - **Option B (More secure):** Backend proxies Grafana panels (render PNG/snapshot). More complex, loses interactivity.
  - **Recommended for MVP:** Option A with Grafana public but anonymous-only (no login page exposed), `allow_embedding=true`.

### 7.3 Authentication & Authorization

| Layer | Mechanism |
|-------|-----------|
| Web App Login | Email + bcrypt password → JWT token (httponly cookie) |
| API Authorization | JWT middleware; role check (viewer vs admin) |
| Grafana Admin | Service account token (stored in Key Vault), used by backend only |
| Grafana Embed | Anonymous viewer access, scoped by orgId in URL |
| EMQX Devices | Phase 2: username/password per device |
| InfluxDB | Token-based, internal only |

---

## 8. Azure Infrastructure

### 8.1 Resource Overview

```
Resource Group: rg-iotdash-{env}
│
├── Container Apps Environment: cae-iotdash-{env}
│   ├── Container App: ca-webapp          (Web App Backend + Frontend)
│   ├── Container App: ca-grafana         (Grafana)
│   ├── Container App: ca-emqx            (EMQX MQTT Broker)
│   ├── Container App: ca-telegraf        (Telegraf)
│   └── Container App: ca-influxdb        (InfluxDB)
│
├── Azure Database for PostgreSQL Flexible Server: psql-iotdash-{env}
│   └── Database: iotdash
│
├── Azure Key Vault: kv-iotdash-{env}
│   └── All secrets
│
├── Azure Container Registry: criotdash{env}
│   └── Docker images
│
├── Azure Log Analytics Workspace: law-iotdash-{env}
│
├── Azure Communication Services (or SendGrid): email-iotdash-{env}
│   └── Email delivery for alerts
│
└── Azure Storage Account: stiotdash{env}  (optional, for InfluxDB persistent data)
```

### 8.2 Container Apps Configuration

| App | Ingress | Min/Max Replicas | CPU | Memory | Persistent Storage |
|-----|---------|-----------------|-----|--------|--------------------|
| ca-webapp | External, HTTPS, port 8000 | 1/3 | 0.5 | 1Gi | — |
| ca-grafana | External, HTTPS, port 3000 | 1/1 | 0.5 | 1Gi | Azure Files (grafana_data) |
| ca-emqx | External, TCP, port 1883 | 1/1 | 0.5 | 1Gi | Azure Files (emqx_data) |
| ca-telegraf | Internal only | 1/1 | 0.25 | 0.5Gi | — |
| ca-influxdb | Internal only | 1/1 | 1.0 | 2Gi | Azure Files (influxdb_data) |

**Note:** For production, consider Azure Managed Grafana and/or Azure Database for PostgreSQL instead of containerised versions. For MVP, containers are fine.

### 8.3 Terraform Structure

```
infra/
├── main.tf                 # Provider config, backend
├── variables.tf            # Input variables
├── outputs.tf              # Outputs (URLs, resource IDs)
├── resource_group.tf       # Resource group
├── container_registry.tf   # ACR
├── key_vault.tf            # Key Vault + secrets
├── network.tf              # VNet (if needed), Container Apps Environment
├── container_apps.tf       # All container app definitions
├── postgresql.tf           # Azure DB for PostgreSQL
├── storage.tf              # Azure Files for persistent volumes
├── log_analytics.tf        # Monitoring
├── email.tf                # Email service
├── environments/
│   ├── dev.tfvars
│   └── prod.tfvars
└── README.md
```

### 8.4 Admin Access

| Service | Admin Access Method |
|---------|-------------------|
| Grafana | SSH tunnel / Azure Bastion OR public ingress with admin credentials from Key Vault |
| InfluxDB | `az containerapp exec` to get a shell, or port-forward with `az containerapp` |
| EMQX Dashboard | Port 18083 — expose temporarily via `az containerapp ingress` or `exec` |
| PostgreSQL | Azure Portal, `psql` via connection string from Key Vault |
| Container Logs | `az containerapp logs show` or Log Analytics |

---

## 9. CI/CD Pipeline

### 9.1 Repository Structure (Proposed)

```
iotdash/
├── .github/
│   └── workflows/
│       ├── ci.yml                  # Lint, test, build on every PR
│       ├── deploy-infra.yml        # Terraform plan/apply on infra/ changes
│       └── deploy-apps.yml         # Build + push images, deploy to Container Apps
├── infra/                          # Terraform (see 8.3)
├── backend/                        # FastAPI application
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic/                    # DB migrations
│   ├── app/
│   │   ├── main.py
│   │   ├── api/                    # Route handlers
│   │   ├── models/                 # SQLAlchemy models
│   │   ├── schemas/                # Pydantic schemas
│   │   ├── services/               # Business logic (grafana_client, alert_sync)
│   │   └── core/                   # Config, security, deps
│   └── tests/
├── frontend/                       # React (Vite)
│   ├── Dockerfile
│   ├── package.json
│   └── src/
├── grafana/                        # Grafana provisioning (existing, enhanced)
│   ├── Dockerfile                  # Custom Grafana image with provisioning
│   └── provisioning/
├── telegraf/
│   └── telegraf.conf
├── docker-compose.yml              # Local dev
├── docker-compose.override.yml     # Local dev overrides
└── docs/
    └── PLANNING.md                 # This document
```

### 9.2 GitHub Actions Workflows

**`ci.yml` — On every PR:**
1. Lint backend (ruff)
2. Type check backend (mypy)
3. Run backend tests (pytest)
4. Lint frontend (eslint)
5. Build frontend (vite build)
6. Terraform fmt + validate

**`deploy-infra.yml` — On merge to `main` when `infra/` changes:**
1. `terraform plan` (post as PR comment on PRs)
2. On `main`: `terraform apply -auto-approve`

**`deploy-apps.yml` — On merge to `main` when app code changes:**
1. Build Docker images (backend, frontend, grafana)
2. Push to Azure Container Registry
3. Update Container App revisions
4. Run DB migrations (`alembic upgrade head`)

### 9.3 Environments

| Environment | Trigger | Azure Subscription |
|-------------|---------|-------------------|
| `dev` | Push to `main` | Dev/test subscription |
| `prod` | Manual approval or tag-based | Production subscription |

---

## 10. Implementation Phases

### Phase 1 — Foundation (Weeks 1-2)

| Task | Description |
|------|-------------|
| Repo restructure | Move to proposed structure (backend/, frontend/, infra/, etc.) |
| PostgreSQL setup | Schema, Alembic migrations, local docker-compose |
| Backend skeleton | FastAPI project, config, DB connection, health endpoint |
| User auth | Registration (admin-only), login, JWT, password hashing |
| Docker Compose v2 | Add PostgreSQL, backend to local docker-compose |
| Secrets cleanup | Move all hardcoded credentials to `.env` file for local dev |

### Phase 2 — Core Web App (Weeks 3-4)

| Task | Description |
|------|-------------|
| Backend CRUD | Organisations, devices, users, dashboard embed APIs |
| Grafana multi-org | Script/API to create orgs, datasources, dashboards per client |
| Grafana embedding | Configure anonymous access, `allow_embedding`, test iframe embed |
| Frontend scaffold | React + Vite + TanStack Router + TanStack Query + Zustand, login page, dashboard page with iframe embeds |
| Frontend dashboard | Device list, embedded Grafana panels, responsive layout |
| Telegraf multi-topic | Extend to `sensors/+/+` with org/device tagging |

### Phase 3 — Alerts (Weeks 5-6)

| Task | Description |
|------|-------------|
| Alert data model | Alert table, backend CRUD API |
| Grafana alert sync | Service that translates web app alerts → Grafana alerting API |
| Email setup | SMTP or SendGrid integration, contact point management |
| Frontend alerts UI | Alert list, create/edit forms, enable/disable toggle |
| Alert testing | End-to-end test: create alert → trigger → receive email |

### Phase 4 — Azure Deployment (Weeks 7-8)

| Task | Description |
|------|-------------|
| Terraform base | Resource group, ACR, Key Vault, Log Analytics |
| Terraform apps | Container Apps Environment, all container app definitions |
| Terraform DB | Azure Database for PostgreSQL |
| Persistent storage | Azure Files volumes for InfluxDB, Grafana |
| CI/CD pipelines | GitHub Actions for infra + app deployment |
| DNS + TLS | Custom domain, managed certificates |
| Admin access | Verify admin can reach all services |

### Phase 5 — Hardening (Weeks 9-10)

| Task | Description |
|------|-------------|
| MQTT auth | Device authentication in EMQX |
| Rate limiting | API rate limiting, MQTT connection limits |
| Monitoring | Log Analytics dashboards, Container App health alerts |
| Backup strategy | PostgreSQL automated backups, InfluxDB backup plan |
| Documentation | Runbooks, admin guide, client onboarding guide |
| Load testing | Simulate N devices, M concurrent users |

---

## 11. Open Questions & Decisions

| # | Question | Options | Recommended | Status |
|---|----------|---------|-------------|--------|
| Q1 | **Grafana embed: public vs proxy?** | A) Grafana public with anon access, B) Backend proxies renders | A for MVP | Pending |
| Q2 | **InfluxDB isolation: tag-based vs bucket-per-org?** | A) Single bucket + tags, B) Bucket per org | A for MVP | Pending |
| Q3 | **Frontend framework?** | A) React, B) Next.js, C) Vue | A (React + Vite + Zustand + TanStack Router/Query) | Decided |
| Q4 | **Auth mechanism?** | A) JWT in httponly cookie, B) Session-based | A (JWT) | Pending |
| Q5 | **Email service?** | A) SendGrid, B) Azure Communication Services, C) Self-hosted SMTP | B (Azure native) | Pending |
| Q6 | **PostgreSQL: Container vs Azure managed?** | A) Container App, B) Azure DB Flexible Server | B for prod, A for dev | Pending |
| Q7 | **Custom domain?** | Need domain name decided | — | Pending |
| Q8 | **Grafana: self-hosted vs Azure Managed Grafana?** | A) Container, B) Azure Managed | A (more control for multi-org + alerting API) | Pending |
| Q9 | **Number of initial sensor types?** | Temperature only? Others? | Start with temperature | Pending |
| Q10 | **User self-registration?** | A) Admin creates users, B) Self-registration with org code | A for MVP | Pending |

---

*End of planning document. See companion documents for detailed specifications:*
- [`docs/ARCHITECTURE.md`](./ARCHITECTURE.md) — Detailed architecture diagrams
- [`docs/API-SPEC.md`](./API-SPEC.md) — Full API specification
- [`docs/RUNBOOK.md`](./RUNBOOK.md) — Operational runbook (post-deployment)
