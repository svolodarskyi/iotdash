# Alerting Beyond Grafana — Alternatives When You Outgrow Grafana

> **Version:** 0.1.0-draft
> **Date:** 2026-04-12
> **Context:** If/when Grafana multi-org is dropped in favour of custom dashboards, the alerting engine goes with it. This document maps every alternative.

---

## Table of Contents

1. [What Grafana Alerting Actually Does (So We Know What to Replace)](#1-what-grafana-alerting-actually-does)
2. [Option 1: Keep Grafana Headless (Drop UI, Keep Alerting)](#2-option-1-keep-grafana-headless)
3. [Option 2: Prometheus Alertmanager + Rule Evaluation](#3-option-2-prometheus-alertmanager--rule-evaluation)
4. [Option 3: Custom Alerting Engine (Build It Yourself)](#4-option-3-custom-alerting-engine)
5. [Option 4: Managed Alerting Services](#5-option-4-managed-alerting-services)
6. [Option 5: Open-Source Alerting Platforms](#6-option-5-open-source-alerting-platforms)
7. [Option 6: Database-Native Alerting](#7-option-6-database-native-alerting)
8. [Option 7: Stream Processing Alerting (Kafka/Flink)](#8-option-7-stream-processing-alerting)
9. [Comparison Matrix](#9-comparison-matrix)
10. [Recommendation by Stage](#10-recommendation-by-stage)

---

## 1. What Grafana Alerting Actually Does

Before replacing it, understand the 5 distinct jobs Grafana alerting performs:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Grafana Alerting Engine                       │
│                                                                 │
│  Job 1: SCHEDULING                                              │
│    Run alert rule evaluation every N seconds/minutes             │
│                                                                 │
│  Job 2: QUERYING                                                │
│    Execute a datasource query (Flux, PromQL, SQL, etc.)         │
│    against InfluxDB / TimescaleDB / Prometheus                  │
│                                                                 │
│  Job 3: EVALUATION                                              │
│    Apply condition logic: reduce to single value,               │
│    compare against threshold (>, <, within range, etc.)         │
│    Track state: Normal → Pending → Firing → Resolved            │
│                                                                 │
│  Job 4: ROUTING                                                 │
│    Match alert labels against notification policy tree           │
│    Decide which contact point receives the notification          │
│    Group related alerts, deduplicate, apply silences             │
│                                                                 │
│  Job 5: NOTIFICATION                                            │
│    Send to contact point (email, Slack, webhook, PagerDuty)     │
│    Handle resolved notifications                                │
│    Respect repeat intervals and mute timings                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

Any replacement must cover all 5 jobs. Some alternatives handle all 5. Others handle a subset and you compose the rest.

---

## 2. Option 1: Keep Grafana Headless (Drop UI, Keep Alerting)

**The simplest option.** Don't drop Grafana entirely — drop only the iframe embedding. Keep a Grafana instance running internally purely as an alerting engine.

```
                              ┌────────────────────┐
Custom React Frontend         │  Grafana (internal) │
  (no iframes, direct         │  ┌──────────────┐  │
   charts from TimescaleDB)   │  │  Alerting    │  │
        │                     │  │  Engine      │  │
        │                     │  │  (all 5 jobs)│  │
        │                     │  └──────┬───────┘  │
        │                     │         │ webhook  │
        │                     └─────────┼──────────┘
        │                               │
        ▼                               ▼
  Your FastAPI Backend ◀──── Receives webhook, sends email
        │
        ▼
   TimescaleDB
```

**What changes:**
- Grafana is no longer public-facing (internal ingress only)
- Grafana is no longer multi-org (single org, all alert rules live here)
- Frontend uses custom React charts instead of Grafana iframes
- Alert rules still managed via Grafana Provisioning API from your backend
- Grafana sends webhooks to your backend (not direct email)

**What stays the same:**
- Full Grafana alerting (scheduling, querying, evaluation, routing)
- Grafana Provisioning API for CRUD
- Grafana handles state management (pending, firing, resolved)

**Multi-tenancy without multi-org:**
Instead of one Grafana org per client, use **labels + folders**:
- Each alert rule gets labels: `org_id=acme`, `device_id=sensor01`
- Each org's rules live in a folder: `folder=org-acme`
- Notification policies route by `org_id` label
- Single datasource, queries filter by `device_id` tag

```
# Single notification policy tree handles all orgs:
root:
  receiver: backend-webhook
  group_by: [org_id, alertname]
  routes:
    - matchers: [org_id=acme]
      receiver: backend-webhook    # same webhook, backend routes by org label
    - matchers: [org_id=beta]
      receiver: backend-webhook
```

| Aspect | Assessment |
|--------|-----------|
| **Effort** | Low — minimal changes to existing alerting setup |
| **Handles** | Up to ~5,000 alert rules (same as current Grafana limits) |
| **Multi-tenancy** | Label-based (no more multi-org overhead) |
| **Dependencies** | Still need Grafana running (but internal only, lighter) |
| **Best for** | Stage 3-4 when you drop Grafana embedding but want to keep its alerting |

---

## 3. Option 2: Prometheus Alertmanager + Rule Evaluation

The Prometheus ecosystem has mature, production-proven alerting components. They work independently of Grafana.

### 3.1 Architecture

```
TimescaleDB / InfluxDB
        │
        │ scraped by or queried by
        ▼
┌─────────────────────┐
│  Rule Evaluator      │
│  (evaluates alert    │
│   rules on schedule) │
│                      │
│  Options:            │
│  - Prometheus server │
│  - Grafana Mimir     │
│    Ruler             │
│  - Thanos Ruler      │
│  - VictoriaMetrics   │
│    vmalert           │
└──────────┬──────────┘
           │ fires alerts
           ▼
┌─────────────────────┐
│  Alertmanager        │
│  (routing, grouping, │
│   dedup, silencing,  │
│   notification)      │
│                      │
│  - Prometheus        │
│    Alertmanager      │
│  - OR your backend   │
│    as webhook recv   │
└──────────┬──────────┘
           │ sends
           ▼
     Email / Slack / Webhook / PagerDuty
```

### 3.2 Component: Prometheus Alertmanager (Standalone)

Alertmanager handles **Jobs 4 and 5** (routing + notification). It is a standalone binary that receives alerts from any source and routes them.

**What it does:**
- Receives alerts via HTTP API (`POST /api/v2/alerts`)
- Routes alerts based on label matching (same tree model as Grafana)
- Groups related alerts into single notifications
- Deduplicates (same alert from multiple senders)
- Silences (temporary suppression)
- Inhibition (if alert A fires, suppress alert B)
- Sends to receivers: email, Slack, webhook, PagerDuty, OpsGenie, etc.
- Clusterable for HA (gossip protocol)

**What it does NOT do:**
- Does not evaluate alert rules (needs a separate evaluator)
- Does not query your database

**Configuration:**
```yaml
# alertmanager.yml
global:
  smtp_smarthost: 'smtp.sendgrid.net:587'
  smtp_from: 'alerts@yourdomain.com'
  smtp_auth_username: 'apikey'
  smtp_auth_password: 'SG.xxxxx'

route:
  receiver: 'default'
  group_by: ['org_id', 'alertname']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  routes:
    - match:
        severity: critical
      receiver: 'critical-email'
    - match_re:
        org_id: '.*'
      receiver: 'org-webhook'

receivers:
  - name: 'default'
    email_configs:
      - to: 'admin@yourdomain.com'

  - name: 'critical-email'
    email_configs:
      - to: 'admin@yourdomain.com'
        send_resolved: true

  - name: 'org-webhook'
    webhook_configs:
      - url: 'http://backend:8000/api/internal/alerts/webhook'
        send_resolved: true
```

**How your backend feeds it:**
```python
import httpx

async def fire_alert(alertmanager_url, alert):
    """Send alert to Alertmanager."""
    await httpx.post(f"{alertmanager_url}/api/v2/alerts", json=[
        {
            "labels": {
                "alertname": f"{alert.metric}_{alert.condition}_{alert.device_code}",
                "org_id": alert.org_id,
                "device_id": alert.device_code,
                "metric": alert.metric,
                "severity": "warning",
            },
            "annotations": {
                "summary": f"{alert.metric} is {alert.condition} {alert.threshold} on {alert.device_code}",
                "value": str(current_value),
            },
            "startsAt": datetime.utcnow().isoformat() + "Z",
        }
    ])
```

### 3.3 Component: Rule Evaluator Options

Something needs to do **Jobs 1, 2, 3** (scheduling, querying, evaluation). Options:

**A. Prometheus Server (if you have PromQL-compatible metrics)**
```
Prometheus scrapes metrics → evaluates recording/alerting rules → fires to Alertmanager
```
- Only works with PromQL. Your data is in InfluxDB/TimescaleDB, not Prometheus.
- You'd need a metrics exporter or remote-write adapter.
- Overkill if you don't already run Prometheus.

**B. Grafana Mimir Ruler**
```
Mimir Ruler evaluates PromQL rules against Mimir long-term storage
```
- Only works with PromQL against Mimir/Cortex datasources.
- Not applicable to InfluxDB/TimescaleDB.

**C. VictoriaMetrics vmalert**
```
vmalert queries VictoriaMetrics (or any PromQL-compatible) → fires to Alertmanager
```
- Lightweight alternative to Prometheus for rule evaluation.
- Still requires PromQL-compatible datasource.

**D. Your own evaluator (if using TimescaleDB/InfluxDB)**

This is the most common path when your data lives in a SQL database, not Prometheus:

```python
# Custom alert evaluator — runs as background worker in your FastAPI app

async def alert_evaluator_loop():
    """Runs every 60 seconds. Evaluates all enabled alerts."""
    while True:
        alerts = await db.fetch_all(
            "SELECT * FROM alerts WHERE is_enabled = true"
        )

        for alert in alerts:
            current_value = await query_current_value(
                device_code=alert.device_code,
                metric=alert.metric,
            )

            if current_value is None:
                await update_alert_state(alert.id, "no_data")
                continue

            condition_met = evaluate_condition(
                value=current_value,
                condition=alert.condition,    # "above" / "below"
                threshold=alert.threshold,
            )

            previous_state = alert.current_state  # "normal", "pending", "firing"
            new_state = compute_new_state(
                condition_met=condition_met,
                previous_state=previous_state,
                pending_since=alert.pending_since,
                for_duration=alert.duration_seconds,
            )

            if new_state != previous_state:
                await update_alert_state(alert.id, new_state)

                if new_state == "firing":
                    await fire_alert_to_alertmanager(alert, current_value)
                elif new_state == "normal" and previous_state == "firing":
                    await resolve_alert_in_alertmanager(alert)

        await asyncio.sleep(60)  # evaluation interval


async def query_current_value(device_code: str, metric: str) -> float | None:
    """Query TimescaleDB for the latest metric value."""
    row = await db.fetch_one(
        """
        SELECT value FROM telemetry
        WHERE device_id = :device_code
          AND metric = :metric
          AND time > now() - interval '10 minutes'
        ORDER BY time DESC
        LIMIT 1
        """,
        {"device_code": device_code, "metric": metric}
    )
    return row["value"] if row else None


def evaluate_condition(value, condition, threshold) -> bool:
    if condition == "above":
        return value > threshold
    elif condition == "below":
        return value < threshold
    return False


def compute_new_state(condition_met, previous_state, pending_since, for_duration) -> str:
    if condition_met:
        if previous_state == "normal":
            return "pending"  # start the "for" timer
        elif previous_state == "pending":
            elapsed = (datetime.utcnow() - pending_since).total_seconds()
            if elapsed >= for_duration:
                return "firing"
            return "pending"  # still waiting
        else:
            return "firing"  # still firing
    else:
        return "normal"  # condition no longer met
```

| Aspect | Assessment |
|--------|-----------|
| **Effort** | Medium (Alertmanager is off-the-shelf; evaluator is ~200 lines) |
| **Handles** | Alertmanager: tens of thousands of alerts. Evaluator: depends on query speed, ~1000-5000 rules at 1-min intervals. |
| **Multi-tenancy** | Label-based routing in Alertmanager, org_id filtering in evaluator |
| **Dependencies** | Alertmanager (single binary, Docker image: `prom/alertmanager`) + your evaluator code |
| **Best for** | Stage 4 when Grafana is fully replaced with custom dashboards |

---

## 4. Option 3: Custom Alerting Engine (Build It Yourself)

Full control. No external alerting dependencies. Everything in your FastAPI app.

### 4.1 Architecture

```
┌──────────────────────────────────────────────────────┐
│                  Your FastAPI Application              │
│                                                      │
│  ┌──────────────┐    ┌──────────────┐               │
│  │  Alert       │    │  State       │               │
│  │  Evaluator   │───▶│  Manager     │               │
│  │  (scheduler) │    │  (normal →   │               │
│  │              │    │   pending →  │               │
│  │  Queries     │    │   firing)    │               │
│  │  TimescaleDB │    └──────┬───────┘               │
│  └──────────────┘           │                        │
│                             │ state change           │
│                             ▼                        │
│                    ┌──────────────────┐              │
│                    │  Notification    │              │
│                    │  Dispatcher      │              │
│                    │                  │              │
│                    │  - Dedup         │              │
│                    │  - Rate limit    │              │
│                    │  - Grouping      │              │
│                    │  - Queue to DB   │              │
│                    └──────┬───────────┘              │
│                           │                          │
│                    ┌──────▼───────────┐              │
│                    │  Email Worker    │              │
│                    │  (sends via API) │              │
│                    └─────────────────┘              │
│                                                      │
│  All state in PostgreSQL:                            │
│    - alerts table (config)                           │
│    - alert_states table (current state per rule)     │
│    - alert_history table (state transitions)         │
│    - email_queue table (pending emails)              │
│    - suppression_list table (bounced addresses)      │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 4.2 Additional Database Tables

```sql
-- Current state of each alert (updated by evaluator)
CREATE TABLE alert_states (
    alert_id        UUID PRIMARY KEY REFERENCES alerts(id),
    current_state   VARCHAR(20) DEFAULT 'normal',  -- normal, pending, firing, no_data, error
    pending_since   TIMESTAMPTZ,
    firing_since    TIMESTAMPTZ,
    last_value      DOUBLE PRECISION,
    last_evaluated  TIMESTAMPTZ,
    last_notified   TIMESTAMPTZ,
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- History of state transitions (for audit, debugging, UI)
CREATE TABLE alert_history (
    id              BIGSERIAL PRIMARY KEY,
    alert_id        UUID NOT NULL REFERENCES alerts(id),
    from_state      VARCHAR(20),
    to_state        VARCHAR(20) NOT NULL,
    value           DOUBLE PRECISION,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_alert_history_alert_time
  ON alert_history (alert_id, created_at DESC);
```

### 4.3 What You Gain vs Grafana

| Capability | Grafana Alerting | Custom Engine |
|-----------|-----------------|---------------|
| Threshold alerts (>, <) | Yes | Yes (trivial) |
| "For" duration (pending period) | Yes | Yes (state machine) |
| No-data handling | Yes | Yes (configurable) |
| Multi-tenant isolation | Multi-org (complex) | org_id filter (simple) |
| Alert state history | Limited (annotations) | Full audit table |
| Custom alert logic | No (threshold + reduce only) | **Anything you can code** |
| Rate of change alerts | No | `WHERE value - lag(value) > X` |
| Cross-device correlation | No | `GROUP BY org_id HAVING count(*) > 3` |
| Anomaly detection | No | Rolling stddev, ML models |
| User-facing alert status API | Must proxy Grafana API | Native API endpoint |
| Notification customisation | Go templates (limited) | Full HTML, branded, per-org |
| Dependency on external service | Yes (Grafana must be running) | **None** |

### 4.4 What You Lose vs Grafana

| Capability | Impact | Mitigation |
|-----------|--------|-----------|
| Battle-tested evaluation engine | Must test your own thoroughly | Comprehensive test suite |
| Alertmanager-quality routing | Must implement grouping, dedup, silences | Use Alertmanager alongside, or implement basic versions |
| Grafana alerting UI (rule viewer, state viewer) | Must build alert management UI in React | Part of your admin panel |
| PromQL/Flux expression language | Your evaluator uses SQL only | SQL is more readable anyway |
| Community plugins and integrations | Limited to what you build | Webhook output covers most cases |

| Aspect | Assessment |
|--------|-----------|
| **Effort** | Medium-large (~1-2 weeks for solid implementation) |
| **Handles** | Depends on TimescaleDB query speed. ~5,000-10,000 rules at 1-min intervals with batched queries. |
| **Multi-tenancy** | Native (org_id filter in SQL) |
| **Dependencies** | None beyond your existing stack (FastAPI + PostgreSQL/TimescaleDB) |
| **Best for** | Stage 4+ when you want zero Grafana dependency and need custom alert logic |

---

## 5. Option 4: Managed Alerting Services

Cloud-native alerting that you don't host or maintain.

### 5.1 Azure Monitor Alerts

```
TimescaleDB / InfluxDB
        │
        │ (metrics exported via Azure Monitor custom metrics API
        │  or Log Analytics workspace)
        ▼
Azure Monitor
        │
        ├─▶ Metric Alerts (threshold on numeric value)
        ├─▶ Log Alerts (KQL query on Log Analytics)
        └─▶ Action Groups (email, SMS, webhook, Azure Function, Logic App)
```

| Aspect | Details |
|--------|---------|
| **Pricing** | Metric alerts: ~$0.10/alert rule/month. Log alerts: ~$0.50-1.50/rule/month (depending on frequency). |
| **Strengths** | Zero infrastructure, Azure-native, integrates with Action Groups (email, SMS, webhook, ITSM). |
| **Weaknesses** | Must export your data to Azure Monitor or Log Analytics first. KQL learning curve. Not designed for per-tenant alerting at IoT scale. Alert rule limits (~100-5000 per subscription depending on type). |
| **Multi-tenancy** | Not built for per-client alerting. You'd need one alert rule per device per metric — hits limits fast. |
| **Verdict** | Good for infrastructure monitoring (is my container healthy?). **Not suitable for per-device IoT alerting at scale.** |

### 5.2 AWS CloudWatch Alarms

| Aspect | Details |
|--------|---------|
| **Pricing** | Standard: $0.10/alarm/month. High-res: $0.30/alarm/month. |
| **Strengths** | Zero infrastructure, AWS-native, SNS integration (email, SMS, Lambda). |
| **Weaknesses** | Same as Azure Monitor — must export metrics to CloudWatch. Per-alarm pricing adds up fast. 5,000 alarms per region limit. |
| **Multi-tenancy** | Same problem — one alarm per device per metric. 1,000 devices × 2 metrics = 2,000 alarms = $200/month in alarm costs alone. |
| **Verdict** | Same: good for infra monitoring, **not for per-device IoT alerting.** |

### 5.3 PagerDuty / OpsGenie / Incident.io

These are **incident management** platforms, not alert evaluation engines. They receive alerts from other systems and manage the human response (escalation, on-call routing, war rooms).

```
Your alerting engine (Grafana / Custom / Alertmanager)
        │
        │ fires alert
        ▼
PagerDuty / OpsGenie
        │
        ├─▶ Escalation policies
        ├─▶ On-call scheduling
        ├─▶ Incident tracking
        └─▶ Notification (push, SMS, phone call)
```

| Aspect | Details |
|--------|---------|
| **Pricing** | PagerDuty: from $21/user/month. OpsGenie: from $9/user/month. |
| **Use case** | Your internal ops team (not your clients). When your platform is down and you need to wake up the engineer on call. |
| **Verdict** | **Not a replacement for Grafana alerting.** Complementary — use it for your own incident management. |

### 5.4 Datadog / New Relic

Full-stack observability platforms with built-in alerting.

| Aspect | Datadog | New Relic |
|--------|---------|-----------|
| **Pricing** | Infrastructure: $15/host/month. Custom metrics: $0.05/metric/month. | Free tier: 100GB/month. Pro: $0.30/GB ingested. |
| **Alerting** | Powerful (threshold, anomaly, composite, forecast). | Powerful (NRQL query-based alerts). |
| **IoT scale** | Gets expensive fast. 10,000 custom metrics = $500/month just for metrics, plus alert costs. | Cheaper on ingestion, but custom alert logic is limited. |
| **Multi-tenancy** | Not designed for per-client tenant isolation. | Not designed for per-client tenant isolation. |
| **Verdict** | Excellent for monitoring your platform's health. **Too expensive and not designed for per-device per-client IoT alerting.** |

**Summary of managed services:**

All managed alerting services (Azure Monitor, CloudWatch, Datadog, New Relic) share the same fundamental mismatch: they are designed for **infrastructure and application monitoring**, not for **per-tenant IoT device alerting**. They charge per-alarm or per-metric, which scales linearly with device count. At IoT scale, the cost is prohibitive.

---

## 6. Option 5: Open-Source Alerting Platforms

### 6.1 Zabbix

```
Zabbix Server (monitors, evaluates triggers, sends notifications)
        ▲
        │ Zabbix Agent / Trapper / API
        │
Your data (pushed via Zabbix Sender or Trapper API)
```

| Aspect | Details |
|--------|---------|
| **What it is** | Full monitoring + alerting platform (like Nagios on steroids). |
| **Alerting** | Trigger-based: define conditions on items (metrics). Supports dependencies, escalations, maintenance windows. |
| **Scale** | Handles 100K+ metrics on a single server. Designed for network/server monitoring at scale. |
| **Multi-tenancy** | User groups + host groups provide isolation. Not true multi-org. |
| **API** | Full JSON-RPC API for managing triggers, actions, hosts programmatically. |
| **Notification** | Email, Slack, webhook, SMS, custom scripts. |
| **Weakness** | Heavy (Java/PHP/C, needs its own database). Complex to operate. UI is dated. Not designed for IoT telemetry — designed for infrastructure. |
| **Verdict** | Possible but a poor fit. You'd be bending an infrastructure monitoring tool into an IoT alerting engine. |

### 6.2 Kapacitor (InfluxData)

```
InfluxDB ──stream/batch──▶ Kapacitor ──alert──▶ Handlers (email, Slack, webhook)
```

| Aspect | Details |
|--------|---------|
| **What it is** | Native alerting and stream processing engine for InfluxDB (part of the TICK stack). |
| **Alerting** | TICKscript language: threshold, relative, deadman, anomaly detection. |
| **Scale** | Good for InfluxDB-native workloads. Handles thousands of alert rules. |
| **Multi-tenancy** | Not built-in. Must structure TICKscripts with tag-based filtering. |
| **API** | HTTP API for managing tasks (alert rules). |
| **Weakness** | TICKscript is a niche language. Kapacitor development has slowed (InfluxData focusing on InfluxDB 3.x/Cloud). If you migrate to TimescaleDB, Kapacitor can't query it. |
| **Verdict** | Only viable if you stay on InfluxDB forever. Since the recommendation is to migrate to TimescaleDB, Kapacitor is a dead end. |

### 6.3 Keep (open-source alert management)

```
Alert sources (Grafana, Prometheus, Datadog, custom)
        │
        │ webhook / API
        ▼
Keep (correlates, deduplicates, enriches)
        │
        ▼
Notification channels (email, Slack, PagerDuty)
```

| Aspect | Details |
|--------|---------|
| **What it is** | Open-source alert management platform. Aggregates alerts from multiple sources. |
| **What it does** | Alert correlation, deduplication, enrichment, workflow automation. |
| **What it does NOT do** | Does not evaluate alert rules or query your database. Needs an external source of alerts. |
| **Verdict** | Useful as a layer on top of your custom evaluator or Alertmanager. Not a standalone replacement for Grafana alerting. |

### 6.4 SigNoz

```
Your app ──OTLP──▶ SigNoz (traces, metrics, logs, alerts)
```

| Aspect | Details |
|--------|---------|
| **What it is** | Open-source observability platform (Datadog alternative). Uses ClickHouse for storage. |
| **Alerting** | PromQL-based alert rules with notification channels. |
| **Scale** | Good (ClickHouse handles high cardinality). |
| **Multi-tenancy** | Not built-in (single-tenant). |
| **Weakness** | Another full observability platform to operate. You'd need to ingest your IoT data into SigNoz (via OpenTelemetry). Adds significant infrastructure. |
| **Verdict** | Good if you want a Grafana replacement for both dashboards and alerting. Heavy to operate. Not purpose-built for IoT. |

---

## 7. Option 6: Database-Native Alerting

If your data is in TimescaleDB (PostgreSQL), you can use PostgreSQL features for alerting.

### 7.1 pg_cron + Custom SQL Evaluator

```sql
-- Install pg_cron extension
CREATE EXTENSION pg_cron;

-- Schedule alert evaluation every 60 seconds
SELECT cron.schedule(
    'evaluate-alerts',
    '* * * * *',     -- every minute
    $$
    SELECT evaluate_alerts();
    $$
);
```

```sql
-- Alert evaluation function (runs inside PostgreSQL)
CREATE OR REPLACE FUNCTION evaluate_alerts() RETURNS void AS $$
DECLARE
    alert RECORD;
    current_val DOUBLE PRECISION;
    condition_met BOOLEAN;
BEGIN
    FOR alert IN
        SELECT a.*, d.device_code, s.current_state, s.pending_since
        FROM alerts a
        JOIN devices d ON a.device_id = d.id
        LEFT JOIN alert_states s ON a.id = s.alert_id
        WHERE a.is_enabled = true
    LOOP
        -- Get latest value from telemetry hypertable
        SELECT value INTO current_val
        FROM telemetry
        WHERE device_id = alert.device_code
          AND metric = alert.metric
          AND time > now() - interval '10 minutes'
        ORDER BY time DESC
        LIMIT 1;

        -- Evaluate condition
        condition_met := CASE alert.condition
            WHEN 'above' THEN current_val > alert.threshold
            WHEN 'below' THEN current_val < alert.threshold
            ELSE false
        END;

        -- Update state + queue notification via pg_notify
        IF condition_met AND alert.current_state = 'normal' THEN
            UPDATE alert_states SET current_state = 'pending', pending_since = now()
            WHERE alert_id = alert.id;
        ELSIF condition_met AND alert.current_state = 'pending'
              AND (now() - alert.pending_since) > (alert.duration_seconds * interval '1 second') THEN
            UPDATE alert_states SET current_state = 'firing', firing_since = now()
            WHERE alert_id = alert.id;
            -- Notify the backend to send email
            PERFORM pg_notify('alert_fired', json_build_object(
                'alert_id', alert.id,
                'device_code', alert.device_code,
                'metric', alert.metric,
                'value', current_val,
                'threshold', alert.threshold
            )::text);
        ELSIF NOT condition_met AND alert.current_state IN ('pending', 'firing') THEN
            UPDATE alert_states SET current_state = 'normal', pending_since = NULL
            WHERE alert_id = alert.id;
            IF alert.current_state = 'firing' THEN
                PERFORM pg_notify('alert_resolved', json_build_object(
                    'alert_id', alert.id
                )::text);
            END IF;
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;
```

**Backend listens for notifications:**
```python
import asyncpg

async def listen_for_alerts():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.add_listener('alert_fired', handle_alert_fired)
    await conn.add_listener('alert_resolved', handle_alert_resolved)

async def handle_alert_fired(conn, pid, channel, payload):
    data = json.loads(payload)
    # Enqueue email notification
    await enqueue_alert_email(data['alert_id'], data['value'])
```

| Aspect | Assessment |
|--------|-----------|
| **Effort** | Low-medium (~1 day for basic implementation) |
| **Dependencies** | pg_cron extension (available on Azure Flexible Server) |
| **Handles** | ~1,000-5,000 alert rules (limited by PostgreSQL function execution time) |
| **Advantage** | Zero external services. Alert evaluation is a database operation. Data locality — no network hops between evaluator and data. |
| **Weakness** | Complex alert logic is hard to express in PL/pgSQL. No built-in routing/grouping/silencing. |
| **Best for** | Simple threshold alerts when data is already in TimescaleDB |

### 7.2 TimescaleDB Continuous Aggregates + pg_cron

For more complex conditions (rate of change, rolling averages):

```sql
-- Continuous aggregate: 5-minute average temperature per device
CREATE MATERIALIZED VIEW device_5m_avg
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('5 minutes', time) AS bucket,
    device_id,
    avg(value) as avg_value,
    max(value) as max_value,
    min(value) as min_value,
    stddev(value) as stddev_value
FROM telemetry
WHERE metric = 'temperature'
GROUP BY bucket, device_id;

-- Alert: temperature rising more than 5°C in 10 minutes
SELECT device_id, max_value - min_value as delta
FROM device_5m_avg
WHERE bucket > now() - interval '10 minutes'
GROUP BY device_id
HAVING max(max_value) - min(min_value) > 5;
```

---

## 8. Option 7: Stream Processing Alerting (Kafka/Flink)

When alerts are evaluated on the stream as data arrives, not by polling the database.

### 8.1 Architecture

```
EMQX ──bridge──▶ Kafka / Event Hubs
                        │
                        ▼
                  Flink / Stream Analytics
                  ┌──────────────────────┐
                  │ CEP (Complex Event   │
                  │ Processing):         │
                  │                      │
                  │ - Threshold alerts   │
                  │ - Rate of change     │
                  │ - Cross-device       │
                  │   correlation        │
                  │ - Anomaly detection  │
                  │ - Windowed aggs      │
                  │ - Pattern matching   │
                  └──────────┬───────────┘
                             │
                             ▼
                      Alertmanager / Your Backend
                             │
                             ▼
                        Email / Slack
```

### 8.2 Flink CEP Example

```java
// Flink CEP: Alert if temperature > 30 for 3 consecutive readings
Pattern<TelemetryEvent, ?> highTempPattern = Pattern
    .<TelemetryEvent>begin("first")
    .where(event -> event.getMetric().equals("temperature")
                 && event.getValue() > 30.0)
    .next("second")
    .where(event -> event.getMetric().equals("temperature")
                 && event.getValue() > 30.0)
    .next("third")
    .where(event -> event.getMetric().equals("temperature")
                 && event.getValue() > 30.0)
    .within(Time.minutes(5));

PatternStream<TelemetryEvent> patternStream = CEP.pattern(
    telemetryStream.keyBy(TelemetryEvent::getDeviceId),
    highTempPattern
);

patternStream.select(matchedEvents -> {
    // Fire alert to Alertmanager
    return new Alert(
        matchedEvents.get("first").get(0).getDeviceId(),
        "temperature_sustained_high",
        matchedEvents.get("third").get(0).getValue()
    );
}).addSink(alertmanagerSink);
```

### 8.3 Azure Stream Analytics Example (SQL-like)

```sql
-- Alert: temperature above 30 for more than 5 minutes
SELECT
    deviceId,
    AVG(temperature) as avgTemp,
    System.Timestamp() as alertTime
INTO AlertOutput
FROM IoTInput TIMESTAMP BY eventTime
GROUP BY
    deviceId,
    TumblingWindow(minute, 5)
HAVING AVG(temperature) > 30

-- Alert: >3 error messages from same device in 1 minute
SELECT
    deviceId,
    COUNT(*) as errorCount,
    System.Timestamp() as alertTime
INTO AlertOutput
FROM IoTInput TIMESTAMP BY eventTime
WHERE messageType = 'error'
GROUP BY
    deviceId,
    SlidingWindow(minute, 1)
HAVING COUNT(*) > 3

-- Alert: cross-device — >5 devices in same org offline simultaneously
SELECT
    orgId,
    COUNT(DISTINCT deviceId) as offlineCount,
    System.Timestamp() as alertTime
INTO AlertOutput
FROM DeviceStatusInput TIMESTAMP BY eventTime
WHERE status = 'offline'
GROUP BY
    orgId,
    TumblingWindow(minute, 2)
HAVING COUNT(DISTINCT deviceId) > 5
```

| Aspect | Assessment |
|--------|-----------|
| **Effort** | Large (requires Kafka + Flink/ASA infrastructure) |
| **Handles** | Millions of events/sec. Unlimited alert complexity. |
| **Latency** | Sub-second (alerts fire as data arrives, not on a polling schedule) |
| **Cost** | Kafka + Flink: $200-500+/mo minimum |
| **Best for** | Stage 4-5. When you need real-time cross-device correlation, anomaly detection, or millisecond alert latency. |
| **Overkill for** | Simple threshold alerting on < 10,000 devices |

---

## 9. Comparison Matrix

| Option | Jobs Covered | Effort | Max Rules | Multi-Tenant | External Deps | Best Stage |
|--------|-------------|--------|-----------|-------------|---------------|-----------|
| **1. Grafana Headless** | All 5 | Low | ~5,000 | Label-based | Grafana (internal) | 3-4 |
| **2. Alertmanager + Custom Evaluator** | All 5 (split) | Medium | ~5,000-10,000 | Label-based routing | Alertmanager binary | 4 |
| **3. Custom Engine (full)** | All 5 | Medium-Large | ~5,000-10,000 | Native (SQL filter) | None | 4+ |
| **4. Azure Monitor / CloudWatch** | All 5 | Low | ~5,000 (per-sub limit) | Not designed for it | Cloud service | Infra monitoring only |
| **5. SigNoz / Zabbix** | All 5 | Large | Varies | Limited | Full platform to operate | Not recommended |
| **6. DB-Native (pg_cron)** | 1,2,3 (need 4,5 separately) | Low | ~1,000-5,000 | Native (SQL) | pg_cron extension | 3-4 (simple alerts) |
| **7. Kafka + Flink/ASA** | 1,2,3 (need 4,5 separately) | Very Large | Unlimited | Partition-based | Kafka + Flink | 5+ |

---

## 10. Recommendation by Stage

### Stage 3 (50-200 orgs, dropping Grafana embedding)

**Recommended: Option 1 (Grafana Headless) + Option 6 (pg_cron) for simple alerts**

```
                    ┌─────────────────┐
                    │ Grafana          │ (internal only, no public access)
                    │ Single-org       │
                    │ Alert rules via  │
                    │ Provisioning API │
                    │                  │──webhook──▶ Your Backend ──▶ Email
                    └─────────────────┘
```

Why: Minimum disruption. Grafana keeps doing what it's good at (alerting). You just stop using it for dashboards.

### Stage 4 (200+ orgs, Grafana fully removed)

**Recommended: Option 3 (Custom Engine) or Option 2 (Alertmanager + Custom Evaluator)**

If you want simplicity (no extra services):
```
FastAPI Background Worker (evaluator)
    → queries TimescaleDB every 60s
    → manages state in PostgreSQL
    → enqueues emails to email_queue table
    → Email Worker sends via SES/SendGrid
```

If you want battle-tested notification routing:
```
FastAPI Background Worker (evaluator)
    → queries TimescaleDB every 60s
    → fires alerts to Prometheus Alertmanager
    → Alertmanager handles grouping, dedup, silencing, routing
    → Alertmanager sends webhook to your backend or direct email
```

### Stage 5 (10,000+ devices, complex alert logic needed)

**Recommended: Option 7 (Kafka + Stream Processing) for real-time + Option 3 (Custom Engine) for user-configured threshold alerts**

```
EMQX ──▶ Kafka ──▶ Flink/ASA (real-time CEP: anomaly detection, cross-device)
                        │
                        ▼
                   Alertmanager
                        │
                        ▼
                   Your Backend ──▶ Email

Simultaneously:

User-configured simple alerts (threshold > X):
  FastAPI Worker ──▶ TimescaleDB query ──▶ State machine ──▶ Email queue
```

Two systems coexist: stream-based for complex platform-level alerting, poll-based for user-configured simple alerts.

---

### Summary: The Recommended Path

```
Today (Stage 1-2):
  Grafana Alerting (full, multi-org, as described in GRAFANA-ALERTING-STRATEGY.md)

Stage 3 (drop Grafana embedding, keep alerting):
  Grafana Headless (internal only, single-org, label-based tenancy)

Stage 4 (drop Grafana entirely):
  Custom Evaluator (FastAPI worker + TimescaleDB)
  + Prometheus Alertmanager (routing, grouping, dedup)
  + Email queue (PostgreSQL-based)

Stage 5 (complex real-time alerting):
  Add Kafka + Flink/Azure Stream Analytics for CEP
  Keep custom evaluator for user-configured simple threshold alerts
```

Each transition is incremental. You never need to rebuild alerting from scratch — you migrate one job at a time.

---

*Companion documents: [`GRAFANA-ALERTING-STRATEGY.md`](./GRAFANA-ALERTING-STRATEGY.md), [`EMAIL-NOTIFICATION-STRATEGY.md`](./EMAIL-NOTIFICATION-STRATEGY.md), [`SCALING-STRATEGY.md`](./SCALING-STRATEGY.md)*
