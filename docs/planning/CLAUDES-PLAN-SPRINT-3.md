# Sprint 3 — Admin Panel + Device Provisioning + Multi-Metric Dashboards

## Context

Sprint 2 delivered alert CRUD with Grafana integration and email notifications. The platform now supports two demo orgs, JWT auth, org-scoped data isolation, and end-to-end alerting. But everything is seeded via scripts — there's no admin UI to create orgs, devices, or users. Devices are hardcoded to a single metric (temperature). The dashboard is a static Grafana JSON file.

Sprint 3 adds the admin panel, device provisioning with MQTT-based metric enablement, multi-metric dashboards, and a metrics catalog. The demo moment: admin provisions a new device with humidity + temperature metrics → device receives MQTT config → dashboard shows both metrics as separate graphs.

---

## Key Decisions

**Admin routes under `/api/admin/*` with role guard.** A `require_admin` FastAPI dependency checks `current_user.role == "admin"`. All admin endpoints use this. Regular users get 403 on admin routes. Existing user-facing endpoints (`/api/devices`, `/api/alerts`) stay unchanged.

**Metrics catalog table.** A `metrics` table stores the supported metric types (temperature, humidity, engine_rpm) with units and data types. Seeded on first run. Extensible — admin can add new metric types later. This replaces hardcoded metric assumptions throughout the app.

**DeviceMetric join table for per-device metric enablement.** Rather than the user's proposed three-table model (device_provisions + device_metrics + device_provision_metrics), we add a single `device_metrics` table linking devices to metrics with an `is_enabled` flag. The current `Device` table already captures the provisioning concept (device_code = UID, organisation_id = assignment). This avoids a large schema overhaul while supporting the same workflow.

**MQTT publisher via `paho-mqtt`.** The backend publishes to `{device_code}/to/config` with `{"addMetrics": [...]}` when an admin enables a device or its metrics. The `paho-mqtt` library was already identified in SKILLS-AND-FEATURES-BREAKDOWN.md. Synchronous publish with fire-and-forget QoS 0 — matching the existing telemetry pipeline.

**Parametric Grafana dashboard with `$device_id` and `$metric` variables.** Replace the static `temperature.json` with a single `iot-metrics.json` dashboard that uses template variables. Each embed URL passes `var-device_id=sensor01&var-metric=temperature`. One dashboard template handles all metrics — no per-metric dashboard files. The backend generates one embed URL per enabled metric per device.

**Device UID: auto-generated or manual entry.** `POST /api/admin/devices` accepts an optional `device_code` field. If omitted, a short UUID is generated (8 chars, e.g. `dev-a1b2c3d4`). If provided, uniqueness is validated against existing devices. A checkbox in the admin UI toggles between manual and auto-gen modes.

**Auto-enable on provision.** The admin device creation form includes an "Auto-enable" checkbox. If checked, after creating the device and its metric assignments, the backend immediately publishes the MQTT config. If unchecked, the device is created but no MQTT message is sent — admin can enable later via a "Send Config" button.

---

## Data Model Changes (Migration 002)

### New table: `metrics`

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default uuid4 |
| name | VARCHAR(100) | NOT NULL, UNIQUE (e.g. "temperature", "humidity", "engine_rpm") |
| unit | VARCHAR(50) | nullable (e.g. "°C", "%", "rpm") |
| data_type | VARCHAR(50) | NOT NULL, default "float" |
| description | TEXT | nullable |
| created_at | TIMESTAMPTZ | server_default now() |

### New table: `device_metrics`

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default uuid4 |
| device_id | UUID | FK → devices.id, NOT NULL |
| metric_id | UUID | FK → metrics.id, NOT NULL |
| is_enabled | BOOLEAN | NOT NULL, default TRUE |
| enabled_at | TIMESTAMPTZ | server_default now() |
| disabled_at | TIMESTAMPTZ | nullable |
| UNIQUE | | (device_id, metric_id) |

### Seed data: 3 default metrics
- `temperature` — unit: "°C", data_type: "float", description: "Temperature reading"
- `humidity` — unit: "%", data_type: "float", description: "Relative humidity"
- `engine_rpm` — unit: "rpm", data_type: "float", description: "Engine revolutions per minute"

### Seed data: link existing devices to metrics
- sensor01: temperature (enabled)
- sensor02: temperature (enabled)
- sensor03: temperature (enabled)

---

## Step 1: Backend — Admin Role Guard + Config

**Create `backend/app/auth.py`** — add `require_admin` dependency:
```python
def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
```

**`backend/app/config.py`** — add:
- `MQTT_BROKER_HOST: str = "emqx"` (internal Docker network)
- `MQTT_BROKER_PORT: int = 1883`

**`docker-compose.yml`** — add to backend environment:
- `MQTT_BROKER_HOST: ${MQTT_BROKER_HOST:-emqx}`
- `MQTT_BROKER_PORT: ${MQTT_BROKER_PORT:-1883}`

**`backend/requirements.txt`** — add `paho-mqtt>=2.0,<3`

## Step 2: Database — Migration 002

**Create `backend/alembic/versions/002_metrics_and_device_metrics.py`:**
- Create `metrics` table
- Create `device_metrics` table with composite unique constraint on (device_id, metric_id)
- No changes to existing tables

**`backend/app/models.py`** — add:
- `Metric` model (id, name, unit, data_type, description, created_at)
- `DeviceMetric` model (id, device_id, metric_id, is_enabled, enabled_at, disabled_at)
- Relationships: `Device.device_metrics`, `Metric.device_metrics`

## Step 3: Backend — Schemas for Admin + Metrics

**`backend/app/schemas.py`** — add:

```python
# Metrics
class MetricOut(BaseModel):
    id: uuid.UUID
    name: str
    unit: str | None
    data_type: str
    description: str | None

class DeviceMetricOut(BaseModel):
    metric_id: uuid.UUID
    metric_name: str
    metric_unit: str | None
    is_enabled: bool
    enabled_at: datetime
    disabled_at: datetime | None

# Admin — Organisations
class OrgCreate(BaseModel):
    name: str

class OrgUpdate(BaseModel):
    name: str | None = None

# Admin — Users
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    organisation_id: uuid.UUID
    role: str = "viewer"

class UserUpdate(BaseModel):
    email: str | None = None
    full_name: str | None = None
    role: str | None = None
    is_active: bool | None = None

# Admin — Devices
class DeviceCreate(BaseModel):
    device_code: str | None = None    # auto-generated if omitted
    name: str
    organisation_id: uuid.UUID
    device_type: str = "sensor"
    metric_ids: list[uuid.UUID] = []  # metrics to enable
    auto_enable: bool = False         # send MQTT config immediately

class DeviceUpdate(BaseModel):
    name: str | None = None
    device_type: str | None = None
    is_active: bool | None = None

class DeviceAdminOut(BaseModel):
    """Extended device output for admin views — includes metrics."""
    id: uuid.UUID
    device_code: str
    name: str
    organisation_id: uuid.UUID
    organisation_name: str
    device_type: str
    is_active: bool
    metrics: list[DeviceMetricOut]
    created_at: datetime
    updated_at: datetime

class DeviceMetricUpdate(BaseModel):
    metric_ids: list[uuid.UUID]       # full replacement of enabled metrics
    send_config: bool = False         # publish MQTT config after update

class DeviceSendConfigResponse(BaseModel):
    device_code: str
    metrics_sent: list[str]
    success: bool
```

## Step 4: Backend — MQTT Publisher Service

**Create `backend/app/services/mqtt_publisher.py`:**
- `MqttPublisher` class
- `__init__(broker_host, broker_port)` — connects to EMQX
- `send_device_config(device_code: str, metrics: list[str])` — publishes to `{device_code}/to/config` with `{"addMetrics": metrics}`
- `disconnect()` — cleanup
- `get_mqtt_publisher()` — factory for FastAPI DI
- Synchronous, fire-and-forget, reconnect on failure, log errors
- QoS 0 (same as telemetry pipeline)

## Step 5: Backend — Metrics Router

**Create `backend/app/routers/metrics.py`:**
- `GET /api/metrics` — list all metrics (all authenticated users). Used by dashboard metric selector and alert creation form.

Register in `main.py`.

## Step 6: Backend — Admin Routers

**Create `backend/app/routers/admin_orgs.py`:**
- `GET /api/admin/organisations` — list all orgs (admin only)
- `POST /api/admin/organisations` — create org
- `PUT /api/admin/organisations/{id}` — update org
- `DELETE /api/admin/organisations/{id}` — delete org (cascade: check for devices/users first)

**Create `backend/app/routers/admin_users.py`:**
- `GET /api/admin/users` — list all users, optional `?org_id=` filter
- `POST /api/admin/users` — create user (bcrypt hash password, assign to org)
- `PUT /api/admin/users/{id}` — update user
- `DELETE /api/admin/users/{id}` — deactivate user (soft delete via is_active=False)

**Create `backend/app/routers/admin_devices.py`:**
- `GET /api/admin/devices` — list all devices with metrics, optional `?org_id=` filter
- `POST /api/admin/devices` — provision device:
  1. Generate device_code if not provided (8-char hex from uuid4)
  2. Create Device row
  3. Create DeviceMetric rows for selected metrics
  4. If `auto_enable`: publish MQTT config via MqttPublisher
  5. Return DeviceAdminOut
- `PUT /api/admin/devices/{id}` — update device details
- `DELETE /api/admin/devices/{id}` — delete device (cascade alerts + device_metrics)
- `PATCH /api/admin/devices/{id}/metrics` — update enabled metrics for a device
- `POST /api/admin/devices/{id}/send-config` — (re)send MQTT config for currently enabled metrics. This is the "enable again" / "re-send config" button.

Register all admin routers in `main.py`.

## Step 7: Backend — Updated Device Embed URLs (Metric-Aware)

**Modify `backend/app/routers/devices.py`** — update `get_device_embed_urls`:
- Query `DeviceMetric` for the device (only enabled metrics)
- For each enabled metric, generate an embed URL using the parametric dashboard:
  ```
  {grafana_url}/d-solo/iot-metrics?orgId=1&panelId=1&var-device_id={device_code}&var-metric={metric_name}&from=now-5m&to=now&refresh=5s
  ```
- Return one embed URL per enabled metric
- If no metrics enabled, return empty list

**Add `GET /api/devices/{device_id}/metrics`** — return list of enabled metrics for a device (DeviceMetricOut). Used by the frontend metric selector.

## Step 8: Grafana — Parametric Multi-Metric Dashboard

**Replace `grafana/provisioning/dashboards/temperature.json`** with **`iot-metrics.json`:**
- UID: `iot-metrics`
- Template variables:
  - `device_id` — hidden, set via URL `var-device_id`
  - `metric` — hidden, set via URL `var-metric`
- Single time-series panel (id=1):
  - Flux query uses `$device_id` and `$metric` variables:
    ```flux
    from(bucket: "iot")
      |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
      |> filter(fn: (r) => r._measurement == "mqtt_consumer")
      |> filter(fn: (r) => r.device_id == "${device_id}")
      |> filter(fn: (r) => r._field == "${metric}")
      |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
    ```
  - Title: `${metric} (Live)`
  - Dynamic Y-axis label from `$metric`
- Time range: last 5 minutes, refresh 5s

**Update `grafana/provisioning/dashboards/dashboards.yaml`** — point to the new file.

**Update `GrafanaDashboard` seed data** — change grafana_uid to `iot-metrics`, update panel_ids.

## Step 9: Backend — Seed Data Update

**`backend/app/seed.py`** — update to:
1. Seed 3 metrics (temperature, humidity, engine_rpm) — idempotent, check by name
2. Seed DeviceMetric rows linking existing devices to temperature metric
3. Keep existing org/user/device/alert seeding
4. Update GrafanaDashboard seed to reference `iot-metrics` dashboard UID

## Step 10: Frontend — Types + API Helpers

**`frontend/src/types/api.ts`** — add:
- `Metric` (id, name, unit, data_type, description)
- `DeviceMetric` (metric_id, metric_name, metric_unit, is_enabled, enabled_at, disabled_at)
- `DeviceAdmin` (id, device_code, name, organisation_id, organisation_name, device_type, is_active, metrics, created_at, updated_at)
- `DeviceCreate` (device_code?, name, organisation_id, device_type, metric_ids, auto_enable)
- `DeviceUpdate` (name?, device_type?, is_active?)
- `DeviceMetricUpdate` (metric_ids, send_config)
- `OrgCreate` (name)
- `UserCreate` (email, password, full_name, organisation_id, role)
- `UserUpdate` (email?, full_name?, role?, is_active?)

**`frontend/src/lib/api.ts`** — no changes needed (apiPost/apiPut/apiPatch/apiDelete already exist).

## Step 11: Frontend — Admin Hooks

**Create `frontend/src/hooks/useAdmin.ts`:**
- `useAdminOrgs()` — `GET /api/admin/organisations`
- `useCreateOrg()` — `POST /api/admin/organisations`
- `useUpdateOrg()` — `PUT /api/admin/organisations/{id}`
- `useDeleteOrg()` — `DELETE /api/admin/organisations/{id}`
- `useAdminUsers(orgId?)` — `GET /api/admin/users`
- `useCreateUser()` — `POST /api/admin/users`
- `useUpdateUser()` — `PUT /api/admin/users/{id}`
- `useDeleteUser()` — `DELETE /api/admin/users/{id}`
- `useAdminDevices(orgId?)` — `GET /api/admin/devices`
- `useCreateDevice()` — `POST /api/admin/devices`
- `useUpdateDevice()` — `PUT /api/admin/devices/{id}`
- `useDeleteDevice()` — `DELETE /api/admin/devices/{id}`
- `useUpdateDeviceMetrics()` — `PATCH /api/admin/devices/{id}/metrics`
- `useSendDeviceConfig()` — `POST /api/admin/devices/{id}/send-config`
- `useMetrics()` — `GET /api/metrics`

## Step 12: Frontend — Admin Pages

**Create `frontend/src/routes/_authenticated/admin/` directory:**

**`admin/index.tsx`** — Admin dashboard/landing page. Links to orgs, users, devices sections. Only accessible to admin role.

**`admin/organisations.tsx`** — Org management page:
- Table: name, device count, user count, created_at
- "Create Org" button → inline form or modal
- Edit/Delete actions per row

**`admin/users.tsx`** — User management page:
- Table: email, full_name, org name, role, is_active, created_at
- Org filter dropdown
- "Create User" button → form (email, password, full_name, org select, role select)
- Edit/Deactivate actions

**`admin/devices.tsx`** — Device management page (the star of Sprint 3):
- Table: device_code (UID), name, org name, device_type, enabled metrics (chips/badges), is_active
- Org filter dropdown
- "Provision Device" button → form:
  - Device name (required)
  - Device UID: toggle between "Auto-generate" (checkbox) and manual text input. If manual, validate uniqueness on blur.
  - Organisation (dropdown)
  - Device type (dropdown or text)
  - Metrics (checkbox group): temperature, humidity, engine_rpm
  - Auto-enable (checkbox): "Send config to device immediately"
- Per-device actions:
  - Edit (name, type)
  - Manage Metrics → modal with metric checkboxes + "Send config" toggle
  - "Re-send Config" button (always available, for retry scenarios)
  - Delete (with confirmation)

## Step 13: Frontend — Updated Device Detail Page (Multi-Metric)

**Modify `frontend/src/routes/_authenticated/dashboard/$deviceId.tsx`:**
- Fetch device metrics via `GET /api/devices/{id}/metrics`
- Show metric selector: pill/chip buttons for each enabled metric (e.g. [Temperature] [Humidity] [Engine RPM])
- "Show All" option selected by default
- Each selected metric renders its own Grafana iframe embed
- Embeds use the new parametric URL: `var-device_id={code}&var-metric={metric_name}`
- Each iframe has a label showing metric name + unit

## Step 14: Frontend — Layout + Navigation Update

**`frontend/src/components/Layout.tsx`:**
- Add "Admin" nav link (visible only when `user.role === "admin"`)
- Admin link points to `/admin`

**Create `frontend/src/routes/_authenticated/admin.tsx`** (layout guard):
- `beforeLoad`: check `user.role === "admin"`, redirect to `/dashboard` if not
- Wraps all `/admin/*` child routes

## Step 15: Updated fake_device.py

**Modify `fake_device.py`:**
- Subscribe to `{device_id}/to/config` topic
- Start publishing only temperature by default
- On receiving `{"addMetrics": ["humidity", "engine_rpm"]}`, start publishing those too
- Data generation:
  - temperature: ~22°C ± 3°C (existing)
  - humidity: ~55% ± 10%
  - engine_rpm: ~2500 ± 500
- Single JSON payload with all enabled metrics: `{"temperature": 22.1, "humidity": 54.3, "engine_rpm": 2480}`
- Print log when config received, showing newly enabled metrics
- Support `--all-metrics` CLI flag to start with all metrics enabled (for quick testing)

## Step 16: Backend Tests

**Create `backend/tests/test_admin_orgs.py`:**
- test_create_org (admin) — 201
- test_create_org_duplicate_name — 409
- test_list_orgs (admin sees all) — 200
- test_update_org — 200
- test_delete_org — 204
- test_viewer_cannot_access_admin — 403

**Create `backend/tests/test_admin_users.py`:**
- test_create_user — 201
- test_create_user_duplicate_email — 409
- test_list_users_filter_by_org — 200
- test_update_user — 200
- test_deactivate_user — 200
- test_viewer_cannot_create_user — 403

**Create `backend/tests/test_admin_devices.py`:**
- test_provision_device_auto_code — 201, device_code is generated
- test_provision_device_manual_code — 201, device_code matches input
- test_provision_device_duplicate_code — 409
- test_provision_device_with_metrics — 201, metrics linked
- test_provision_device_auto_enable — 201, MQTT publisher called
- test_update_device — 200
- test_update_device_metrics — 200
- test_send_device_config — 200, MQTT publisher called with correct metrics
- test_delete_device — 204
- test_viewer_cannot_provision — 403

**Create `backend/tests/test_metrics.py`:**
- test_list_metrics — 200, returns seeded metrics
- test_device_metrics — returns enabled metrics for device

**Update `backend/tests/conftest.py`:**
- Add `mock_mqtt` fixture (MagicMock for MqttPublisher)
- Add `admin_client_b` fixture (admin for org B, for cross-org admin tests)
- Add metric seed data to fixtures
- Override `get_mqtt_publisher` dependency

**Estimated test count:** ~20 new tests → ~62 total backend tests

## Step 17: Documentation

- `docs/SPRINT-3-DECISIONS.md` — technical decisions (admin role guard, metrics catalog, parametric dashboard, MQTT publisher, UID auto-gen, DeviceMetric model)
- `docs/SPRINT-3-FEATURES.md` — features delivered, business value, gaps remaining
- `docs/SPRINT-3-MANUAL-QA.md` — QA checklist (~20 steps)

---

## Files Created (~18)

### Backend
- `backend/alembic/versions/002_metrics_and_device_metrics.py`
- `backend/app/services/mqtt_publisher.py`
- `backend/app/routers/metrics.py`
- `backend/app/routers/admin_orgs.py`
- `backend/app/routers/admin_users.py`
- `backend/app/routers/admin_devices.py`
- `backend/tests/test_admin_orgs.py`
- `backend/tests/test_admin_users.py`
- `backend/tests/test_admin_devices.py`
- `backend/tests/test_metrics.py`

### Frontend
- `frontend/src/hooks/useAdmin.ts`
- `frontend/src/routes/_authenticated/admin.tsx` (layout guard)
- `frontend/src/routes/_authenticated/admin/index.tsx`
- `frontend/src/routes/_authenticated/admin/organisations.tsx`
- `frontend/src/routes/_authenticated/admin/users.tsx`
- `frontend/src/routes/_authenticated/admin/devices.tsx`

### Grafana
- `grafana/provisioning/dashboards/iot-metrics.json` (replaces temperature.json)

### Docs
- `docs/SPRINT-3-DECISIONS.md`
- `docs/SPRINT-3-FEATURES.md`
- `docs/SPRINT-3-MANUAL-QA.md`

## Files Modified (~12)

- `backend/requirements.txt` — add paho-mqtt
- `backend/app/config.py` — MQTT broker settings
- `backend/app/models.py` — Metric + DeviceMetric models, Device.device_metrics relationship
- `backend/app/schemas.py` — admin + metrics schemas
- `backend/app/main.py` — register new routers
- `backend/app/seed.py` — metrics seed, device-metric links, dashboard UID update
- `backend/tests/conftest.py` — mqtt mock, metric fixtures, admin fixtures
- `docker-compose.yml` — MQTT env vars for backend
- `frontend/src/types/api.ts` — new TypeScript types
- `frontend/src/components/Layout.tsx` — Admin nav link
- `frontend/src/routes/_authenticated/dashboard/$deviceId.tsx` — multi-metric embeds + selector
- `fake_device.py` — multi-metric + config listener
- `grafana/provisioning/dashboards/dashboards.yaml` — update dashboard file reference

## Files Deleted (1)

- `grafana/provisioning/dashboards/temperature.json` (replaced by iot-metrics.json)

---

## Verification

1. `docker compose down -v && docker compose up --build -d` — 8 services start
2. `docker compose exec backend alembic upgrade head` — migrations 001 + 002 run
3. `docker compose exec backend python -m app.seed` — seeds 2 orgs, 2 users, 3 devices, 2 alerts, **3 metrics**, device-metric links
4. Login as `admin@democorp.com` → header shows "Admin" nav link
5. Login as `viewer@acmeiot.com` → no "Admin" link visible
6. Admin: navigate to `/admin/devices` → see sensor01, sensor02 with temperature metric badge
7. Admin: click "Provision Device" → fill form with name "Humidity Sensor", auto-generate UID, select temperature + humidity, check auto-enable → creates device, MQTT message sent
8. `python fake_device.py` → starts with temperature → receives config → starts sending humidity too
9. Navigate to `/dashboard/{new_device_id}` → see two iframes: temperature graph + humidity graph
10. Click metric selector → deselect temperature → only humidity graph shown
11. Admin: click "Re-send Config" on a device → MQTT message re-published
12. Admin: create new org "Beta Corp" → add user → add device → login as new user → see empty dashboard
13. `docker compose run --rm --no-deps backend pytest -v` — ~62 tests pass
14. `docker compose exec frontend npm test` — frontend tests pass

---

## Sprint Review Deliverable

Admin provisions new device "Humidity Sensor" with temperature + humidity metrics → auto-enable sends MQTT config → fake device starts sending both metrics → dashboard shows two live graphs → admin creates org "Beta Corp", adds user, adds device → logs in as that user → sees their own dashboard. Full client onboarding in under 10 minutes.
