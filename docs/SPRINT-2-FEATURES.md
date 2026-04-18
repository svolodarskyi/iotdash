# Sprint 2 — Features Delivered

## Accomplished

### Alert CRUD Backend
- **List alerts** (`GET /api/alerts`) — returns all alerts for the user's organisation
- **Create alert** (`POST /api/alerts`) — validates device ownership, creates DB row, syncs to Grafana
- **Get alert** (`GET /api/alerts/{id}`) — org-scoped single alert retrieval
- **Update alert** (`PUT /api/alerts/{id}`) — partial update with Grafana re-sync
- **Delete alert** (`DELETE /api/alerts/{id}`) — removes DB row + Grafana rule + contact point + notification policy
- **Toggle alert** (`PATCH /api/alerts/{id}/toggle`) — enables/disables alert, pauses/unpauses Grafana rule

### Grafana Alerting Integration
- **GrafanaClient service** — wraps Grafana's Provisioning API for alert rules, contact points, notification policies
- **Alert folder management** — auto-creates "iotdash-alerts" folder in Grafana
- **Dynamic datasource UID lookup** — queries Grafana at runtime to find the InfluxDB datasource UID (not hardcoded)
- **Flux query generation** — builds device-specific InfluxDB queries filtering on `device_id` and `_field` tags
- **Threshold expressions** — translates "above/below" conditions to Grafana threshold evaluators
- **Per-alert email routing** — each alert gets its own contact point and notification policy route
- **Graceful failure** — alerts saved to DB even if Grafana sync fails
- **Automatic re-sync** — update or toggle on an alert with missing Grafana rule creates the rule on the fly

### Email Infrastructure
- **Mailhog** added to docker-compose for local email testing
- **Grafana SMTP** configured to send via Mailhog (port 1025)
- **Mailhog Web UI** at `localhost:8025` for viewing received alert emails

### Frontend Alert Pages
- **Alerts list** (`/alerts`) — table with device, condition, duration, email, toggle, edit/delete actions
- **Create alert** (`/alerts/new`) — form with device select, metric, condition, threshold, duration, email
- **Edit alert** (`/alerts/{id}/edit`) — pre-populated form, device read-only
- **Toggle switch** — enable/disable alerts inline from the list
- **Delete confirmation** — confirm dialog before deleting
- **Navigation** — "Devices" and "Alerts" links in header

### API Helpers
- **apiPut** — PUT requests with credentials
- **apiPatch** — PATCH requests with credentials
- **apiDelete** — DELETE requests with credentials

### Multi-Tenant Alert Isolation
- **Org-scoped alert queries** — alerts filtered through device → organisation join
- **Cross-org alert access returns 404** — no information leakage
- **Cross-org alert creation blocked** — cannot create alert on another org's device

### Testing
- **15 alert tests** — CRUD (10) + org isolation (5)
- **42 total backend tests** — all passing, up from 27 in Sprint 1
- **4 frontend tests** — all passing

### Seed Data
- **Two sample alerts** — Demo Corp sensor01 (temp > 30) + Acme IoT sensor03 (temp > 35)

## Business Value
- **Second demo moment** — create alert → trigger it → email arrives in Mailhog
- **Core product feature** — alerting is what turns a dashboard into an actionable monitoring platform
- **Self-service alerts** — users configure their own alerts without admin intervention
- **Multi-tenant alert isolation** — each org's alerts are completely independent

## Gaps Remaining
- **No alert history** — no record of when alerts fired / resolved (planned: Sprint 5)
- **No in-app notifications** — alerts only send email, no in-app bell/toast (planned: Sprint 5)
- **No duplicate detection** — user can create multiple identical alerts (planned: Sprint 3)
- **No alert validation** — no bounds checking on threshold values (planned: Sprint 3)
- **No bulk operations** — no "delete all" or "disable all" (planned: Sprint 3)
- **Single metric type** — only temperature, no humidity/pressure/custom (planned: Sprint 3)
- **No bulk re-sync endpoint** — individual re-sync works via update/toggle, but no "sync all" admin action (planned: Sprint 3)
- **Mailhog only** — no real email service (planned: Sprint 4 Azure deployment)
