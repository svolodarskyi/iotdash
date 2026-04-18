# Single-Tenant Deployment Strategy — One Stack Per Client

> **Version:** 0.1.0-draft
> **Date:** 2026-04-12
> **Context:** What if instead of multi-tenant isolation via tags/orgs/filters, each client gets their own isolated deployment? Each client may have up to ~100 devices. This document analyses the approach, when it makes sense, how to operate it at 50-100 clients (5,000-10,000 total devices), and where it breaks.

---

## Table of Contents

1. [The Two Models](#1-the-two-models)
2. [Why Single-Tenant Is Worth Considering](#2-why-single-tenant-is-worth-considering)
3. [Architecture Options](#3-architecture-options)
4. [What Gets Shared vs What Gets Isolated](#4-what-gets-shared-vs-what-gets-isolated)
5. [Deployment & Orchestration](#5-deployment--orchestration)
6. [Cost Analysis](#6-cost-analysis)
7. [Operational Complexity](#7-operational-complexity)
8. [Provisioning & Onboarding Automation](#8-provisioning--onboarding-automation)
9. [Update & Rollout Strategy](#9-update--rollout-strategy)
10. [Monitoring at Scale](#10-monitoring-at-scale)
11. [When This Model Breaks](#11-when-this-model-breaks)
12. [Hybrid Model](#12-hybrid-model)
13. [Comparison: Multi-Tenant vs Single-Tenant vs Hybrid](#13-comparison)
14. [Recommendation](#14-recommendation)

---

## 1. The Two Models

### Multi-Tenant (Current Plan)

```
┌──────────────────────────────────────────┐
│           Single Shared Stack             │
│                                          │
│  EMQX  Telegraf  InfluxDB/TimescaleDB    │
│  Grafana  FastAPI  PostgreSQL            │
│                                          │
│  Client A data ──▶ tag: org_id=A         │
│  Client B data ──▶ tag: org_id=B         │
│  Client C data ──▶ tag: org_id=C         │
│                                          │
│  Isolation via: tags, Grafana orgs,      │
│  JWT scoping, SQL WHERE clauses          │
└──────────────────────────────────────────┘
```

### Single-Tenant (This Document)

```
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Client A Stack   │  │  Client B Stack   │  │  Client C Stack   │
│                  │  │                  │  │                  │
│  EMQX            │  │  EMQX            │  │  EMQX            │
│  Telegraf        │  │  Telegraf        │  │  Telegraf        │
│  TimescaleDB     │  │  TimescaleDB     │  │  TimescaleDB     │
│  Grafana         │  │  Grafana         │  │  Grafana         │
│  FastAPI         │  │  FastAPI         │  │  FastAPI         │
│  PostgreSQL      │  │  PostgreSQL      │  │  PostgreSQL      │
│                  │  │                  │  │                  │
│  Only Client A   │  │  Only Client B   │  │  Only Client C   │
│  data exists     │  │  data exists     │  │  data exists     │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

---

## 2. Why Single-Tenant Is Worth Considering

### 2.1 Problems It Eliminates

| Multi-Tenant Problem | Single-Tenant Solution |
|---------------------|----------------------|
| Grafana multi-org management (provisioning orgs, datasources, dashboards per client) | Each client gets their own Grafana. No multi-org. No anonymous embed hacks. |
| InfluxDB/TimescaleDB cardinality scaling (all clients' data in one DB) | Each client's DB only holds their data. Cardinality stays small. |
| Noisy neighbour (one client's heavy queries slow everyone) | Complete isolation. Client A's workload cannot affect Client B. |
| Security isolation (a bug in tag filtering could leak data across orgs) | Physical separation. No code path can ever show Client A's data to Client B. |
| Grafana alerting multi-org complexity | Each Grafana is single-org. Native alerting, no `X-Grafana-Org-Id` header gymnastics. |
| Compliance / data residency (Client in EU needs data in EU) | Deploy client's stack in the region they require. |
| Custom configuration per client | Each stack can have client-specific settings without affecting others. |

### 2.2 Who Uses This Model

Single-tenant deployment is the standard model for:
- **Enterprise SaaS** (Salesforce's largest clients, Atlassian Data Center)
- **Healthcare / Finance** (data isolation is regulatory requirement)
- **Industrial IoT** (each factory gets its own stack)
- **Managed service providers** (deploy same product N times for N clients)

It's also how many IoT startups operate at 10-100 clients before building true multi-tenancy.

---

## 3. Architecture Options

### Option A: Full Stack Per Client (Maximum Isolation)

Each client gets every component:

```
Per client:
  ├── EMQX (MQTT broker)
  ├── Telegraf (bridge)
  ├── TimescaleDB (time-series)
  ├── Grafana (dashboards + alerting)
  ├── FastAPI (backend)
  └── PostgreSQL (app DB)

Shared:
  ├── Azure Container Registry (images)
  ├── Azure Key Vault (secrets)
  ├── CI/CD pipeline
  ├── DNS management
  └── Admin portal (your internal tool)
```

**Components per client: 6**
**At 50 clients (5,000 devices): 300 containers**
**At 100 clients (10,000 devices): 600 containers**

### Option B: Shared Ingestion, Isolated Application (Balanced)

MQTT and data ingestion are shared (they're stateless bridges). Each client gets their own database and application layer. With up to 100 devices per client, the shared EMQX handles 5,000-10,000 total device connections — comfortably within single-cluster capacity.

```
Shared:
  ├── EMQX (single cluster, topic-based routing)
  │   └── Handles 5K-10K connections (100 clients × up to 100 devices)
  ├── Telegraf (routes by device_id → client's DB)

Per client:
  ├── TimescaleDB (client's own database, ~100 devices worth of telemetry)
  ├── Grafana (client's own instance, ~100 device dashboards)
  ├── FastAPI (client's own backend)
  └── PostgreSQL (client's app DB, or schema in shared PG)
```

**Components per client: 3-4**
**At 50 clients (5,000 devices): ~150-200 containers + shared ingestion**
**At 100 clients (10,000 devices): ~300-400 containers + shared ingestion**

### Option C: Shared Infrastructure, Isolated Databases (Minimal Isolation)

Application code is shared (single FastAPI deployment). Each client gets their own database/schema.

```
Shared:
  ├── EMQX
  ├── Telegraf
  ├── FastAPI (single deployment, routes by client context)
  ├── Grafana (single deployment, multi-org OR label-based)

Per client:
  ├── TimescaleDB schema (separate schema in shared PG instance)
  └── PostgreSQL schema (separate schema in shared PG instance)
```

**This is essentially multi-tenant with database-level isolation.** Less extreme than Options A/B but stronger isolation than tag-based filtering.

### Which Option?

| Factor | Option A (Full) | Option B (Balanced) | Option C (Schema) |
|--------|----------------|--------------------|--------------------|
| Isolation strength | Maximum | Strong | Moderate |
| Cost per client | Highest | Medium | Lowest |
| Operational complexity | Highest | Medium | Lowest |
| Noisy neighbour protection | Complete | Strong (DB isolated) | Moderate |
| Compliance / data residency | Easiest | Possible | Harder |
| Custom config per client | Full flexibility | Good | Limited |
| Scaling effort | Linear | Sub-linear | Sub-linear |
| Grafana complexity | None (single-org per client) | None | Multi-org still needed |

**For the rest of this document, we focus on Option A and Option B** since Option C is closer to the existing multi-tenant plan.

---

## 4. What Gets Shared vs What Gets Isolated

### 4.1 Always Shared (Regardless of Model)

| Component | Why Shared |
|-----------|-----------|
| **Container Registry (ACR)** | Same Docker images for all clients. One build, deployed N times. |
| **CI/CD Pipeline** | Same GitHub Actions workflows. Parameterized by client. |
| **Terraform Modules** | Same infrastructure code. One module, instantiated N times. |
| **DNS Management** | One zone, N subdomains (client-a.iotdash.com, client-b.iotdash.com). |
| **Key Vault** | Secrets per client, but in shared vault (or vault-per-client for strict compliance). |
| **Admin Portal** | Your internal tool for managing all client stacks. |
| **Monitoring/Alerting** | Centralized (you need one view of all client health). |
| **Source Code** | One repo. Client-specific config via environment variables, not code branches. |

### 4.2 Per-Client (Option A — Full Isolation)

| Component | Why Isolated | Provisioned How |
|-----------|-------------|-----------------|
| **EMQX** | Client devices connect to their own broker | Terraform module |
| **Telegraf** | Reads from client's EMQX, writes to client's DB | Terraform module |
| **TimescaleDB** | Client's telemetry data | Azure PG Flexible Server (1 per client) OR shared server with DB-per-client |
| **Grafana** | Client's dashboards and alerting | Container App + persistent volume |
| **FastAPI** | Client's API instance | Container App |
| **PostgreSQL** | Client's app data (users, alerts) | Same Azure PG instance as TimescaleDB (different database) |

### 4.3 Per-Client (Option B — Shared Ingestion)

| Component | Shared/Isolated | Notes |
|-----------|----------------|-------|
| **EMQX** | Shared (clustered) | Topic prefix routing: `{client_id}/{device_id}/from/message` |
| **Telegraf** | Shared (with output routing) | Telegraf can route to different outputs based on tags, OR use one Telegraf per client writing to that client's DB |
| **TimescaleDB** | Isolated (DB per client) | On shared Azure PG Flexible Server, one database per client |
| **Grafana** | Isolated | One container per client |
| **FastAPI** | Isolated | One container per client |
| **PostgreSQL** | Isolated (DB per client) | Same Azure PG server, separate databases |

---

## 5. Deployment & Orchestration

### 5.1 Container Apps (Current Plan, up to ~50 clients)

Azure Container Apps can host multiple apps in one Container Apps Environment.

```
Container Apps Environment: cae-iotdash-prod
│
├── Shared:
│   ├── ca-emqx (if Option B)
│   └── ca-admin-portal
│
├── Client: acme
│   ├── ca-acme-grafana
│   ├── ca-acme-backend
│   ├── ca-acme-telegraf (if Option A)
│   └── ca-acme-emqx (if Option A)
│
├── Client: beta
│   ├── ca-beta-grafana
│   ├── ca-beta-backend
│   ├── ca-beta-telegraf
│   └── ca-beta-emqx
│
└── ... (50-100 clients)
```

**Container Apps Limits:**

| Limit | Value | Impact at 100 clients |
|-------|-------|-----------------------|
| Apps per environment | 100 (soft limit, can request increase) | Option A: 600 apps → need multiple environments or exception. Option B: ~300 apps → need exception. |
| Environments per subscription | 15 (soft limit) | May need 2-6 environments |
| CPU per environment | 300 cores (Workload Profiles) | Shared across all apps |
| Custom domains per app | 10 | Fine |

**At 50+ clients, Container Apps gets strained.** You'll need multiple Container Apps Environments or move to Kubernetes.

### 5.2 Kubernetes / AKS (50+ clients)

Kubernetes is the natural orchestrator for N-deployment patterns.

**Namespace-per-client model:**

```
AKS Cluster
│
├── Namespace: shared
│   ├── Deployment: emqx-cluster (if Option B)
│   ├── Deployment: admin-portal
│   └── ConfigMap: global-config
│
├── Namespace: client-acme
│   ├── Deployment: grafana
│   ├── Deployment: backend
│   ├── Deployment: telegraf
│   ├── Service: grafana-svc
│   ├── Service: backend-svc
│   ├── Ingress: acme.iotdash.com
│   ├── Secret: acme-db-credentials
│   └── PVC: acme-grafana-data
│
├── Namespace: client-beta
│   ├── ... (same structure)
│
└── Namespace: client-xyz
    ├── ...
```

**Why Kubernetes works well here:**
- Namespaces provide natural isolation (RBAC, network policies, resource quotas)
- Helm charts + values files = same template, different config per client
- Resource quotas per namespace prevent noisy neighbour at compute level
- Network policies prevent cross-namespace traffic
- Horizontal Pod Autoscaler per deployment
- Single cluster serves 50-200+ clients easily

**Helm chart structure:**

```
charts/iotdash-client/
├── Chart.yaml
├── values.yaml              # defaults
├── templates/
│   ├── namespace.yaml
│   ├── grafana-deployment.yaml
│   ├── grafana-service.yaml
│   ├── backend-deployment.yaml
│   ├── backend-service.yaml
│   ├── telegraf-deployment.yaml
│   ├── ingress.yaml
│   ├── secrets.yaml
│   ├── pvc.yaml
│   └── network-policy.yaml
└── clients/
    ├── acme.values.yaml     # client-specific overrides
    ├── beta.values.yaml
    └── xyz.values.yaml
```

**Client values file:**
```yaml
# clients/acme.values.yaml
clientId: acme
clientName: "Acme Corp"
domain: acme.iotdash.com

database:
  host: psql-iotdash-prod.postgres.database.azure.com
  name: acme_db
  # password from Azure Key Vault

grafana:
  adminPassword: vault:kv-iotdash/acme-grafana-admin
  resources:
    cpu: 500m
    memory: 1Gi

backend:
  replicas: 1
  resources:
    cpu: 250m
    memory: 512Mi

telegraf:
  influxdbUrl: "" # not used if TimescaleDB
  postgresHost: psql-iotdash-prod.postgres.database.azure.com
  postgresDb: acme_db

emqx:
  enabled: false  # using shared EMQX (Option B)

devices:
  - code: sensor01
    name: "Warehouse Sensor"
  - code: sensor02
    name: "Office Sensor"
```

**Deploy a new client:**
```bash
helm install client-acme ./charts/iotdash-client \
  -f clients/acme.values.yaml \
  -n client-acme --create-namespace
```

**Update all clients to new version:**
```bash
for client in $(ls clients/*.values.yaml); do
  name=$(basename $client .values.yaml)
  helm upgrade client-$name ./charts/iotdash-client \
    -f clients/$name.values.yaml \
    -n client-$name
done
```

### 5.3 AKS Cluster Sizing

Assumes ~100 devices per client. Each client's backend and Grafana handle more load than a 5-device client, so container resources are sized accordingly (0.5 CPU, 1GB each).

| Clients | Total Devices | Containers (Option B) | AKS Nodes (4 CPU, 16GB each) | Est. AKS Cost/month |
|---------|--------------|----------------------|------------------------------|-------------------|
| 10 | ~1,000 | ~40 | 3-4 nodes | $200-400 |
| 50 | ~5,000 | ~200 | 8-12 nodes | $700-1,200 |
| 100 | ~10,000 | ~400 | 15-25 nodes | $1,200-2,500 |

AKS control plane is free. Cost is only for worker nodes (VMs).

**Note on per-client resource allocation:** A client with 100 devices generates ~100 msg/sec of telemetry. Their Grafana evaluates dashboards over ~100 device time-series. Their backend handles API calls for ~100 device embed URLs. This is still lightweight per-container (0.5 CPU, 1GB is sufficient), but more than a 5-device client would need.

---

## 6. Cost Analysis

### 6.1 Multi-Tenant vs Single-Tenant Cost Per Client

**Baseline assumption:** Each client has up to 100 devices sending 1 msg/sec = 100 msg/sec per client.
At 50 clients: 5,000 devices, 5,000 msg/sec aggregate.
At 100 clients: 10,000 devices, 10,000 msg/sec aggregate.

**Multi-tenant (shared stack):**
```
Total stack cost: ~$500-1,200/month (Stage 3 sizing for 5K-10K devices)
Divided by 50 clients: $10-24/client/month infrastructure cost
Divided by 100 clients: $5-12/client/month infrastructure cost
```

**Single-tenant Option A (full isolation):**
```
Per client (~100 devices, ~100 msg/sec):
  EMQX container:        $10-20/month  (0.5 CPU, 1GB — handles 100 connections easily)
  Telegraf container:     $5-10/month   (0.25 CPU, 0.5GB)
  Grafana container:      $10-20/month  (0.5 CPU, 1GB — 100 device dashboards + alerting)
  Backend container:      $10-20/month  (0.5 CPU, 1GB)
  Database (DB on shared server): $8-20/month  (shared Azure PG, ~100 devices of telemetry)
  ─────────────────────────────
  Total per client:       $43-90/month

Shared infra:
  Azure PG Flexible (D8s, shared by all client DBs): $400-500/month
    (100 clients × 100 devices = 10K devices worth of telemetry across all DBs)
  AKS nodes (or Container Apps):                      $1,000-3,000/month
  ACR, Key Vault, Log Analytics:                      $50-100/month
  ─────────────────────────────
  Shared overhead:         $1,450-3,600/month

At 50 clients (5,000 devices):
  Per-client: 50 × $43-90 = $2,150-4,500
  Shared: $1,450-3,600
  Total: $3,600-8,100/month
  Per client: $72-162/month

At 100 clients (10,000 devices):
  Per-client: 100 × $43-90 = $4,300-9,000
  Shared: $1,450-3,600
  Total: $5,750-12,600/month
  Per client: $58-126/month
```

**Single-tenant Option B (shared ingestion):**
```
Per client (~100 devices):
  Grafana container:     $10-20/month  (0.5 CPU, 1GB)
  Backend container:     $10-20/month  (0.5 CPU, 1GB)
  Database (DB on shared server): $8-20/month
  ─────────────────────────────
  Total per client:      $28-60/month

Shared:
  EMQX cluster (3-node, handles 5K-10K connections): $150-300/month
  Telegraf (2 instances for throughput):              $20-40/month
  Azure PG Flexible (D8s):                           $400-500/month
  AKS/Container Apps:                                $800-2,000/month
  Other shared:                                      $50-100/month
  ─────────────────────────────
  Shared:                $1,420-2,940/month

At 50 clients (5,000 devices):
  Per-client: 50 × $28-60 = $1,400-3,000
  Shared: $1,420-2,940
  Total: $2,820-5,940/month
  Per client: $56-119/month

At 100 clients (10,000 devices):
  Per-client: 100 × $28-60 = $2,800-6,000
  Shared: $1,420-2,940
  Total: $4,220-8,940/month
  Per client: $42-89/month
```

### 6.2 Cost Comparison Table

Assumes ~100 devices per client, 1 msg/sec per device.

| Model | 10 clients (1K devices) | 50 clients (5K devices) | 100 clients (10K devices) |
|-------|------------------------|------------------------|--------------------------|
| **Multi-tenant** | $300-600 ($30-60/ea) | $500-1,200 ($10-24/ea) | $800-1,500 ($8-15/ea) |
| **Single-tenant Option A** | $1,900-3,500 ($190-350/ea) | $3,600-8,100 ($72-162/ea) | $5,750-12,600 ($58-126/ea) |
| **Single-tenant Option B** | $1,700-2,500 ($170-250/ea) | $2,820-5,940 ($56-119/ea) | $4,220-8,940 ($42-89/ea) |

**Multi-tenant is 4-8x cheaper per client.** Single-tenant's cost justification must come from higher client pricing (enterprise clients paying $200-500+/month), compliance requirements that mandate isolation, or the engineering time saved by not building multi-tenant complexity.

**Breakeven example:** If your multi-tenant Grafana multi-org setup takes 2 months of engineering time ($20K+) and the single-tenant Helm chart takes 1 week, the extra $2,000-5,000/month in infra cost pays for itself in 4-10 months while you also ship faster.

### 6.3 Database Cost Strategy

**Don't provision a separate Azure PG server per client.** Instead:

```
1 Azure PG Flexible Server (D4s: 4 vCPU, 16GB RAM) = ~$200-250/month
  ├── Database: acme_db       (client Acme — app tables + TimescaleDB hypertables)
  ├── Database: beta_db       (client Beta)
  ├── Database: gamma_db      (client Gamma)
  └── ... (up to ~50-100 databases on one server)

Each database:
  ├── Schema: public (app tables — users, devices, alerts)
  └── Schema: timeseries (TimescaleDB hypertable — telemetry data)
```

PostgreSQL handles 50-100 databases on a single server. Each database is fully isolated (separate tables, indexes, data). Cross-database access requires explicit configuration.

**Sizing consideration at 100 devices/client:**
- Each client generates ~100 writes/sec to their TimescaleDB hypertable
- 50 clients on one PG server = ~5,000 writes/sec aggregate — needs D4s or D8s tier
- 100 clients on one PG server = ~10,000 writes/sec — needs D8s or D16s tier, or split into 2 servers
- Storage: 100 devices × 1 msg/sec × 86,400 sec/day × ~100 bytes × 30 days ≈ 25 GB/client/month (before compression). With TimescaleDB compression (~90%): ~2.5 GB/client/month. At 100 clients: ~250 GB total — manageable on one server.

At 100+ clients or when individual clients have heavy workloads, split into multiple PG servers or dedicated servers for large clients.

---

## 7. Operational Complexity

### 7.1 The Operational Tax

| Operation | Multi-Tenant | Single-Tenant (50 clients) |
|-----------|-------------|---------------------------|
| Deploy new version | 1 deployment | 50 deployments (automated, but 50x rollout time) |
| Monitor health | 1 dashboard | 50 health endpoints to watch |
| Debug an issue | 1 set of logs | Must identify which client's stack has the issue |
| Backup databases | 1 backup job | 50 databases to back up (automated, but 50x storage) |
| SSL certificate renewal | 1 cert (or wildcard) | 1 wildcard cert (*.iotdash.com) covers all |
| Onboard new client | Create org + users in shared DB | Provision entire stack (Terraform/Helm) |
| Decommission client | Delete org data | Destroy stack (Terraform/Helm destroy) — cleaner |
| Grafana dashboard update | Push to N orgs via API | Push to N Grafana instances |
| Security patch (e.g., Grafana CVE) | Update 1 container | Update 50 containers (rolling update) |
| Capacity planning | One stack to right-size | 50 stacks, each potentially different size |

### 7.2 What You Must Automate (Non-Negotiable)

If you choose single-tenant, these must be fully automated. Manual operations at 50 clients are unsustainable.

| Operation | Automation Tool | Effort |
|-----------|----------------|--------|
| **Client provisioning** | Terraform module + Helm chart + onboarding script | 1-2 weeks |
| **Client decommissioning** | Terraform destroy + DB cleanup + DNS removal | 1-2 days |
| **Version rollout** | CI/CD pipeline with rolling deploy across all clients | 1 week |
| **Health monitoring** | Centralized health dashboard (aggregate all clients) | 2-3 days |
| **Log aggregation** | All client logs → shared Log Analytics workspace | 1 day |
| **Backup verification** | Automated backup test (restore to temp DB, verify) | 1-2 days |
| **Certificate management** | Wildcard cert + auto-renewal (Let's Encrypt or Azure) | 1 day |
| **Alerting (your ops)** | Azure Monitor alerts on all client health endpoints | 1 day |

### 7.3 The Admin Portal (Critical)

You need an internal admin tool to manage all client stacks:

```
Admin Portal (internal, for you only)
│
├── Client List
│   ├── Acme Corp  [healthy]  [12 devices]  [v2.3.1]
│   ├── Beta Inc   [degraded] [5 devices]   [v2.3.1]
│   └── Gamma Ltd  [healthy]  [28 devices]  [v2.3.0]  ← needs update
│
├── Actions:
│   ├── Provision New Client
│   │   → Triggers Terraform + Helm + DB migration + DNS
│   ├── Update Client Version
│   │   → Triggers Helm upgrade for selected client
│   ├── Update All Clients
│   │   → Rolling Helm upgrade across all clients
│   ├── View Client Logs
│   │   → Filtered Log Analytics query
│   ├── View Client Metrics
│   │   → Per-client CPU, memory, request rate, device count
│   └── Decommission Client
│       → Terraform destroy + DB drop + DNS cleanup
│
├── Health Overview:
│   ├── All backends responding: 49/50
│   ├── All Grafanas healthy: 50/50
│   ├── Database connections: 234/500
│   └── Active devices across all clients: 847
│
└── Version Matrix:
    ├── v2.3.1: 48 clients
    ├── v2.3.0: 2 clients (update available)
    └── Latest: v2.3.1
```

---

## 8. Provisioning & Onboarding Automation

### 8.1 Terraform Module

```hcl
# modules/client-stack/main.tf

variable "client_id" {}
variable "client_name" {}
variable "region" { default = "westeurope" }
variable "device_count_tier" { default = "small" }  # small, medium, large

# Database (on shared PG server)
resource "azurerm_postgresql_flexible_server_database" "client_db" {
  name      = "${var.client_id}_db"
  server_id = var.shared_pg_server_id
  collation = "en_US.utf8"
  charset   = "UTF8"
}

# Secrets
resource "azurerm_key_vault_secret" "db_password" {
  name         = "${var.client_id}-db-password"
  value        = random_password.db.result
  key_vault_id = var.shared_key_vault_id
}

resource "azurerm_key_vault_secret" "grafana_admin" {
  name         = "${var.client_id}-grafana-admin"
  value        = random_password.grafana.result
  key_vault_id = var.shared_key_vault_id
}

# DNS
resource "azurerm_dns_cname_record" "client" {
  name                = var.client_id
  zone_name           = var.dns_zone_name
  resource_group_name = var.dns_rg
  ttl                 = 300
  record              = var.ingress_fqdn
}

# Kubernetes namespace + Helm release (if using AKS)
resource "helm_release" "client_stack" {
  name       = "client-${var.client_id}"
  chart      = "../charts/iotdash-client"
  namespace  = "client-${var.client_id}"
  create_namespace = true

  values = [
    templatefile("${path.module}/client-values.tpl.yaml", {
      client_id    = var.client_id
      client_name  = var.client_name
      db_host      = var.shared_pg_host
      db_name      = "${var.client_id}_db"
      db_password  = random_password.db.result
      grafana_pass = random_password.grafana.result
      domain       = "${var.client_id}.${var.base_domain}"
      image_tag    = var.app_version
    })
  ]
}
```

**Onboard a new client:**
```bash
# 1. Add client to Terraform
cat >> clients.tf <<EOF
module "client_newcorp" {
  source      = "./modules/client-stack"
  client_id   = "newcorp"
  client_name = "New Corp Industries"
}
EOF

# 2. Apply
terraform plan
terraform apply

# 3. Run DB migrations
kubectl exec -n client-newcorp deploy/backend -- alembic upgrade head

# 4. Seed admin user
kubectl exec -n client-newcorp deploy/backend -- python -m app.seed \
  --email admin@newcorp.com \
  --password "initial-pass-123"

# 5. Verify
curl https://newcorp.iotdash.com/api/health
```

**Total time to onboard: ~5 minutes** (mostly Terraform apply waiting for Azure resources).

### 8.2 Decommission a Client

```bash
# 1. Remove from Terraform
# Delete the module block from clients.tf

# 2. Destroy
terraform plan   # shows resources to destroy
terraform apply  # destroys namespace, Helm release, DNS record

# 3. Drop database
az postgres flexible-server db delete \
  --server-name psql-iotdash-prod \
  --database-name newcorp_db \
  --resource-group rg-iotdash-prod

# 4. Remove secrets from Key Vault
az keyvault secret delete --vault-name kv-iotdash --name newcorp-db-password
az keyvault secret delete --vault-name kv-iotdash --name newcorp-grafana-admin
```

**Clean. Complete. No data remnants in shared tables.**

This is a major advantage over multi-tenant: decommissioning is `DROP DATABASE`, not "delete all rows WHERE org_id = X across 6 tables and hope you didn't miss a foreign key."

---

## 9. Update & Rollout Strategy

### 9.1 Rolling Updates

Never update all clients simultaneously. Use canary rollout:

```
Phase 1 (Canary):     Update 1 internal/test client
  → Verify health, run smoke tests
  → Wait 1 hour

Phase 2 (Early Adopter): Update 5 low-risk clients
  → Monitor for 24 hours
  → Check error rates, latency, alert functionality

Phase 3 (General):    Update remaining clients in batches of 10
  → 10 clients per batch, 30-minute wait between batches
  → Automated rollback if health check fails

Phase 4 (Stragglers): Update remaining clients that were excluded
```

**CI/CD pipeline for rolling update:**

```yaml
# .github/workflows/rollout.yml
name: Rolling Client Update

on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Image tag to deploy'
        required: true
      batch_size:
        description: 'Clients per batch'
        default: '10'

jobs:
  rollout:
    runs-on: ubuntu-latest
    steps:
      - name: Get client list
        run: |
          # List all client namespaces
          kubectl get ns -l app=iotdash-client -o name > clients.txt

      - name: Canary (1 client)
        run: |
          client=$(head -1 clients.txt)
          helm upgrade $client ./charts/iotdash-client --set image.tag=${{ inputs.version }}
          sleep 60
          # Health check
          curl -f https://$client.iotdash.com/api/health

      - name: Batch rollout
        run: |
          tail -n +2 clients.txt | xargs -n ${{ inputs.batch_size }} -P 1 \
            bash -c 'for client in "$@"; do
              helm upgrade $client ./charts/iotdash-client --set image.tag=${{ inputs.version }}
            done; sleep 300' _
```

### 9.2 Version Pinning

Some enterprise clients may require version pinning (they don't want updates until they've tested):

```yaml
# clients/bigcorp.values.yaml
clientId: bigcorp
versionPolicy: pinned       # "latest" or "pinned"
pinnedVersion: "2.2.0"      # stays on this version until client approves upgrade
```

Your rollout script skips pinned clients. This is a selling point for enterprise clients.

### 9.3 Database Migrations

Migrations must run per-client database. Automate it:

```bash
#!/bin/bash
# migrate-all.sh — Run Alembic migrations on all client databases

CLIENTS=$(kubectl get ns -l app=iotdash-client -o jsonpath='{.items[*].metadata.name}')

for ns in $CLIENTS; do
  echo "Migrating $ns..."
  kubectl exec -n $ns deploy/backend -- alembic upgrade head
  if [ $? -ne 0 ]; then
    echo "FAILED: $ns — stopping rollout"
    exit 1
  fi
done

echo "All migrations complete."
```

**Important:** Database schema must be backwards-compatible. New code must work with old schema (for the transition period during rolling updates). Never make breaking schema changes in a single release.

---

## 10. Monitoring at Scale

### 10.1 Centralized Health Dashboard

All client stacks report to a single monitoring system:

```
Client A Backend ──▶ ┐
Client B Backend ──▶ ├──▶ Azure Log Analytics Workspace
Client C Backend ──▶ ┘         │
Client A Grafana ──▶ ┐         │
Client B Grafana ──▶ ├──▶      │
Client C Grafana ──▶ ┘         ▼
                          Admin Dashboard
                          (Azure Workbook or custom)
                          │
                          ├── All clients health: 49/50 ✓
                          ├── Failed: client-beta (backend CrashLoopBackOff)
                          ├── Versions: 48 on v2.3.1, 2 on v2.3.0
                          ├── Total devices: 847 active
                          ├── Total alert rules: 1,234
                          └── Alerts firing right now: 7
```

### 10.2 Key Metrics to Monitor Per Client

| Metric | Source | Alert If |
|--------|--------|----------|
| Backend health | `/api/health` endpoint | Down for > 2 minutes |
| Grafana health | `/api/health` endpoint | Down for > 2 minutes |
| Database connections | PG stats | > 80% of pool |
| API error rate | Backend logs | > 5% 5xx in 5 minutes |
| API latency (p95) | Backend logs | > 2 seconds |
| Device data freshness | TimescaleDB | No new telemetry for > 10 minutes |
| Disk usage (Grafana PVC) | Kubernetes metrics | > 80% |
| Pod restarts | Kubernetes events | > 3 in 10 minutes |

### 10.3 Log Aggregation

```
All client containers → stdout/stderr
        │
        ▼ (Kubernetes FluentBit DaemonSet or Azure Container Insights)
        │
Azure Log Analytics Workspace
        │
        ▼
KQL queries:
  // Errors across all clients in last hour
  ContainerLog
  | where LogEntry contains "ERROR"
  | summarize count() by Namespace, bin(TimeGenerated, 5m)

  // Specific client's logs
  ContainerLog
  | where Namespace == "client-acme"
  | where TimeGenerated > ago(1h)
  | order by TimeGenerated desc
```

---

## 11. When This Model Breaks

### 11.1 Scale Limits

| Limit | Threshold | Impact |
|-------|-----------|--------|
| **AKS node count** | ~100 nodes per node pool (1000 per cluster) | Need to optimize resource requests or split clusters |
| **Helm releases** | ~200-300 per cluster (Helm's tiller state) | Need multiple clusters |
| **Azure PG databases** | ~100-200 per server (practical) | Need multiple PG servers |
| **Operational overhead** | ~100+ clients | Need dedicated SRE / platform team |
| **CI/CD time** | ~100+ clients (rolling update takes hours) | Need parallel batch updates |
| **Azure subscription limits** | Various per-resource limits | Request increases or multiple subscriptions |

### 11.2 When to Stop Adding Clients as Separate Stacks

```
Signal: You're spending more time operating stacks than building product.
Signal: Client onboarding takes >1 hour despite automation.
Signal: Rolling updates take >4 hours across all clients.
Signal: You need 2+ people just for infrastructure operations.
Signal: You've hired a team and need multi-tenant economics.
```

At this point (typically 100-200 clients), you either:
1. **Build true multi-tenant** (shared application, database-level isolation)
2. **Split into tiers** (see Hybrid Model below)

---

## 12. Hybrid Model

The most practical approach for a growing IoT platform: **different isolation levels for different client tiers.**

```
┌─────────────────────────────────────────────────────────┐
│                    Your Platform                         │
│                                                         │
│  Tier 1: Shared (Small Clients)                         │
│  ┌───────────────────────────────────────────┐          │
│  │ Multi-tenant shared stack                  │          │
│  │ 30 clients × 1-5 devices each             │          │
│  │ Lowest cost ($5-15/client/month)           │          │
│  │ Tag-based isolation in shared DB           │          │
│  └───────────────────────────────────────────┘          │
│                                                         │
│  Tier 2: Isolated Database (Medium Clients)             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                │
│  │ Client D  │ │ Client E  │ │ Client F  │               │
│  │ Own DB    │ │ Own DB    │ │ Own DB    │               │
│  │ Shared app│ │ Shared app│ │ Shared app│               │
│  └──────────┘ └──────────┘ └──────────┘                │
│  15 clients × 5-50 devices each                         │
│  Medium cost ($30-80/client/month)                      │
│  Database-level isolation, shared compute               │
│                                                         │
│  Tier 3: Dedicated Stack (Enterprise Clients)           │
│  ┌──────────┐ ┌──────────┐                              │
│  │ Client G  │ │ Client H  │                             │
│  │ Full stack│ │ Full stack│                             │
│  │ Own EMQX  │ │ Own EMQX  │                             │
│  │ Own DB    │ │ Own DB    │                             │
│  │ Own region│ │ Own region│                             │
│  └──────────┘ └──────────┘                              │
│  5 clients × 50-500 devices each                        │
│  Highest cost ($200-500+/client/month)                  │
│  Full isolation, SLA, custom config, data residency     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Tier Criteria

| Factor | Tier 1 (Shared) | Tier 2 (Isolated DB) | Tier 3 (Dedicated) |
|--------|----------------|---------------------|-------------------|
| Devices | 1-5 | 5-50 | 50-500+ |
| Monthly price | $29-99 | $199-499 | $999-5,000+ |
| SLA | Best effort | 99.5% | 99.9% |
| Data residency | Shared region | Shared region | Client-chosen region |
| Custom config | No | Limited | Full |
| Compliance cert | Shared | Shared | Dedicated audit |
| Support | Email | Email + chat | Dedicated account manager |
| Noisy neighbour risk | Possible | Low (DB isolated) | None |

**This is how most B2B SaaS platforms operate at scale.** Start with Tier 3 (dedicated, simplest to build), add Tier 1 (shared, cheapest to operate) when you have enough small clients, add Tier 2 (middle ground) when needed.

---

## 13. Comparison

| Factor | Multi-Tenant | Single-Tenant | Hybrid |
|--------|-------------|---------------|--------|
| **Cost per client** | Lowest ($5-15) | Highest ($40-110) | Varies by tier |
| **Isolation** | Weakest (code-enforced) | Strongest (physical) | Varies by tier |
| **Onboarding speed** | Fast (create DB rows) | Medium (provision stack) | Varies by tier |
| **Decommissioning** | Messy (delete rows across tables) | Clean (destroy stack) | Varies by tier |
| **Version management** | One version for all | Can pin per client | Can pin per tier/client |
| **Compliance** | Harder (shared infra) | Easier (isolated) | Flexible |
| **Data residency** | Hard (one region) | Easy (deploy anywhere) | Flexible |
| **Operational complexity** | Low (one stack) | High (N stacks) | Medium |
| **Development complexity** | High (must enforce isolation in code) | Low (isolation is free) | Medium |
| **Grafana** | Multi-org (complex) | Single-org per client (simple) | Mix |
| **When to choose** | >50 small clients, cost-sensitive | <50 enterprise clients, isolation-critical | Growing platform, mixed client sizes |

---

## 14. Recommendation

### For IoTDash Now (Stage 1-2, 1-10 clients)

**Start with single-tenant (Option B).** Here's why:

1. You have few clients. The operational overhead is minimal at 5-10 stacks.
2. You avoid the entire multi-org Grafana complexity. Each client gets a simple, single-org Grafana.
3. Isolation is free. No risk of data leaks between clients. No `WHERE org_id = X` bugs.
4. Decommissioning is clean. `DROP DATABASE` + `helm uninstall`. Done.
5. You can deploy Grafana with native alerting per client with zero multi-org API gymnastics.
6. Client-specific customization is a values file change, not a code change.

### When to Add Multi-Tenant Tier (Stage 3, 30+ small clients)

When you have enough small clients (1-5 devices each) that the per-client infrastructure cost is disproportionate, add a shared tier:
- Build the multi-tenant shared stack for small/cheap clients
- Keep dedicated stacks for enterprise clients
- Two tiers operating simultaneously

### The Evolution

```
Today:           All clients → Dedicated stack (Option B)
Stage 3 (30+):   Small clients → Shared tier
                  Enterprise → Dedicated stack
Stage 4 (100+):  Small → Shared
                  Medium → Isolated DB (shared compute)
                  Enterprise → Dedicated
                  Critical → Dedicated in client's region
```

This is a natural progression. You're not locked into a decision — you can migrate clients between tiers as the platform matures.

---

*Companion documents: [`SCALING-STRATEGY.md`](./SCALING-STRATEGY.md), [`ARCHITECTURE.md`](../planning/ARCHITECTURE.md), [`PLANNING.md`](../planning/PLANNING.md)*
