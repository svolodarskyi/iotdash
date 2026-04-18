# Sprint 2 — Alerts (Week 5-6)

## Context

Sprint 1 delivered authentication, org-scoped data isolation, and embedded Grafana dashboards. Users can log in, see their org's devices, and view live charts. What's missing: users can't **act** on the data. Sprint 2 adds the alert system — users create threshold alerts in the web app, the backend syncs them to Grafana's alerting engine, and when conditions breach, Grafana sends an email notification.

**Sprint Review Deliverable:** Create alert "temperature > 30 for sensor01". Run fake_device with temps > 30. Receive email in Mailhog. Delete alert. Verify Grafana rule removed.

---

## What Already Exists

- **Alert model** (`backend/app/models.py`) — full schema with `metric`, `condition`, `threshold`, `duration_seconds`, `notification_email`, `is_enabled`, `grafana_rule_uid`, FK to devices + users
- **Alert table** in migration `001` — already created in PostgreSQL
- **Alert API spec** (`docs/planning/API-SPEC.md`) — endpoints + request/response shapes defined
- **Alert architecture** (`docs/planning/ARCHITECTURE.md` §6) — lifecycle, Grafana API calls, state machine
- **Device.alerts relationship** — already defined in models

---

## Key Decisions

**Grafana service account token** for backend → Grafana API calls. Created on first `docker compose up` via an init script that calls Grafana's admin API. Token stored in env var `GRAFANA_SERVICE_ACCOUNT_TOKEN`. The backend uses this token to create/update/delete alert rules, contact points, and notification policies.

**Mailhog** for local email testing. Grafana sends SMTP to Mailhog on port 1025. Mailhog web UI on port 8025 shows received emails. No real email service needed until Azure deployment (Sprint 4).

**Grafana Alerting Provisioning API** (`/api/v1/provisioning/alert-rules`). This is the programmatic API for managing alert rules — unlike the Ruler API, it doesn't require Cortex/Mimir. Works out of the box with Grafana's built-in alertmanager.

**Alert CRUD is org-scoped.** Alerts belong to devices, devices belong to orgs. All alert queries join through device to enforce `organisation_id == current_user.organisation_id`. Cross-org alert access returns 404.

**Grafana sync is synchronous on create/update/delete.** When a user creates an alert, the backend immediately calls Grafana's API and stores the returned `rule_uid`. If Grafana is unreachable, the API returns 502. No background queue — overkill for MVP scale.

**Notification routing via label matching.** Each alert rule gets a label `iotdash_alert_id={uuid}`. A notification policy routes that label to a contact point named `alert-{uuid}` with the user's email. This avoids the "all alerts go to one email" problem.

**`httpx`** for backend → Grafana HTTP calls. Already used in the Python ecosystem, async-capable, cleaner than `requests` for service-to-service calls. Add `httpx>=0.27,<1` to requirements.txt.

---

## Step 1: Infrastructure — Mailhog + Grafana SMTP + Service Account

### `docker-compose.yml` — add Mailhog service

```yaml
mailhog:
  image: mailhog/mailhog:latest
  container_name: mailhog
  ports:
    - "1025:1025"   # SMTP
    - "8025:8025"   # Web UI
  networks:
    - iot_net
```

### `docker-compose.yml` — Grafana SMTP + alerting env vars

Add to `grafana.environment`:
```yaml
GF_SMTP_ENABLED: "true"
GF_SMTP_HOST: "mailhog:1025"
GF_SMTP_SKIP_VERIFY: "true"
GF_SMTP_FROM_ADDRESS: "alerts@iotdash.local"
GF_SMTP_FROM_NAME: "IoTDash Alerts"
GF_UNIFIED_ALERTING_ENABLED: "true"
```

### `docker-compose.yml` — backend env vars

Add to `backend.environment`:
```yaml
GRAFANA_ADMIN_USER: ${GRAFANA_ADMIN_USER:-admin}
GRAFANA_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD:-admin}
```

### `backend/app/config.py` — new settings

```python
GRAFANA_ADMIN_USER: str = "admin"
GRAFANA_ADMIN_PASSWORD: str = "admin"
```

### `.env.example` — add

```
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin
```

### `backend/requirements.txt` — add httpx

```
httpx>=0.27,<1
```

---

## Step 2: Grafana Client Service

**Create `backend/app/services/__init__.py`** — empty.

**Create `backend/app/services/grafana_client.py`:**

A class that wraps Grafana's HTTP API using httpx. All calls use basic auth (`admin:admin`) since we're calling from the backend (internal network). Methods:

- `__init__(base_url, admin_user, admin_password)` — stores config
- `create_alert_rule(alert, device, org) → str` — calls `POST /api/v1/provisioning/alert-rules`, returns Grafana `rule_uid`. The rule:
  - Uses the org's InfluxDB datasource
  - Flux query: `from(bucket:"iot") |> range(start:-{duration}s) |> filter(fn:(r) => r.device_id == "{device_code}") |> filter(fn:(r) => r._field == "{metric}") |> filter(fn:(r) => r.message_type == "message")`
  - Reduce expression: `last()` then threshold comparison (`condition` + `threshold`)
  - Evaluation interval: `1m`, for duration: `duration_seconds`
  - Labels: `{iotdash_alert_id: str(alert.id), device_code: device.device_code}`
  - Folder: use "alerts" folder (created if missing via `POST /api/v1/folders`)
  - Rule group: `iotdash-alerts`
- `update_alert_rule(grafana_rule_uid, alert, device, org) → None` — `PUT /api/v1/provisioning/alert-rules/{uid}`
- `delete_alert_rule(grafana_rule_uid) → None` — `DELETE /api/v1/provisioning/alert-rules/{uid}`
- `ensure_contact_point(alert) → None` — `POST /api/v1/provisioning/contact-points` with type `email`, name `alert-{alert.id}`, addresses `alert.notification_email`
- `update_contact_point(alert) → None` — `PUT /api/v1/provisioning/contact-points/{uid}`
- `delete_contact_point(alert_id) → None` — `DELETE /api/v1/provisioning/contact-points/{uid}`
- `ensure_notification_policy(alert) → None` — reads current policy tree via `GET /api/v1/provisioning/policies`, adds/updates a child route matching label `iotdash_alert_id={alert.id}` → contact point `alert-{alert.id}`
- `remove_notification_policy(alert_id) → None` — removes the child route for this alert from the policy tree
- `ensure_alerts_folder() → str` — `GET /api/v1/folders`, if "iotdash-alerts" folder doesn't exist, create it. Returns folder UID.

**Error handling:** All methods raise `HTTPException(502, "Grafana API error: {detail}")` on failure. The router catches these and returns them to the frontend.

---

## Step 3: Alert Schemas

**`backend/app/schemas.py`** — add:

```python
class AlertCreate(BaseModel):
    device_id: uuid.UUID
    metric: str  # "temperature"
    condition: str  # "above" | "below"
    threshold: float
    duration_seconds: int = 60
    notification_email: str

class AlertUpdate(BaseModel):
    metric: str | None = None
    condition: str | None = None
    threshold: float | None = None
    duration_seconds: int | None = None
    notification_email: str | None = None

class AlertToggle(BaseModel):
    is_enabled: bool

class AlertOut(BaseModel):
    id: uuid.UUID
    device_id: uuid.UUID
    device_code: str  # denormalized from device relationship
    created_by: uuid.UUID | None
    metric: str
    condition: str
    threshold: float
    duration_seconds: int
    notification_email: str | None
    is_enabled: bool
    grafana_rule_uid: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

Note: `AlertOut.device_code` comes from `alert.device.device_code` — the router will construct this manually or we add a `@computed_field` / build it in the response.

---

## Step 4: Alert Router

**Create `backend/app/routers/alerts.py`:**

All endpoints inject `current_user` via `Depends(get_current_user)`. Org scoping enforced by joining through `Device.organisation_id`.

- `GET /api/alerts` → `list[AlertOut]` — query `Alert` joined with `Device` where `Device.organisation_id == current_user.organisation_id`. Return all alerts for the user's org.
- `POST /api/alerts` → `AlertOut` (201) — validate device belongs to user's org, create Alert row, call `grafana_client.ensure_alerts_folder()`, `grafana_client.create_alert_rule()`, `grafana_client.ensure_contact_point()`, `grafana_client.ensure_notification_policy()`, store `grafana_rule_uid`, commit, return alert.
- `GET /api/alerts/{alert_id}` → `AlertOut` — compound filter on alert ID + device org scoping. 404 if not found / wrong org.
- `PUT /api/alerts/{alert_id}` → `AlertOut` — load alert (org-scoped), apply partial updates, call `grafana_client.update_alert_rule()` + `grafana_client.update_contact_point()` if email changed, commit, return.
- `DELETE /api/alerts/{alert_id}` → 204 — load alert (org-scoped), call `grafana_client.delete_alert_rule()` + `grafana_client.delete_contact_point()` + `grafana_client.remove_notification_policy()`, delete from DB, commit.
- `PATCH /api/alerts/{alert_id}/toggle` → `AlertOut` — load alert, flip `is_enabled`, if disabling: Grafana rule still exists but we set `"isPaused": true` via update. If enabling: set `"isPaused": false`. Commit, return.

**`backend/app/main.py`** — register alerts router:
```python
from app.routers import alerts
app.include_router(alerts.router)
```

---

## Step 5: Backend Tests

### `backend/tests/conftest.py` — additions

- Add `Alert` import to model imports
- `alert_seed(db, seed_data, seed_user)` fixture — creates 1 alert for device1 in test org. Returns alert + references.
- Update `two_org_seed` fixture to include alerts: 1 alert per org (device_a gets an alert from user_a, device_b gets an alert from user_b).

### Create `backend/tests/test_alerts.py`

**CRUD tests (use `auth_client` + `seed_data` fixtures):**
- `test_list_alerts_empty` — no alerts, returns `[]`
- `test_create_alert` — POST with valid body, assert 201, check response fields, check `created_by == seed_user.id`
- `test_create_alert_device_not_found` — POST with random device_id, assert 404
- `test_create_alert_wrong_org_device` — POST with device from other org, assert 404
- `test_get_alert` — create then GET by ID, assert 200
- `test_get_alert_not_found` — GET random UUID, assert 404
- `test_update_alert` — PUT with new threshold, assert 200, check updated value
- `test_delete_alert` — DELETE, assert 204, then GET returns 404
- `test_toggle_alert` — PATCH toggle to disabled, assert `is_enabled == false`
- `test_list_alerts_unauthenticated` — no cookie, assert 401

**Org isolation tests (use `two_org_seed`):**
- `test_org_a_cannot_see_org_b_alerts` — user_a lists alerts, sees only org_a's
- `test_org_a_cannot_get_org_b_alert` — user_a GETs org_b's alert by ID, 404
- `test_org_a_cannot_delete_org_b_alert` — user_a DELETEs org_b's alert, 404
- `test_org_a_cannot_create_alert_on_org_b_device` — user_a POSTs alert for org_b device, 404

**Note:** Tests mock the Grafana client to avoid needing a running Grafana instance. Use `unittest.mock.patch` on `app.services.grafana_client.GrafanaClient` methods to return fake UIDs.

---

## Step 6: Frontend — Types + API Helpers

### `frontend/src/types/api.ts` — add

```typescript
export interface Alert {
  id: string
  device_id: string
  device_code: string
  created_by: string | null
  metric: string
  condition: string
  threshold: number
  duration_seconds: number
  notification_email: string | null
  is_enabled: boolean
  grafana_rule_uid: string | null
  created_at: string
  updated_at: string
}

export interface AlertCreate {
  device_id: string
  metric: string
  condition: string
  threshold: number
  duration_seconds: number
  notification_email: string
}

export interface AlertUpdate {
  metric?: string
  condition?: string
  threshold?: number
  duration_seconds?: number
  notification_email?: string
}

export interface AlertToggle {
  is_enabled: boolean
}
```

### `frontend/src/lib/api.ts` — add PUT, PATCH, DELETE helpers

```typescript
export async function apiPut<T>(path: string, body: unknown): Promise<T>
export async function apiPatch<T>(path: string, body: unknown): Promise<T>
export async function apiDelete(path: string): Promise<void>
```

All use `credentials: 'include'` and follow the same pattern as `apiPost`.

---

## Step 7: Frontend — Alert Hooks

**Create `frontend/src/hooks/useAlerts.ts`:**

- `useAlerts()` — `useQuery(['alerts'], () => apiFetch<Alert[]>('/api/alerts'))`. `staleTime: 30s`.
- `useAlert(alertId)` — `useQuery(['alerts', alertId], () => apiFetch<Alert>(`/api/alerts/${alertId}`))`.
- `useCreateAlert()` — `useMutation` calling `apiPost<Alert, AlertCreate>('/api/alerts', body)`. On success → `invalidateQueries(['alerts'])`.
- `useUpdateAlert()` — `useMutation` calling `apiPut<Alert>(`/api/alerts/${id}`, body)`. On success → `invalidateQueries(['alerts'])`.
- `useDeleteAlert()` — `useMutation` calling `apiDelete(`/api/alerts/${id}`)`. On success → `invalidateQueries(['alerts'])`.
- `useToggleAlert()` — `useMutation` calling `apiPatch<Alert>(`/api/alerts/${id}/toggle`, { is_enabled })`. On success → `invalidateQueries(['alerts'])`.

---

## Step 8: Frontend — Alerts List Page

**Create `frontend/src/routes/_authenticated/alerts/index.tsx`:**

Route: `/alerts`

Layout:
- Page title: "Alerts"
- "New Alert" button → navigates to `/alerts/new`
- Table/card list of alerts:
  - Device name (from `device_code`)
  - Metric + condition + threshold (e.g., "temperature above 30.0")
  - Duration (formatted, e.g., "5 minutes")
  - Notification email
  - Enabled toggle (calls `useToggleAlert`)
  - Edit button → `/alerts/{id}/edit`
  - Delete button → confirm dialog → `useDeleteAlert`
- Empty state: "No alerts configured. Create one to get notified when device metrics exceed thresholds."

---

## Step 9: Frontend — Create Alert Page

**Create `frontend/src/routes/_authenticated/alerts/new.tsx`:**

Route: `/alerts/new`

Form fields:
- **Device** — select dropdown, populated from `useDevices()`. Shows `device.name (device.device_code)`.
- **Metric** — select dropdown: `temperature` (hardcoded for now — only sensor type). Extensible later.
- **Condition** — select dropdown: `above`, `below`.
- **Threshold** — number input with step 0.1.
- **Duration** — number input (seconds), with helper text "Alert fires after condition holds for this many seconds". Default 60.
- **Notification email** — text input, pre-filled with current user's email from auth store.
- **Submit** → calls `useCreateAlert()`, on success navigate to `/alerts`.
- **Cancel** → navigate to `/alerts`.
- Validation: all fields required, threshold must be a number, email must look valid.
- Error display: if mutation fails, show error message.

---

## Step 10: Frontend — Edit Alert Page

**Create `frontend/src/routes/_authenticated/alerts/$alertId.edit.tsx`:**

Route: `/alerts/{alertId}/edit`

Same form as create, but:
- Pre-populated with existing alert data via `useAlert(alertId)`.
- Device field is **read-only** (can't change device on an existing alert — would invalidate the Grafana rule).
- Submit calls `useUpdateAlert()`.
- Loading state while fetching alert.
- 404 handling if alert not found.

---

## Step 11: Frontend — Navigation Update

**`frontend/src/components/Layout.tsx`** — add "Alerts" nav link to header (next to dashboard link). Only visible when authenticated.

Navigation order: Dashboard | Alerts | [spacer] | User info + Logout

---

## Step 12: Frontend Tests

**Create `frontend/src/__tests__/alerts.test.ts`:**

- `test_alert_types_exist` — import Alert, AlertCreate types, verify they compile
- `test_api_delete_helper` — mock fetch, call `apiDelete`, verify method + credentials

---

## Step 13: Seed Data Update

**`backend/app/seed.py`** — add sample alerts to seed:

- Demo Corp: 1 alert on sensor01 — "temperature above 30, email admin@democorp.com, duration 60s"
- Acme IoT: 1 alert on sensor03 — "temperature above 35, email viewer@acmeiot.com, duration 120s"

These alerts won't have `grafana_rule_uid` (Grafana sync happens via API at runtime, not seed time). The seed just creates the DB rows so the frontend has data to display.

---

## Step 14: Documentation

- `docs/SPRINT-2-WEEK5-DECISIONS.md` — Grafana alerting API choice, Mailhog for dev email, httpx for HTTP client, sync vs async Grafana calls, notification routing via labels
- `docs/SPRINT-2-WEEK5-FEATURES.md` — features delivered, business value, gaps remaining
- `docs/SPRINT-2-WEEK6-MANUAL-QA.md` — QA checklist:
  1. Fresh start (docker compose down -v, up, migrate, seed)
  2. Login as Demo Corp admin
  3. Navigate to /alerts — see 1 seeded alert
  4. Create new alert (sensor02, temperature above 25, email admin@democorp.com)
  5. See alert in list with enabled toggle
  6. Toggle alert off/on
  7. Edit alert threshold
  8. Delete alert
  9. Login as Acme IoT viewer — see only Acme's alert
  10. Grafana sync test: create alert → check Grafana alerting UI shows rule
  11. End-to-end: create alert with low threshold → modify fake_device to exceed → check Mailhog for email
  12. API returns 401 without auth: `curl /api/alerts`
  13. Tests pass: backend + frontend

---

## Files Created (9)
- `backend/app/services/__init__.py`
- `backend/app/services/grafana_client.py`
- `backend/app/routers/alerts.py`
- `backend/tests/test_alerts.py`
- `frontend/src/hooks/useAlerts.ts`
- `frontend/src/routes/_authenticated/alerts/index.tsx`
- `frontend/src/routes/_authenticated/alerts/new.tsx`
- `frontend/src/routes/_authenticated/alerts/$alertId.edit.tsx`
- `frontend/src/__tests__/alerts.test.ts`

## Files Modified (11)
- `docker-compose.yml` — add Mailhog service, Grafana SMTP env, backend Grafana env
- `backend/requirements.txt` — add httpx
- `backend/app/config.py` — GRAFANA_ADMIN_USER, GRAFANA_ADMIN_PASSWORD
- `backend/app/schemas.py` — AlertCreate, AlertUpdate, AlertToggle, AlertOut
- `backend/app/main.py` — register alerts router
- `backend/app/seed.py` — add sample alerts
- `backend/tests/conftest.py` — alert fixtures, mock Grafana client
- `frontend/src/types/api.ts` — Alert types
- `frontend/src/lib/api.ts` — apiPut, apiPatch, apiDelete helpers
- `frontend/src/components/Layout.tsx` — Alerts nav link
- `.env.example` — GRAFANA_ADMIN_USER, GRAFANA_ADMIN_PASSWORD

---

## Verification

1. `docker compose down -v && docker compose up --build -d` — 8 services (+ mailhog)
2. `docker compose exec backend alembic upgrade head` — migrations applied
3. `docker compose exec backend python -m app.seed` — seeds 2 orgs, 2 users, 3 devices, 2 alerts
4. Open `http://localhost:5173`, login as `admin@democorp.com` / `admin123`
5. Click "Alerts" in nav → see 1 seeded alert for sensor01
6. Click "New Alert" → create alert: sensor02, temperature above 25, 60s, admin@democorp.com
7. See new alert in list → toggle it off/on → edit threshold → delete it
8. Logout, login as `viewer@acmeiot.com` → see only Acme's alert
9. Create alert with threshold 20 → run `python fake_device.py` (temp ~22°C) → wait ~2 minutes
10. Open `http://localhost:8025` (Mailhog) → email from IoTDash Alerts about threshold breach
11. Delete the alert → Grafana UI (`http://localhost:3000/alerting/list`) shows rule removed
12. `docker compose run --rm --no-deps backend pytest -v` — all tests pass
13. `docker compose exec frontend npm test` — frontend tests pass
