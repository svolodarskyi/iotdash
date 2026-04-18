# Scaling Strategy — When to Change What

> **Version:** 0.1.0-draft
> **Date:** 2026-04-12
> **Context:** Growth path from 10 devices to 100,000+. When to substitute components, adopt managed services, introduce streaming, and what it costs on Azure vs AWS.

---

## Table of Contents

1. [Current Stack & Breaking Points](#1-current-stack--breaking-points)
2. [Growth Stages Overview](#2-growth-stages-overview)
3. [MQTT Broker Scaling](#3-mqtt-broker-scaling)
4. [When to Introduce Kafka, Flink, or a Streaming Architecture](#4-when-to-introduce-kafka-flink-or-a-streaming-architecture)
5. [Time-Series Database Scaling](#5-time-series-database-scaling)
6. [Grafana Scaling & When to Drop It](#6-grafana-scaling--when-to-drop-it)
7. [PostgreSQL Scaling](#7-postgresql-scaling)
8. [Managed IoT Services — Azure vs AWS](#8-managed-iot-services--azure-vs-aws)
9. [Azure vs AWS Full Comparison](#9-azure-vs-aws-full-comparison)
10. [Cost Projections](#10-cost-projections)
11. [Migration Paths](#11-migration-paths)
12. [Decision Framework](#12-decision-framework)

---

## 1. Current Stack & Breaking Points

| Component | Current | Breaking Point | What Breaks |
|-----------|---------|----------------|-------------|
| **EMQX** (MQTT) | Single node, 0.5 CPU, 1GB | ~2,000-5,000 connections | Connections refused, message drops |
| **Telegraf** | Single instance | ~50,000-100,000 msg/sec | Write backpressure, data loss |
| **InfluxDB** | Single node OSS 2.7 | ~1M series cardinality OR ~500K points/sec | Queries slow to minutes, OOM crashes |
| **Grafana** | Single node, multi-org | ~50-100 orgs | Provisioning API overhead, anonymous embed limitations |
| **PostgreSQL** | Planned (Burstable) | ~500 concurrent connections | Connection exhaustion |
| **FastAPI** | Planned (single replica) | ~1000 req/sec | Latency spikes |

**The key bottleneck progression:**
```
Stage 1 (10 devices):     Nothing is a bottleneck
Stage 2 (100 devices):    Nothing is a bottleneck
Stage 3 (1,000 devices):  InfluxDB cardinality starts mattering
Stage 4 (10,000 devices): EMQX needs clustering, InfluxDB is strained, Grafana multi-org is painful
Stage 5 (100,000 devices): Everything needs to be managed/clustered/replaced
```

---

## 2. Growth Stages Overview

### The Complete Picture

| | **Stage 1** | **Stage 2** | **Stage 3** | **Stage 4** |
|-|-------------|-------------|-------------|-------------|
| **Orgs** | 1-10 | 10-50 | 50-200 | 200+ |
| **Devices** | 1-100 | 100-1,000 | 1,000-10,000 | 10,000+ |
| **Msg/sec** | 1-100 | 100-1,000 | 1,000-10,000 | 10,000+ |
| **Alert rules** | 1-50 | 50-500 | 500-2,000 | 2,000+ |
| **MQTT** | EMQX single node | EMQX single (scaled up) | EMQX 3-node cluster | IoT Hub/Core OR EMQX 5+ |
| **Bridge** | Telegraf x1 | Telegraf x1 | Telegraf x2 | **Kafka/Event Hubs** |
| **TSDB** | InfluxDB OSS | InfluxDB OSS (tuned) | **TimescaleDB** | TimescaleDB Cloud / ADX |
| **Dashboards** | Grafana multi-org | Grafana multi-org | Grafana (strain) | **Custom React charts** OR Grafana Enterprise |
| **App DB** | Azure PG Burstable B1ms | Azure PG Burstable B2s | Azure PG General Purpose D2s | Azure PG D4s + read replicas |
| **Backend** | FastAPI x1 | FastAPI x2 | FastAPI x3-5 | FastAPI on K8s (AKS) |
| **Alerting** | Grafana native | Grafana + webhook → app | Grafana + External Alertmanager | Custom alerting engine |
| **Email** | SendGrid free | SendGrid/SES via app queue | SES with digest mode | Notification service |
| **Queue** | None | PostgreSQL queue | PostgreSQL queue | **RabbitMQ or Kafka** |
| **Infra** | Container Apps | Container Apps | Container Apps | AKS (Kubernetes) |
| **Est. cost** | $100-200/mo | $200-400/mo | $500-1,200/mo | $1,500-5,000+/mo |

---

## 3. MQTT Broker Scaling

### 3.1 EMQX Scaling Characteristics

**Single node (your current Container App: 0.5 CPU, 1GB):**

| Metric | Limit |
|--------|-------|
| Concurrent connections | ~2,000-5,000 |
| Messages/sec (QoS 0) | ~10,000-20,000 |
| Messages/sec (QoS 1) | ~5,000-10,000 |

**Single node (scaled up: 4 CPU, 8GB):**

| Metric | Limit |
|--------|-------|
| Concurrent connections | ~50,000-100,000 |
| Messages/sec (QoS 0) | ~100,000-200,000 |

**3-node cluster:**

| Metric | Limit |
|--------|-------|
| Concurrent connections | ~300,000-500,000 |
| Messages/sec | ~500,000-1,000,000 |

**When to cluster:**
- More than 5,000 concurrent device connections
- Need high availability (any production deployment)
- More than 50,000 msg/sec

### 3.2 MQTT Broker Alternatives

| Broker | Max Conns (single) | Clustering | Best For |
|--------|-------------------|------------|----------|
| **EMQX** | ~1M (tuned) | Yes, built-in | Your project. General IoT, large scale. |
| **HiveMQ** | ~1M (tuned) | Yes, native | Enterprise, strong MQTT 5.0 |
| **Mosquitto** | ~50K-100K | **No clustering** | Edge gateways, prototyping. Not for platforms. |
| **VerneMQ** | ~500K | Yes, Erlang | Cost-sensitive, community support only |

**Verdict:** Stay with EMQX. It's the right choice at every stage. Just scale up (node size) then out (cluster).

---

## 4. When to Introduce Kafka, Flink, or a Streaming Architecture

This is the most common premature optimization in IoT platforms. Here's when you actually need it.

### 4.1 Your Current Architecture (Simple Pipeline)

```
Devices ──MQTT──▶ EMQX ──subscribe──▶ Telegraf ──write──▶ InfluxDB
                                                              │
                                                    Grafana queries
```

**This is a batch-pull pipeline.** Telegraf subscribes to MQTT, buffers messages, and flushes to InfluxDB in batches. Grafana queries InfluxDB on a schedule. There is no "stream processing" — data flows through in a simple pipe.

**This works until you need one of these things:**

### 4.2 Signals That You Need Streaming

| Signal | Why It Means Streaming | Threshold |
|--------|----------------------|-----------|
| **Multiple consumers need the same data** | Telegraf writes to InfluxDB, but you also need the same messages for real-time alerting, audit log, billing, ML pipeline | When you have 3+ consumers for the same MQTT data |
| **You need to replay historical messages** | A bug in your alerting logic lost 2 days of data. You need to reprocess it. With MQTT, messages are gone after delivery. | When data reprocessing is a business requirement |
| **Telegraf can't keep up** | InfluxDB write latency spikes cause Telegraf's internal buffer to fill. Messages are dropped. | When message ingestion rate exceeds Telegraf's flush rate for sustained periods |
| **You need complex event processing** | "Alert if temperature rises >5°C in 10 minutes across any 3 devices in the same org" — this requires windowed aggregation across devices | When alert logic goes beyond single-device threshold checks |
| **You need exactly-once semantics** | Billing, compliance, or SLA tracking requires guaranteed processing — no duplicates, no drops | When financial or regulatory consequences exist for missed/duplicate messages |
| **Message ordering matters** | Device commands must be processed in order. MQTT QoS 0 doesn't guarantee this. | When out-of-order processing causes incorrect device state |

### 4.3 The Streaming Architecture

```
Devices ──MQTT──▶ EMQX ──bridge──▶ Kafka / Event Hubs
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
            Consumer Group 1    Consumer Group 2    Consumer Group 3
            Telegraf/Flink      FastAPI Workers     Audit Logger
            → InfluxDB/         → Real-time alerts  → Blob Storage
              TimescaleDB       → Anomaly detection → Compliance DB
                                → Device state mgmt
```

### 4.4 Kafka vs Event Hubs vs RabbitMQ — When to Use What

| | **RabbitMQ** | **Apache Kafka** | **Azure Event Hubs** |
|-|-------------|-----------------|---------------------|
| **What it is** | Message broker (queue-based) | Distributed event log | Managed Kafka-compatible event streaming |
| **Message model** | Queue: message consumed once, removed | Log: messages retained, multiple consumers replay | Same as Kafka |
| **Ordering** | Per-queue FIFO | Per-partition FIFO | Per-partition FIFO |
| **Throughput** | ~50K-100K msg/sec | ~1M-10M+ msg/sec per cluster | ~1M msg/sec per namespace |
| **Retention** | Until consumed (or TTL) | Configurable (hours/days/forever) | Up to 90 days (7 default) |
| **Replay** | No (message gone after ACK) | Yes (consumer rewinds offset) | Yes |
| **Operational complexity** | Low-medium | **High** (3+ brokers, KRaft, partition mgmt) | **None** (fully managed) |
| **Min viable deployment** | 1 node | 3 nodes (or KRaft mode) | N/A (managed) |
| **Azure managed option** | No native (run in container) | No native (use Event Hubs Kafka mode) | **Yes — native** |
| **AWS managed option** | Amazon MQ | Amazon MSK | — |
| **Cost (managed, basic)** | ~$50-150/mo (Amazon MQ) | ~$200-500/mo (MSK) | ~$100-300/mo (Standard) |

### 4.5 When to Introduce Each

**RabbitMQ — Stage 3 (1,000-10,000 devices):**
```
Use for:
  - Device command queuing (platform → device commands need guaranteed delivery)
  - Async background jobs (Grafana sync, email sending, report generation)
  - Work distribution across multiple FastAPI workers

Don't use for:
  - Telemetry data pipeline (Telegraf handles this)
  - Event replay (RabbitMQ deletes messages after consumption)
```

**Kafka / Event Hubs — Stage 4 (10,000+ devices):**
```
Use for:
  - Telemetry data pipeline (replace direct Telegraf → InfluxDB with Kafka in between)
  - Multiple consumers (telemetry → TSDB + alerting + ML + audit simultaneously)
  - Event replay (reprocess last 7 days through a new algorithm)
  - Cross-service event backbone

Don't use for:
  - Small deployments (operational overhead not justified under 10K devices)
  - Simple command queuing (RabbitMQ is simpler)
```

### 4.6 Apache Flink — When and Why

**What Flink does:** Real-time stream processing engine. Takes a stream of events in, applies transformations/aggregations/windowing, emits processed results.

**What Flink does NOT do:** It's not a message broker. It sits between Kafka and your output systems.

```
Kafka ──▶ Flink ──▶ TimescaleDB (aggregated metrics)
                ──▶ Alertmanager (complex alert conditions)
                ──▶ Kafka (enriched/transformed events for downstream)
```

**When you need Flink (or similar: Spark Streaming, Kafka Streams, Azure Stream Analytics):**

| Use Case | Example | Without Flink | With Flink |
|----------|---------|--------------|------------|
| **Windowed aggregation** | "Average temperature per device per 5-minute window" | InfluxDB continuous query (works, but limited) | Flink tumbling window (scalable, complex logic) |
| **Cross-device correlation** | "Alert if >3 devices in the same building report errors within 1 minute" | Impossible in Grafana alerting (per-rule, per-device) | Flink CEP (Complex Event Processing) with pattern matching |
| **Enrichment at scale** | "Join every telemetry message with device metadata from PostgreSQL before writing to TSDB" | Telegraf can't do joins | Flink async lookup + join |
| **Anomaly detection** | "Alert if this device's reading deviates >3σ from its rolling 24h average" | Very hard in Grafana (needs continuous query + alert) | Flink ML library or custom operator |
| **Event deduplication** | "Devices sometimes send duplicates; deduplicate within a 10-second window" | Cannot do in Telegraf | Flink keyed window dedup |

**Managed alternatives to self-hosted Flink:**

| Service | Cloud | Cost | Best For |
|---------|-------|------|----------|
| **Azure Stream Analytics** | Azure | ~$0.11/streaming unit/hour (~$80/mo) | SQL-like stream queries, Azure-native |
| **Amazon Managed Flink** | AWS | ~$0.11/KPU/hour (~$80/mo) | Full Flink, Java/Python, AWS-native |
| **Amazon Kinesis Data Analytics** | AWS | Similar | Simpler than Flink, SQL queries on streams |
| **Confluent Cloud ksqlDB** | Any | ~$0.10/CSU/hour | SQL on Kafka, managed, cloud-agnostic |

### 4.7 The Decision Matrix

```
Do you have >3 consumers for the same telemetry stream?
  No  → Stay with Telegraf direct pipeline
  Yes → Introduce Kafka/Event Hubs between EMQX and consumers

Do you need event replay or reprocessing?
  No  → Kafka optional (RabbitMQ sufficient for command queuing)
  Yes → Kafka/Event Hubs required

Do you need complex event processing (cross-device, windowed, ML)?
  No  → Don't introduce Flink. Grafana alerting or simple app logic is enough.
  Yes → Introduce Flink (or Azure Stream Analytics for simpler cases)

Are you processing >10,000 messages/sec?
  No  → Telegraf + InfluxDB handles it. Don't add Kafka.
  Yes → Kafka/Event Hubs for decoupling, backpressure, and fan-out
```

### 4.8 Recommended Architecture by Stage

**Stage 1-2 (1-1,000 devices): Simple Pipeline**
```
Devices ──MQTT──▶ EMQX ──▶ Telegraf ──▶ InfluxDB ──▶ Grafana
```

**Stage 3 (1,000-10,000 devices): Add RabbitMQ for Async Work**
```
Devices ──MQTT──▶ EMQX ──▶ Telegraf ──▶ TimescaleDB ──▶ Grafana
                                │
                    EMQX Rule Engine
                                │
                                ▼
                           RabbitMQ
                           │       │
                      Commands   Async Jobs
                     (to devices) (email, sync)
```

**Stage 4 (10,000+ devices): Kafka + Optional Flink**
```
Devices ──MQTT──▶ EMQX ──bridge──▶ Kafka (Event Hubs)
                                        │
                    ┌───────────────────┼──────────────────────┐
                    │                   │                      │
                    ▼                   ▼                      ▼
               Flink / ASA         Consumer Workers       Audit Writer
               (complex CEP,       (simple routing,       (compliance,
                anomaly detect)     device state)          blob storage)
                    │                   │
                    ▼                   ▼
              TimescaleDB /        Alertmanager
              ADX                  (notifications)
```

**Stage 5 (100,000+ devices): Full Streaming + Managed IoT**
```
Devices ──▶ Azure IoT Hub (device mgmt, DPS, twins)
                    │
                    ▼
             Event Hubs (retention + fan-out)
                    │
        ┌───────────┼──────────┐──────────────┐
        ▼           ▼          ▼              ▼
   Stream Analytics  Flink    Blob Storage    Custom Consumer
   (real-time agg)  (CEP/ML)  (cold archive)  (billing, audit)
        │           │
        ▼           ▼
   TimescaleDB   Alertmanager ──▶ Notification Service
   Cloud / ADX
        │
        ▼
   Custom React Dashboards (API → TimescaleDB)
```

---

## 5. Time-Series Database Scaling

### 5.1 InfluxDB OSS — Limits

| Metric | Comfortable | Strained | Breaking |
|--------|-------------|----------|----------|
| Series cardinality | < 100K | 100K-1M | > 1M (queries degrade, OOM) |
| Write throughput | < 100K pts/sec | 100K-500K | > 500K (single node limit) |
| Query concurrency | < 10 heavy queries | 10-20 | > 20 (timeouts) |

**What is series cardinality in your context?**
Each unique combo of `measurement + tag values` = 1 series.
- 100 devices × 3 message types × 5 fields = 1,500 series (trivial)
- 10,000 devices × 3 types × 10 fields = 300,000 series (manageable)
- 100,000 devices × 10 types × 20 fields = 20,000,000 (**dangerous**)

### 5.2 TimescaleDB — Why and When to Migrate

| Factor | InfluxDB OSS | TimescaleDB |
|--------|-------------|-------------|
| Query language | Flux (being deprecated by InfluxData) | **SQL** (universal) |
| Cardinality limits | Yes (series explosion) | **No** (it's just rows) |
| Join with app data | Not possible | **Native** (same PostgreSQL) |
| Compression | Good | Good (90-95%) |
| Multi-tenancy | Tag-based | **Row-Level Security, schemas, or partitioning** |
| Continuous aggregates | Manual tasks | **Built-in materialized views** |
| Ecosystem | Telegraf, Grafana | **All PostgreSQL tools** + Grafana |

**Migrate at Stage 2-3 boundary (before 1,000 devices).**

Why not later? Because every Grafana dashboard query must be rewritten from Flux to SQL. The more dashboards you have, the more painful the migration. Do it early when you have few dashboards.

**TimescaleDB pricing:**

| Option | Cost/month | Notes |
|--------|-----------|-------|
| Self-hosted (on Azure PG) | $0 (extension is Apache 2.0) | Install extension on your existing Azure PostgreSQL Flexible Server |
| TimescaleDB Cloud | From ~$30/mo | Managed, auto-tuned |

### 5.3 Azure Data Explorer (ADX) vs AWS Timestream

| Factor | ADX | Timestream |
|--------|-----|-----------|
| Query language | KQL (powerful, IoT-specific functions) | SQL-like (limited) |
| Min cost/month | ~$90 (Dev/Test), ~$175 (Production) | Pay-per-use (~$65 at 100 devices) |
| Cost at 1,000 devices (1 msg/sec) | ~$175-300 | **~$1,300** (extremely expensive) |
| Cost at 10,000 devices | ~$300-600 | **~$13,000** (not viable) |
| IoT features | Anomaly detection, forecasting in KQL | Basic |
| Grafana support | Plugin available | Plugin available |
| Verdict | Good at scale (10K+ devices) | **Too expensive for continuous telemetry** |

**Timestream warning:** AWS Timestream charges per write AND per data scanned in queries. Continuous telemetry (1 msg/sec per device) generates massive write volume. Timestream is designed for intermittent/bursty data, not continuous streams.

### 5.4 TSDB Recommendation by Stage

| Stage | Recommendation | Why |
|-------|---------------|-----|
| 1 (1-100 devices) | InfluxDB OSS | Already set up, works fine |
| 2 (100-1,000) | **Migrate to TimescaleDB** | Before cardinality bites, before you have many dashboards to rewrite |
| 3 (1,000-10,000) | TimescaleDB (on Azure PG General Purpose) | Handles scale, SQL, JOINs with app data |
| 4 (10,000+) | TimescaleDB Cloud OR Azure Data Explorer | Managed, scales to billions of points |

---

## 6. Grafana Scaling & When to Drop It

### 6.1 Multi-Org Pain Points

| Orgs | Pain Level | Issues |
|------|-----------|--------|
| 1-20 | Low | Manageable with API automation |
| 20-50 | Medium | Dashboard version drift, provisioning takes time |
| 50-100 | High | Anonymous embed breaks (only works for 1 org by default), API provisioning overhead |
| 100+ | Very High | Consider alternatives |

**The anonymous embed problem:**
Grafana's `[auth.anonymous]` section only applies to ONE default org. For multi-org embedding, you need:
- **Option A:** Auth proxy that injects `X-Grafana-Org-Id` per request — complex
- **Option B:** Service account tokens per org, passed via URL — token management overhead
- **Option C:** Grafana Enterprise with RBAC — costs money
- **Option D:** Drop Grafana embedding. Build custom dashboards.

### 6.2 Managed Grafana (Azure / AWS) — Can't Use It

| Feature | Azure Managed Grafana | Amazon Managed Grafana |
|---------|----------------------|----------------------|
| Multi-org | **No** | **No** |
| Anonymous access | **No** (Azure AD only) | **No** (SAML only) |
| Embed without login | **No** | Signed URLs (time-limited) |

**Both managed Grafana services lack multi-org and anonymous embed.** They are not suitable for your multi-tenant embedding architecture.

### 6.3 When to Build Custom Dashboards

**Trigger:** When Grafana multi-org management overhead exceeds the value of Grafana's built-in visualizations (typically at 100+ orgs or when branding/UX customization is critical).

**What replaces Grafana:**
```
Your React Frontend
    │
    ▼
React charting libraries:
  - Apache ECharts (most full-featured, excellent time-series)
  - Plotly.js (interactive, scientific)
  - Recharts (simple, React-native)
  - Tremor (modern, dashboard-focused)
    │
    ▼
Your FastAPI Backend
    │
    ▼ SQL queries
TimescaleDB
```

**What you gain:**
- Full control over multi-tenancy (no Grafana org management)
- Full branding control
- No iframe limitations (CORS, CSP, cookie issues)
- No Grafana licensing concerns at scale
- Better mobile experience

**What you lose:**
- Grafana's built-in 200+ panel types
- Grafana's explore/ad-hoc query mode
- Grafana's alerting engine (must be replaced)
- Development time (weeks instead of configuration)

---

## 7. PostgreSQL Scaling

### 7.1 Azure Database for PostgreSQL Flexible Server

| Tier | vCores | RAM | Price/month |
|------|--------|-----|-------------|
| Burstable B1ms | 1 | 2 GB | ~$13-25 |
| Burstable B2s | 2 | 4 GB | ~$26-50 |
| General Purpose D2s | 2 | 8 GB | ~$100-125 |
| General Purpose D4s | 4 | 16 GB | ~$200-250 |
| Memory Optimized E2s | 2 | 16 GB | ~$130-160 |

- **PgBouncer**: Built-in (enable via server parameter, no extra cost)
- **Read replicas**: Up to 5 (same region or cross-region)
- **Backup**: 7-35 days, geo-redundant available

### 7.2 AWS RDS PostgreSQL

| Instance | vCPUs | RAM | Price/month |
|----------|-------|-----|-------------|
| db.t4g.micro | 2 | 1 GB | ~$12 |
| db.t4g.small | 2 | 2 GB | ~$24 |
| db.t4g.medium | 2 | 4 GB | ~$48 |
| db.m7g.large | 2 | 8 GB | ~$130 |

- **RDS Proxy**: ~$22/month for connection pooling
- **Read replicas**: Up to 15

### 7.3 When to Scale

| Signal | Action |
|--------|--------|
| > 50 concurrent connections | Enable PgBouncer |
| Query latency > 100ms on app tables | Add indexes, analyze slow query log |
| Query latency > 100ms on telemetry (if using TimescaleDB) | Add continuous aggregates, check chunk size |
| > 200 concurrent connections | Move to General Purpose tier |
| Dashboard reads slow down write-heavy operations | Add read replica for dashboard/reporting queries |

---

## 8. Managed IoT Services — Azure vs AWS

### 8.1 Azure IoT Hub

**What you get:**
- Managed MQTT broker with per-device identity
- Device twins (desired + reported state)
- Device-to-cloud (D2C) and cloud-to-device (C2D) messaging
- Device Provisioning Service (DPS) — zero-touch onboarding
- Message routing (to Event Hubs, Service Bus, Storage, custom endpoints)
- Built-in monitoring and diagnostics

**What you lose (compared to EMQX):**
- Custom MQTT topic structure (IoT Hub uses fixed `devices/{id}/messages/events/`)
- MQTT 5.0 (IoT Hub only supports 3.1.1 as of mid-2025)
- Direct Telegraf integration (need Event Hubs consumer instead)
- Free (IoT Hub costs per-message)

**Pricing:**

| Tier | Messages/day/unit | Price/unit/month | 1,000 devices @ 1 msg/sec |
|------|-------------------|-----------------|--------------------------|
| Free (F1) | 8,000 | $0 | Not enough (need 86.4M/day) |
| Basic B1 | 400,000 | ~$10 | ~$2,160/mo (216 units) |
| Standard S1 | 400,000 | ~$25 | ~$5,400/mo (216 units) |
| Standard S2 | 6,000,000 | ~$250 | ~$3,750/mo (15 units) |
| Standard S3 | 300,000,000 | ~$2,500 | ~$2,500/mo (1 unit) |

**Note:** Standard tier is needed for device twins and C2D. Basic tier is telemetry-only.

### 8.2 Azure IoT Central

IoT Central is a **full IoT SaaS platform** — it's a competitor to what you're building, not a component.

| Feature | IoT Central | Your Platform (IoTDash) |
|---------|------------|------------------------|
| Dashboard builder | Built-in (limited) | Grafana embed (rich) → Custom React (richest) |
| Multi-tenancy | Built-in organizations | Custom (PostgreSQL + Grafana orgs) |
| Device management | Full GUI | Admin panel (custom) |
| Alerting | Built-in rules | Custom (Grafana API + web app) |
| Branding | Limited (logo/color only) | Full control |
| Pricing | ~$0.25-0.70/device/month | Infrastructure cost only |

**Verdict:** Don't use IoT Central. You're building a custom-branded platform. IoT Central competes with your product.

### 8.3 AWS IoT Core

**What you get:**
- Managed MQTT broker (supports MQTT 5.0)
- Device shadows (like Azure Device Twins)
- Rules engine (SQL-like, routes to Lambda, Kinesis, S3, DynamoDB, etc.)
- Device registry with groups and types
- More flexible topic structure than Azure IoT Hub

**What you lose:**
- Direct Telegraf integration
- Free

**Pricing:**

| Component | Price |
|-----------|-------|
| Connectivity | $0.08 per 1M connection-minutes |
| Messaging | $1.00 per 1M messages (5KB chunks) |
| Rules triggered | $0.15 per 1M |
| Rules actions | $0.15 per 1M |
| Shadow updates | $1.25 per 1M |

**1,000 devices @ 1 msg/sec:**
- Connectivity: ~$3.50/mo
- Messaging: 2.59B messages/mo = **~$2,590/mo**
- Rules: ~$390/mo
- **Total: ~$3,000/mo**

This is 30x the cost of running EMQX on a $100/mo container.

### 8.4 When Managed IoT Makes Sense

| Signal | Self-Hosted EMQX | Managed IoT Hub/Core |
|--------|------------------|---------------------|
| < 10,000 devices | **Cheaper, simpler** | Expensive overkill |
| Need custom MQTT topics | **Required** | IoT Hub can't do custom topics |
| Need MQTT 5.0 | **EMQX supports it** | Only AWS IoT Core |
| Need zero-touch device provisioning (DPS) | Build it yourself (complex) | **Built-in** |
| Need device twins / state management | Build it yourself | **Built-in** |
| Need firmware OTA updates | Build it yourself | **Built-in** |
| > 50,000 devices, global distribution | Complex EMQX clustering | **Managed, auto-scaling** |
| Regulatory compliance (ISO 27001, SOC 2) | You certify your EMQX deployment | **Pre-certified** |
| Team size < 3, no DevOps capacity | Operational burden | **Reduced ops** |

**Recommendation:** Stay with EMQX through Stage 3. Evaluate Azure IoT Hub at Stage 4 **only if** device lifecycle management (provisioning, twins, firmware updates) becomes a bigger problem than the messaging cost.

### 8.5 Devices Compatible with Managed IoT

| Device Type | Protocol | Azure IoT Hub | AWS IoT Core | EMQX |
|-------------|----------|--------------|-------------|------|
| ESP32/ESP8266 | MQTT | Yes (Arduino SDK) | Yes (Arduino SDK) | Yes (any MQTT lib) |
| Raspberry Pi | MQTT | Yes (Python/C SDK) | Yes (Python/C SDK) | Yes (any MQTT lib) |
| STM32 / ARM MCU | MQTT | Yes (C SDK, Azure RTOS) | Yes (FreeRTOS SDK) | Yes (MQTT-C, Paho embedded) |
| Industrial PLC (Modbus/OPC-UA) | Gateway needed | IoT Edge gateway | Greengrass gateway | Neuron gateway (EMQX) |
| LoRaWAN devices | LoRa → gateway → MQTT | Via IoT Edge or TTN integration | Via Sidewalk or TTN | Via LoRa gateway + MQTT |
| Cellular (LTE-M / NB-IoT) | MQTT or HTTPS | Yes | Yes | Yes |

**Key point:** All common IoT devices can speak standard MQTT. The choice of broker (EMQX vs IoT Hub vs IoT Core) does not limit which devices you can support. The difference is in authentication, topic structure, and device management features.

---

## 9. Azure vs AWS Full Comparison

Since your infrastructure is planned for Azure, here's a comparison for future reference:

| Component | Azure Option | AWS Option | IoTDash Recommendation |
|-----------|-------------|------------|----------------------|
| **Container orchestration** | Container Apps ($15-30/app) | ECS Fargate ($20-40/service) | Azure (already planned) |
| **Kubernetes** | AKS (free control plane) | EKS ($73/mo control plane) | Azure (cheaper control plane) |
| **IoT broker (managed)** | IoT Hub ($25-2500/unit) | IoT Core (per-message) | **Neither** until Stage 4 |
| **Event streaming** | Event Hubs ($100-300/mo) | MSK ($200-500/mo) | Azure Event Hubs (simpler) |
| **Stream processing** | Stream Analytics ($80/mo) | Managed Flink ($80/mo) | Azure (simpler for SQL-like) |
| **PostgreSQL (managed)** | Flexible Server ($13-250/mo) | RDS ($12-260/mo) | Azure (built-in PgBouncer) |
| **Time-series DB** | ADX ($175+/mo) | Timestream (**very expensive**) | **TimescaleDB on Azure PG** |
| **Grafana (managed)** | Managed Grafana (no multi-org) | Managed Grafana (no multi-org) | **Self-hosted** (multi-org needed) |
| **Secrets** | Key Vault (~$1/mo) | Secrets Manager ($0.40/secret/mo) | Azure (already planned) |
| **Email** | ACS ($0.25/1K) | SES ($0.10/1K) | SendGrid initially, then ACS or SES |
| **Container registry** | ACR Basic ($5/mo) | ECR ($0.10/GB) | Azure (already planned) |
| **Blob storage** | Blob Storage | S3 | Azure |
| **CDN** | Azure CDN or Cloudflare | CloudFront or Cloudflare | Cloudflare (cloud-agnostic, free tier) |

**Verdict:** Stay on Azure. The only AWS advantage is IoT Core's MQTT 5.0 support (IoT Hub lacks it) and SES's cheaper email pricing. Neither justifies switching clouds.

---

## 10. Cost Projections

### Monthly Infrastructure Cost by Stage

```
                 Stage 1        Stage 2        Stage 3        Stage 4
Component        (10 devices)   (500 devices)  (5K devices)   (50K devices)
───────────────  ─────────────  ─────────────  ─────────────  ──────────────
EMQX             $15-30         $30-50         $100-200       $300-600
Telegraf         $8-15          $8-15          $20-30         Replaced by Kafka consumers
InfluxDB         $30-50         $50-100        Replaced       Replaced
TimescaleDB      —              —              $100-300       $300-1000 (Cloud)
Kafka/Event Hubs —              —              —              $200-500
Grafana          $15-30         $15-30         $30-50         $0-500 (custom or Enterprise)
PostgreSQL       $15-25         $30-50         $100-150       $200-500
FastAPI          $15-30         $30-60         $60-120        $200-500 (K8s)
RabbitMQ         —              —              $30-50         Replaced by Kafka
Email service    $0             $0-20          $20-50         $50-200
Key Vault        $1             $1             $1             $5
ACR              $5             $5             $5             $20
Log Analytics    $0-10          $10-20         $20-40         $50-100
CDN              —              —              $0-20          $20-50
───────────────  ─────────────  ─────────────  ─────────────  ──────────────
TOTAL            $100-200       $200-400       $500-1,200     $1,500-5,000+
Per-device cost  $10-20/device  $0.40-0.80     $0.10-0.24     $0.03-0.10
```

**The cost-per-device drops dramatically with scale.** This is the business model: charge clients $5-20/device/month while your cost is $0.10-1.00/device.

---

## 11. Migration Paths

### 11.1 InfluxDB → TimescaleDB (Do at Stage 2-3)

| Step | Action | Breaks What |
|------|--------|------------|
| 1 | Create TimescaleDB hypertable on Azure PG | Nothing (additive) |
| 2 | Configure Telegraf dual-output (InfluxDB + PostgreSQL) | Nothing (parallel write) |
| 3 | Migrate historical data (export → transform → import) | Nothing (background job) |
| 4 | Rewrite Grafana dashboards from Flux to SQL | Grafana dashboards |
| 5 | Update backend (if any InfluxDB queries) to SQL | Backend code |
| 6 | Remove InfluxDB output from Telegraf | Nothing |
| 7 | Remove InfluxDB container | Nothing |

**Biggest cost:** Rewriting Grafana dashboards from Flux to SQL. This is why you should migrate early (fewer dashboards = less rewriting).

### 11.2 Grafana Multi-Org → Custom React Dashboards (Do at Stage 3-4)

| Step | Action | Breaks What |
|------|--------|------------|
| 1 | Choose charting library (ECharts recommended) | Nothing (additive) |
| 2 | Build chart components in React (time-series, gauge, stat) | Nothing (new code) |
| 3 | Add API endpoints that return query results (from TimescaleDB) | Nothing (additive) |
| 4 | Replace iframe embeds with native chart components page by page | Frontend changes |
| 5 | Keep Grafana for admin-only analytics/debugging | Nothing removed |
| 6 | Remove Grafana embedding code, anonymous access config | Grafana config simplification |

### 11.3 EMQX → Azure IoT Hub (Do at Stage 4, if at all)

| Step | Action | Breaks What |
|------|--------|------------|
| 1 | Create IoT Hub, register devices | Nothing (parallel) |
| 2 | Update device firmware (new endpoint, auth, topics) | **All device firmware** |
| 3 | Set up Event Hubs consumer (replaces Telegraf MQTT sub) | **Telegraf pipeline** |
| 4 | Run both EMQX and IoT Hub during transition | Nothing (parallel) |
| 5 | Migrate devices in batches (update firmware) | Per-batch downtime |
| 6 | Decommission EMQX | EMQX infrastructure |

**Biggest cost:** Device firmware updates. Every deployed device needs new connection logic. This is a physical-world operation if devices are already installed at client sites.

---

## 12. Decision Framework

### Quick Reference: "Should I Change X?"

| Question | Answer |
|----------|--------|
| Should I replace EMQX? | **No** until 50K+ devices. Scale up, then cluster. |
| Should I add RabbitMQ? | **At Stage 3** — for command queuing and async jobs. |
| Should I add Kafka? | **At Stage 4** — when you have 3+ consumers for telemetry or need replay. |
| Should I add Flink? | **At Stage 4-5** — only for cross-device correlation, anomaly detection, or complex CEP. Most IoT platforms never need Flink. |
| Should I replace InfluxDB? | **Yes, at Stage 2-3 boundary.** Migrate to TimescaleDB before cardinality bites. |
| Should I use Azure IoT Hub? | **Not until Stage 4** — and only if device provisioning/twins justify the cost. |
| Should I use AWS IoT Core? | **No** — you're on Azure and IoT Core is expensive at continuous-telemetry volumes. |
| Should I replace Grafana? | **At Stage 3-4 boundary** — build custom dashboards when multi-org management is unbearable. |
| Should I switch to Kubernetes? | **At Stage 4** — when Container Apps scaling limits or multi-service orchestration needs exceed what Container Apps offers. |
| Should I switch clouds? | **No.** Stay on Azure. No compelling reason to switch. |

### The One Rule

**Don't introduce complexity to solve problems you don't have yet.**

Every component you add (Kafka, Flink, RabbitMQ, IoT Hub) adds operational overhead, monitoring requirements, failure modes, and cost. Only add them when you have concrete evidence that the current stack can't handle the load.

The progression is:
1. **Scale up** (bigger container)
2. **Optimize** (indexes, query tuning, caching, connection pooling)
3. **Scale out** (more replicas, clustering)
4. **Replace** (different technology) — last resort

---

*Companion documents: [`GRAFANA-ALERTING-STRATEGY.md`](./GRAFANA-ALERTING-STRATEGY.md), [`EMAIL-NOTIFICATION-STRATEGY.md`](./EMAIL-NOTIFICATION-STRATEGY.md)*
