# Grafana Alerting Strategy — Multi-Org IoT Platform

> **Version:** 0.1.0-draft
> **Date:** 2026-04-12
> **Context:** How to implement, manage, and scale alerts via Grafana for a multi-tenant IoT platform

---

## Table of Contents

1. [How Grafana Alerting Works](#1-how-grafana-alerting-works)
2. [Setting Alerts via API](#2-setting-alerts-via-api)
3. [Multi-Org Alert Architecture](#3-multi-org-alert-architecture)
4. [Our Platform's Alert Flow](#4-our-platforms-alert-flow)
5. [Scaling Grafana Alerting](#5-scaling-grafana-alerting)
6. [When to Move Beyond Grafana Alerting](#6-when-to-move-beyond-grafana-alerting)

---

## 1. How Grafana Alerting Works

Grafana has a **Unified Alerting** system (introduced in v8, default since v9, mature in v11). It replaces the legacy dashboard-based alerting with a standalone alerting engine.

### 1.1 Core Concepts

```
┌──────────────────────────────────────────────────────────────┐
│                   Grafana Alerting Engine                      │
│                                                              │
│  ┌──────────────┐    ┌───────────────┐    ┌──────────────┐  │
│  │  Alert Rules  │───▶│  Evaluation   │───▶│   State      │  │
│  │  (what to     │    │  Engine       │    │   Manager    │  │
│  │   check)      │    │  (runs every  │    │  (normal,    │  │
│  │               │    │   interval)   │    │   pending,   │  │
│  └──────────────┘    └───────────────┘    │   firing)    │  │
│                                           └──────┬───────┘  │
│                                                  │           │
│  ┌──────────────────────────────────────────────▼────────┐  │
│  │              Notification Pipeline                     │  │
│  │                                                        │  │
│  │  ┌─────────────────┐   ┌────────────────┐             │  │
│  │  │ Notification     │──▶│ Contact Points │             │  │
│  │  │ Policies         │   │ (where to send)│             │  │
│  │  │ (routing rules)  │   │                │             │  │
│  │  └─────────────────┘   └────────────────┘             │  │
│  │                                                        │  │
│  │  ┌─────────────────┐   ┌────────────────┐             │  │
│  │  │ Silences         │   │ Mute Timings   │             │  │
│  │  │ (temp suppress)  │   │ (recurring     │             │  │
│  │  │                  │   │  windows)      │             │  │
│  │  └─────────────────┘   └────────────────┘             │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

**Alert Rule:**
- A query + condition that Grafana evaluates on a schedule
- Contains: datasource query (e.g., Flux query to InfluxDB), a condition expression (e.g., "last value > 30"), evaluation interval, "for" duration (how long condition must be true before firing)
- Lives in a **folder** and **rule group** (grouping is organizational + affects evaluation)
- Each rule group is evaluated sequentially; different groups evaluate in parallel

**Contact Point:**
- A destination for notifications: email, Slack, webhook, PagerDuty, etc.
- One contact point can have multiple integrations (e.g., send to both email AND Slack)
- Each integration has its own settings (SMTP server for email, webhook URL for Slack, etc.)

**Notification Policy:**
- Routing rules that decide which contact point receives which alert
- Tree structure: a root policy (catch-all) with child policies that match on labels
- Example: alerts with label `severity=critical` → PagerDuty; everything else → email
- Controls: grouping (batch related alerts), repeat interval, group wait/interval

**Silence:**
- Temporary suppression of notifications matching certain label matchers
- Has start/end time. Used during maintenance windows.

**Mute Timing:**
- Recurring time windows when notifications are suppressed (e.g., "don't notify on weekends")
- Reusable across notification policies

### 1.2 Alert Rule Structure

An alert rule consists of:

```
Alert Rule
├── Name: "High Temperature - sensor01"
├── Folder: "org-acme-alerts"
├── Rule Group: "device-alerts"
├── Evaluation interval: 1m (how often to check)
├── Pending period ("for"): 5m (must be true for 5 min before firing)
├── Queries and conditions:
│   ├── Query A: (Flux query to InfluxDB)
│   │   from(bucket: "iot")
│   │     |> range(start: -10m)
│   │     |> filter(fn: (r) => r.device_id == "sensor01")
│   │     |> filter(fn: (r) => r._field == "temperature")
│   │     |> last()
│   ├── Expression B: Reduce (last value of A)
│   └── Expression C: Threshold (B > 30)  ← this is the condition
├── Labels:
│   ├── org: "acme"
│   ├── device_id: "sensor01"
│   ├── metric: "temperature"
│   └── severity: "warning"
└── Annotations:
    ├── summary: "Temperature on sensor01 exceeded 30°C"
    └── description: "Current value: {{ $value }}"
```

### 1.3 Evaluation Model

```
Every evaluation interval (e.g., 1 minute):
  1. Execute query A against InfluxDB → get latest temperature value
  2. Run expression B (reduce) → single number
  3. Run expression C (threshold) → true/false
  4. If true:
     - If state was Normal → transition to Pending
     - If state was Pending and "for" duration elapsed → transition to Firing → send notification
  5. If false:
     - If state was Firing → transition to Resolved → send resolution notification
     - If state was Pending → transition back to Normal (no notification)
```

**States:**
| State | Meaning |
|-------|---------|
| Normal | Condition not met |
| Pending | Condition met, waiting for "for" duration to elapse |
| Firing | Condition met for long enough, notification sent |
| No Data | Query returned no data (configurable: treat as alerting, OK, or no data) |
| Error | Query failed (configurable: treat as alerting or error) |

---

## 2. Setting Alerts via API

**Yes, Grafana has a full HTTP API for managing alerts programmatically.** This is exactly what our backend will use.

### 2.1 API Authentication

All API calls require a Grafana **service account token** with admin privileges:

```
Header: Authorization: Bearer <service-account-token>
```

For multi-org, include:
```
Header: X-Grafana-Org-Id: <org_id>
```

This scopes the API call to a specific organization.

### 2.2 Alert Rules API

**Create Alert Rule:**
```
POST /api/v1/provisioning/alert-rules
```

**Request Body:**
```json
{
  "title": "High Temperature - sensor01",
  "ruleGroup": "device-alerts",
  "folderUID": "org-acme-alerts",
  "condition": "C",
  "for": "5m",
  "noDataState": "NoData",
  "execErrState": "Error",
  "labels": {
    "org": "acme",
    "device_id": "sensor01",
    "severity": "warning"
  },
  "annotations": {
    "summary": "Temperature exceeded threshold on sensor01",
    "description": "Temperature is {{ $value }} which is above 30°C"
  },
  "data": [
    {
      "refId": "A",
      "relativeTimeRange": { "from": 600, "to": 0 },
      "datasourceUid": "influxdb-uid",
      "model": {
        "query": "from(bucket: \"iot\") |> range(start: -10m) |> filter(fn: (r) => r.device_id == \"sensor01\") |> filter(fn: (r) => r.message_type == \"message\") |> filter(fn: (r) => r._field == \"temperature\") |> last()",
        "intervalMs": 1000,
        "maxDataPoints": 43200
      }
    },
    {
      "refId": "B",
      "relativeTimeRange": { "from": 600, "to": 0 },
      "datasourceUid": "__expr__",
      "model": {
        "type": "reduce",
        "expression": "A",
        "reducer": "last",
        "settings": { "mode": "dropNN" }
      }
    },
    {
      "refId": "C",
      "relativeTimeRange": { "from": 600, "to": 0 },
      "datasourceUid": "__expr__",
      "model": {
        "type": "threshold",
        "expression": "B",
        "conditions": [
          {
            "evaluator": { "type": "gt", "params": [30] },
            "operator": { "type": "and" },
            "reducer": { "type": "last" }
          }
        ]
      }
    }
  ]
}
```

**Response (201):**
```json
{
  "id": 1,
  "uid": "rule-xyz-123",
  "orgID": 2,
  "folderUID": "org-acme-alerts",
  "ruleGroup": "device-alerts",
  "title": "High Temperature - sensor01",
  "condition": "C",
  "for": "5m0s",
  "updated": "2026-04-12T10:00:00Z",
  "provenance": "api",
  ...
}
```

**Key fields in `data` array:**
- `refId: "A"` — The actual datasource query (Flux for InfluxDB)
- `refId: "B"` — A reduce expression: takes the query result and reduces to a single number
- `refId: "C"` — A threshold expression: evaluates the condition (gt, lt, eq, etc.)
- `condition: "C"` — Tells Grafana which refId is the final condition

**Threshold evaluator types:**
| Type | Meaning |
|------|---------|
| `gt` | Greater than |
| `lt` | Less than |
| `within_range` | Between two values |
| `outside_range` | Outside two values |

**Other Alert Rule endpoints:**
```
GET    /api/v1/provisioning/alert-rules/{uid}        # Get rule
PUT    /api/v1/provisioning/alert-rules/{uid}        # Update rule
DELETE /api/v1/provisioning/alert-rules/{uid}        # Delete rule
GET    /api/v1/provisioning/folder/{folderUID}/rule-groups/{group}  # Get rule group
```

### 2.3 Contact Points API

**Create Contact Point:**
```
POST /api/v1/provisioning/contact-points
```

```json
{
  "name": "alert-email-sensor01-high-temp",
  "type": "email",
  "settings": {
    "addresses": "alice@example.com;bob@example.com",
    "singleEmail": false,
    "message": "Alert: {{ .CommonAnnotations.summary }}"
  },
  "disableResolveMessage": false
}
```

**Supported contact point types:**
`email`, `slack`, `webhook`, `pagerduty`, `opsgenie`, `victorops`, `telegram`, `teams`, `discord`, `googlechat`, `kafka`, `line`, `threema`, `sensugo`, `pushover`, `alertmanager`, `webex`, `oncall`

**Other endpoints:**
```
GET    /api/v1/provisioning/contact-points            # List all
PUT    /api/v1/provisioning/contact-points/{uid}      # Update
DELETE /api/v1/provisioning/contact-points/{uid}      # Delete
```

### 2.4 Notification Policies API

**Get notification policy tree:**
```
GET /api/v1/provisioning/policies
```

**Set notification policy tree:**
```
PUT /api/v1/provisioning/policies
```

```json
{
  "receiver": "default-email",
  "group_by": ["grafana_folder", "alertname"],
  "group_wait": "30s",
  "group_interval": "5m",
  "repeat_interval": "4h",
  "routes": [
    {
      "receiver": "alert-email-sensor01-high-temp",
      "matchers": ["device_id=sensor01", "metric=temperature"],
      "continue": false
    },
    {
      "receiver": "alert-email-sensor05-humidity",
      "matchers": ["device_id=sensor05", "metric=humidity"],
      "continue": false
    }
  ]
}
```

**How routing works:**
1. Alert fires with labels `{device_id: "sensor01", metric: "temperature", org: "acme"}`
2. Notification policy tree is evaluated top-down
3. First matching route wins (unless `continue: true`)
4. Matched route's receiver (contact point) gets the notification

### 2.5 Folders API (for organizing alert rules)

```
POST /api/folders
```
```json
{
  "uid": "org-acme-alerts",
  "title": "Acme Corp Alerts"
}
```

Each org gets its own folder. Alert rules live in folders.

### 2.6 Multi-Org API Scoping

**Critical header: `X-Grafana-Org-Id`**

Every API call must include this header to target the correct organization:

```bash
# Create alert rule in Org 2 (Acme Corp)
curl -X POST http://grafana:3000/api/v1/provisioning/alert-rules \
  -H "Authorization: Bearer $GRAFANA_TOKEN" \
  -H "X-Grafana-Org-Id: 2" \
  -H "Content-Type: application/json" \
  -d '{ ... }'

# Create alert rule in Org 3 (Beta Corp)
curl -X POST http://grafana:3000/api/v1/provisioning/alert-rules \
  -H "Authorization: Bearer $GRAFANA_TOKEN" \
  -H "X-Grafana-Org-Id: 3" \
  -H "Content-Type: application/json" \
  -d '{ ... }'
```

**Requirement:** The service account must be a **Grafana Server Admin** (not just org admin) to operate across organizations. Set this when creating the service account.

---

## 3. Multi-Org Alert Architecture

### 3.1 Isolation Model

Each Grafana organization has **completely separate**:
- Alert rules
- Contact points
- Notification policies
- Silences
- Mute timings
- Alert rule folders

This means Org A's alerts cannot see or affect Org B's alerts. Isolation is enforced at the Grafana database level.

### 3.2 Per-Org Setup (What Admin Creates)

When onboarding a new organisation, the backend:

```
For each new org:
  1. POST /api/orgs                          → Create Grafana org (returns orgId)
  2. POST /api/folders                       → Create alert folder "Org-{name}-Alerts"
     (with X-Grafana-Org-Id: {orgId})
  3. POST /api/v1/provisioning/contact-points → Create default email contact point
     (with X-Grafana-Org-Id: {orgId})
  4. PUT /api/v1/provisioning/policies       → Set notification policy tree
     (with X-Grafana-Org-Id: {orgId})
  5. For each device in org:
     → No alert rules yet (users create these from the web app)
```

### 3.3 Per-Alert Setup (What Happens When User Creates an Alert)

```
User creates alert in web app for sensor01, temperature > 30°C
  │
  ▼
Backend:
  1. Save alert config to PostgreSQL
  2. Determine Grafana orgId from user's organisation
  3. POST /api/v1/provisioning/contact-points
     (X-Grafana-Org-Id: {orgId})
     → Create contact point with user's email
  4. POST /api/v1/provisioning/alert-rules
     (X-Grafana-Org-Id: {orgId})
     → Create alert rule with:
       - Flux query filtered by device_id
       - Threshold condition
       - Labels: device_id, metric, org
  5. PUT /api/v1/provisioning/policies
     (X-Grafana-Org-Id: {orgId})
     → Update notification policy to route this alert's labels
       to the new contact point
  6. Store grafana_rule_uid in PostgreSQL for future updates/deletes
```

---

## 4. Our Platform's Alert Flow

### 4.1 Complete Sequence

```
User sets alert                Backend constructs               Grafana evaluates
in web app                     Grafana API calls                and notifies
─────────────                  ─────────────────                ──────────────────

  "Alert me if               POST contact-point               Every 1 minute:
   sensor01 temp              → user@example.com                Query InfluxDB
   goes above 30°C                                              for sensor01 temp
   for 5 minutes"            POST alert-rule
                              → Flux query +                   If > 30 for 5m:
                                threshold > 30                   → State: Firing
                                for: 5m                          → Route via policy
                              → labels: device_id,               → Send email
                                metric, org
                                                               If resolves:
                             PUT notification-policy             → State: Resolved
                              → route labels to                  → Send resolution
                                contact point                      email
```

### 4.2 Backend Service: GrafanaAlertClient

```python
# Pseudocode for the backend service

class GrafanaAlertClient:
    def __init__(self, grafana_url, admin_token):
        self.url = grafana_url
        self.token = admin_token

    def _headers(self, org_id: int):
        return {
            "Authorization": f"Bearer {self.token}",
            "X-Grafana-Org-Id": str(org_id),
            "Content-Type": "application/json",
        }

    def create_alert_rule(self, org_id, device_code, metric, condition, threshold, duration_sec, folder_uid):
        """Create a Grafana alert rule for a device metric."""
        flux_query = self._build_flux_query(device_code, metric)
        evaluator_type = "gt" if condition == "above" else "lt"

        body = {
            "title": f"{metric}-{condition}-{threshold}-{device_code}",
            "ruleGroup": "device-alerts",
            "folderUID": folder_uid,
            "condition": "C",
            "for": f"{duration_sec}s",
            "labels": {
                "device_id": device_code,
                "metric": metric,
            },
            "annotations": {
                "summary": f"{metric} is {condition} {threshold} on {device_code}",
            },
            "data": [
                # Query A: InfluxDB Flux query
                # Expression B: Reduce to last value
                # Expression C: Threshold comparison
                ...
            ]
        }
        resp = requests.post(
            f"{self.url}/api/v1/provisioning/alert-rules",
            headers=self._headers(org_id),
            json=body
        )
        return resp.json()["uid"]

    def create_contact_point(self, org_id, name, email):
        """Create an email contact point."""
        ...

    def update_notification_policy(self, org_id, routes):
        """Update the notification policy tree with new routes."""
        ...

    def delete_alert_rule(self, org_id, rule_uid):
        """Delete an alert rule."""
        requests.delete(
            f"{self.url}/api/v1/provisioning/alert-rules/{rule_uid}",
            headers=self._headers(org_id)
        )
```

---

## 5. Scaling Grafana Alerting

### 5.1 How Grafana Evaluates Alerts Internally

```
Grafana Alerting Scheduler
│
├── Rule Group "device-alerts" (Org 2)
│   ├── Rule 1: sensor01 temp > 30  ── evaluated sequentially
│   ├── Rule 2: sensor01 temp < 10     within the group
│   └── Rule 3: sensor02 temp > 35
│
├── Rule Group "device-alerts" (Org 3)  ── groups evaluate
│   ├── Rule 4: sensor05 temp > 28       in parallel
│   └── Rule 5: sensor06 humidity > 80
│
└── Rule Group "device-alerts" (Org 4)
    └── Rule 6: sensor09 temp > 25
```

- **Within a rule group:** Rules evaluate sequentially (one after another)
- **Across rule groups:** Groups evaluate in parallel (concurrently)
- **Across orgs:** Each org's groups are independent, evaluated in parallel

### 5.2 Scaling Characteristics

| Scale | Alert Rules | Behavior | Action Needed |
|-------|-------------|----------|---------------|
| **Small** | 1-100 rules | Grafana handles easily on a single instance | None |
| **Medium** | 100-500 rules | Still fine. Watch evaluation duration in Grafana metrics. | Monitor `grafana_alerting_rule_evaluation_duration_seconds` |
| **Large** | 500-2000 rules | Evaluation may lag. InfluxDB query load increases. | Increase Grafana CPU/memory. Optimize Flux queries. Increase evaluation intervals for non-critical alerts. |
| **Very Large** | 2000-5000 rules | Single Grafana instance under pressure. Evaluation backlog possible. | Split into multiple rule groups. Consider external alerting (see Section 6). |
| **Massive** | 5000+ rules | Grafana alerting not designed for this scale. | Move to dedicated alerting stack (Mimir Ruler + Alertmanager). |

### 5.3 Performance Bottlenecks

1. **InfluxDB query load:** Every alert rule fires a query every evaluation interval. 1000 rules at 1-minute intervals = ~17 queries/second to InfluxDB constantly. Solutions:
   - Increase evaluation interval (1m → 5m for non-critical alerts)
   - Use recording rules / continuous queries in InfluxDB to pre-aggregate
   - Ensure InfluxDB has adequate CPU/memory

2. **Grafana memory:** Each alert rule's state is held in memory. At thousands of rules, Grafana's memory footprint grows. Allocate 2-4GB for Grafana at the 1000+ rule scale.

3. **Notification storm:** If many alerts fire simultaneously (e.g., network outage causes all devices to go offline), Grafana sends many emails at once. Solutions:
   - Use `group_by` in notification policies to batch related alerts
   - Set `group_wait` (e.g., 30s) to collect alerts before sending
   - Set `repeat_interval` (e.g., 4h) to avoid repeat spam

### 5.4 Optimization Strategies

**1. Smart rule grouping:**
```
Don't: One rule group with 500 rules (sequential evaluation = slow)
Do:    50 rule groups with 10 rules each (parallel evaluation)
```

**2. Stagger evaluation intervals:**
```
Critical alerts (equipment failure): eval every 30s, for: 1m
Warning alerts (threshold breach):   eval every 2m,  for: 5m
Informational alerts (trends):       eval every 10m, for: 30m
```

**3. Use labels for efficient routing:**
Instead of one contact point per alert, use label-based routing:
```
Labels: { org: "acme", severity: "critical" }
Policy: match org="acme" AND severity="critical" → pagerduty-acme
Policy: match org="acme"                         → email-acme
```

**4. Folder-per-org for isolation and RBAC:**
```
Folder: org-acme-alerts   → only Acme's alert rules
Folder: org-beta-alerts   → only Beta's alert rules
```

---

## 6. When to Move Beyond Grafana Alerting

### 6.1 Grafana-Only (Stage 1: 1-50 orgs, <2000 alert rules)

```
Web App → Grafana Provisioning API → Grafana Alerting Engine → Email
```

This is where you start. Grafana handles everything.

### 6.2 Grafana + External Alertmanager (Stage 2: 50-200 orgs, 2000-5000 rules)

```
Web App → Grafana API → Grafana evaluates rules
                              │
                              ▼
                    External Alertmanager (Prometheus)
                              │
                              ▼ routes, groups, silences
                         Contact Points
```

Grafana can forward firing alerts to an external Alertmanager. This offloads notification routing, grouping, deduplication, and silencing to a dedicated system that handles it better at scale.

Configure in `grafana.ini`:
```ini
[unified_alerting]
execute_alerts = true
[unified_alerting.alertmanager]
# Use external Alertmanager for notification routing
```

### 6.3 Dedicated Alerting Stack (Stage 3: 200+ orgs, 5000+ rules)

At this scale, Grafana's alerting engine itself becomes the bottleneck. Move to:

```
InfluxDB / Time-series DB
         │
         ▼
Grafana Mimir Ruler (or Thanos Ruler)
    Evaluates alert rules at scale
    Horizontally scalable
         │
         ▼
Prometheus Alertmanager (clustered)
    Notification routing, dedup, silencing
         │
         ▼
Contact Points (email, Slack, webhook)
```

**Grafana Mimir Ruler:**
- Part of the Grafana Mimir project (open source)
- Designed to evaluate millions of alert rules
- Horizontally scalable (distributed across multiple pods)
- Compatible with PromQL and Grafana alerting rule format

At this stage, Grafana's role changes: it becomes the **UI for viewing alerts** and the **API for managing rules**, but the heavy lifting of evaluation and notification is done by external components.

### 6.4 Custom Alerting Engine (Stage 4: Platform-level scale)

If you outgrow even Mimir Ruler, or need per-tenant alerting guarantees:

```
Web App Backend
    │
    ├──▶ PostgreSQL (alert configs, source of truth)
    │
    ├──▶ Custom Alert Evaluator Service
    │    - Reads alert configs from DB
    │    - Queries InfluxDB/TimescaleDB on schedule
    │    - Evaluates thresholds
    │    - Pushes to notification queue
    │
    └──▶ Notification Service
         - Consumes from queue (RabbitMQ/Kafka)
         - Sends emails via SendGrid/SES
         - Handles rate limiting, retries, dedup
```

This is a significant engineering investment. Don't build this unless Grafana alerting is demonstrably inadequate.

### 6.5 Decision Matrix

| Signal | Action |
|--------|--------|
| Alert evaluation takes >80% of the evaluation interval | Increase interval or split groups |
| Grafana alerting memory >4GB | Move to external Alertmanager for notification routing |
| >5000 alert rules total | Evaluate Mimir Ruler |
| Need per-tenant alert rate limiting | Custom alerting engine |
| Need complex alert logic (ML, anomaly detection) | Custom alerting engine |
| Grafana alerting meets needs but email delivery is slow | Keep Grafana alerting, fix email layer (see EMAIL-NOTIFICATION-STRATEGY.md) |

---

## Summary

| Question | Answer |
|----------|--------|
| Can we set alerts via API? | **Yes.** Full CRUD via `/api/v1/provisioning/alert-rules`, contact-points, and policies. |
| Can we scope alerts per org? | **Yes.** Use `X-Grafana-Org-Id` header. Each org has fully isolated alerting. |
| Does it scale to our MVP? | **Yes.** Grafana handles hundreds of alert rules easily. |
| When does it stop scaling? | ~2000-5000 rules. Then add external Alertmanager. ~5000+ rules, consider Mimir Ruler. |
| Should we build custom alerting now? | **No.** Start with Grafana's built-in alerting. Move to external components only when you hit concrete limits. |

---

*Companion documents: [`EMAIL-NOTIFICATION-STRATEGY.md`](./EMAIL-NOTIFICATION-STRATEGY.md), [`SCALING-STRATEGY.md`](./SCALING-STRATEGY.md)*
