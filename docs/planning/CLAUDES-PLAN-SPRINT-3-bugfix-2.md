# Sprint 3 Bugfix 2 — Plan

## Overview

Nine changes: **1) data model restructure** (device types + allowed metrics) — implemented first since items 2, 7, 8, and 9 depend on it — then 2) incremental MQTT metric config, 3) visible auto-generated UID, 4) Platform org exclusion from user creation, 5) admin-grade "Devices" page for admins, 6) filter placement fix, 7) device type dropdown from config, 8) inline device editing, and 9) dynamic alert metric selection.

---

## 1. Data Model Restructure — Device Types + Allowed Metrics

### Problem

Only having device-level metrics is not enough — there's no constraint on what a device _should_ support. Only having global metrics is too loose — any metric could be assigned anywhere. We need both:

- **Allowed metrics per device type** — what a device model is capable of
- **Enabled metrics per provisioned device** — what's actually turned on for a specific deployed device

The key invariant: **`device_provisioned_metrics ⊆ device_type_metrics`** — a provisioned device can only enable metrics that its type supports.

### Current State

| Table | Purpose | Problem |
|-------|---------|---------|
| `devices` | Actual deployed devices | `device_type` is a free-text VARCHAR, no FK |
| `metrics` | Global metric catalog | Fine as-is |
| `device_metrics` | Links devices to metrics | No validation that the metric is valid for the device's type |

No concept of "device type" as a first-class entity. No way to define which metrics a type supports.

### Target Schema

**5 tables (2 new, 2 renamed, 1 unchanged):**

#### `device_types` (NEW)
Device models/categories the company manages. Replaces the free-text `device_type` string.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | PK |
| `name` | VARCHAR(100) | Unique, e.g. "temperature_sensor", "hvac_unit" |
| `description` | TEXT | Nullable |
| `created_at` | TIMESTAMPTZ | server default now() |

#### `device_type_metrics` (NEW)
Defines which metrics a device type supports. Prevents invalid metric assignments.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | PK |
| `device_type_id` | UUID | FK → `device_types.id` |
| `metric_id` | UUID | FK → `metrics.id` |
| | | Unique constraint on (device_type_id, metric_id) |

#### `devices` → `devices_provisioned` (RENAME)
Actual devices assigned to clients. FK to `device_types` instead of free-text string.

| Column | Change |
|--------|--------|
| `device_type` (VARCHAR) | **Remove** |
| `device_type_id` (UUID) | **Add** — FK → `device_types.id`, NOT NULL |

Table renamed from `devices` to `devices_provisioned`.

#### `device_metrics` → `device_provisioned_metrics` (RENAME)
Which metrics are enabled on a specific deployed device. Subset of what the device type allows.

| Column | Change |
|--------|--------|
| `device_id` | FK → `devices_provisioned.id` (updated reference) |

Table renamed from `device_metrics` to `device_provisioned_metrics`.

#### `metrics` (UNCHANGED)
Global catalog stays as-is.

### Migration Plan

**Alembic migration `003_device_types_restructure.py`:**

1. Create `device_types` table
2. Populate `device_types` from `SELECT DISTINCT device_type FROM devices` (migrate existing data)
3. Create `device_type_metrics` table
4. Populate `device_type_metrics` from existing device_metrics joins (for each device type, collect all metrics that any device of that type currently uses)
5. Add `device_type_id` column to `devices` (nullable initially)
6. Backfill `device_type_id` from the name mapping
7. Make `device_type_id` NOT NULL, add FK constraint
8. Drop old `device_type` VARCHAR column from `devices`
9. Rename table `devices` → `devices_provisioned`
10. Rename table `device_metrics` → `device_provisioned_metrics`
11. Update FK references in `alerts` table (`devices.id` → `devices_provisioned.id`)

### Backend Changes

**`backend/app/models.py`** — Major restructure:
- Add `DeviceType` model (table `device_types`)
- Add `DeviceTypeMetric` model (table `device_type_metrics`) with relationships to `DeviceType` and `Metric`
- Rename `Device` model's `__tablename__` to `"devices_provisioned"`
- Replace `device_type: str` with `device_type_id: UUID` FK → `device_types.id`
- Add `device_type` relationship on Device → DeviceType
- Rename `DeviceMetric` model's `__tablename__` to `"device_provisioned_metrics"`
- Update `Metric.device_metrics` relationship name → `device_provisioned_metrics`
- Update all back_populates references

**`backend/app/schemas.py`**:
- Add `DeviceTypeOut(id, name, description)`
- Add `DeviceTypeCreate(name, description, metric_ids)`
- Update `DeviceCreate.device_type` → `device_type_id: uuid.UUID`
- Update `DeviceOut` and `DeviceAdminOut` to include `device_type_id` + `device_type_name` (resolved via relationship)
- Update `DeviceUpdate.device_type` → `device_type_id: uuid.UUID | None`

**`backend/app/routers/admin_devices.py`**:
- `GET /api/admin/devices/device-types` — now queries `DeviceType` table instead of `DISTINCT` on string column
- `POST /api/admin/devices` (provision) — validate `device_type_id` exists, validate `metric_ids ⊆ device_type_metrics` for that type
- `PATCH /{device_id}/metrics` — validate new metric_ids are all in `device_type_metrics` for the device's type
- `list_devices` filter — `device_type` query param becomes `device_type_id`

**New router: `backend/app/routers/admin_device_types.py`** (or add to existing admin_devices):
- `GET /api/admin/device-types` — list all device types with their allowed metrics
- `POST /api/admin/device-types` — create device type + link allowed metrics
- `PUT /api/admin/device-types/{id}` — update name/description/allowed metrics
- `DELETE /api/admin/device-types/{id}` — delete (blocked if provisioned devices reference it)

**`backend/app/seed.py`**:
- Create `DeviceType` records (e.g. "temperature_sensor" supports [temperature, humidity])
- Create `DeviceTypeMetric` links
- Update device creation to use `device_type_id` FK instead of string

**`backend/app/routers/alerts.py`**:
- Update model imports (FK table name change)
- Alert metric validation (from item 9) now also validates against `device_type_metrics`

**Validation rule (critical):**
```python
# On device metric assignment (provision or update):
allowed = set(
    db.query(DeviceTypeMetric.metric_id)
    .filter(DeviceTypeMetric.device_type_id == device.device_type_id)
    .all()
)
requested = set(body.metric_ids)
if not requested.issubset(allowed):
    invalid = requested - allowed
    raise HTTPException(400, f"Metrics {invalid} not supported by this device type")
```

### Frontend Changes

**`frontend/src/types/api.ts`**:
- Add `DeviceType { id, name, description }`
- Update `DeviceAdmin.device_type` → `device_type_id` + `device_type_name`
- Update `DeviceCreate.device_type` → `device_type_id`
- Update `DeviceUpdate.device_type` → `device_type_id`

**`frontend/src/hooks/useAdmin.ts`**:
- `useDeviceTypes()` now returns `DeviceType[]` objects (not `string[]`)
- Add `useCreateDeviceType()`, `useUpdateDeviceType()`, `useDeleteDeviceType()` mutations

**`frontend/src/routes/_authenticated/admin/devices.tsx`**:
- Device type filter dropdown uses `DeviceType.id` as value (not string)
- Device type in create form uses `device_type_id` select from `DeviceType` objects
- Inline edit device type dropdown uses same
- Metric checkboxes in create form: filter to only show metrics allowed by selected device type

**Admin device types management page** (new, optional — could be deferred):
- `frontend/src/routes/_authenticated/admin/device-types.tsx`
- CRUD for device types with allowed metrics configuration

### Impact on Other Plan Items

| Item | Impact |
|------|--------|
| Item 2 (Incremental MQTT) | No change — operates on provisioned metric IDs regardless of schema |
| Item 7 (Device type dropdown) | Now uses `DeviceType` objects from DB table, not distinct strings |
| Item 8 (Inline device edit) | Device type field becomes FK dropdown to `device_types` |
| Item 9 (Alert metrics) | Validation can additionally check `device_type_metrics` |

### Files

| File | Change |
|------|--------|
| `backend/app/models.py` | Add DeviceType, DeviceTypeMetric; rename tables; FK restructure |
| `backend/app/schemas.py` | DeviceTypeOut/Create; update Device schemas for FK |
| `backend/app/routers/admin_devices.py` | Validate metrics ⊆ device_type_metrics; update queries |
| `backend/app/routers/admin_device_types.py` | NEW — CRUD for device types |
| `backend/app/routers/alerts.py` | Update imports for renamed models |
| `backend/app/routers/devices.py` | Update imports for renamed models |
| `backend/app/routers/organisations.py` | Update imports for renamed models |
| `backend/app/services/grafana_client.py` | Update imports for renamed models |
| `backend/app/main.py` | Register new admin_device_types router |
| `backend/app/seed.py` | Seed device types + device_type_metrics |
| `backend/alembic/versions/003_*.py` | Migration: new tables, rename, data backfill |
| `backend/tests/conftest.py` | Update model imports + seed fixtures |
| `backend/tests/test_admin_devices.py` | Update for device_type_id FK |
| `frontend/src/types/api.ts` | DeviceType interface; update Device types |
| `frontend/src/hooks/useAdmin.ts` | useDeviceTypes returns objects; add CRUD hooks |
| `frontend/src/routes/_authenticated/admin/devices.tsx` | Device type FK dropdown; metric filtering by type |

---

## 2. Incremental MQTT Metric Add/Remove

### Problem

When metrics are added or removed from a device, the backend deletes all `DeviceMetric` rows and re-inserts the new set, then sends the full list via `{"addMetrics": [...]}`. The device only needs to know what changed — which metrics were added and which were removed.

### Current Flow

- `PATCH /api/admin/devices/{id}/metrics` — deletes all, re-inserts from `metric_ids` body
- `MqttPublisher.send_device_config()` — sends `{"addMetrics": metrics}` with the full new list
- `fake_device.py` — only handles `addMetrics` key, no support for `removeMetrics`

### Plan

**`backend/app/routers/admin_devices.py`** — `update_device_metrics` endpoint

- Before deleting, query existing enabled metric IDs into a set: `old_ids`
- Compute `new_ids` from `body.metric_ids`
- Compute `added = new_ids - old_ids` and `removed = old_ids - new_ids`
- Still do the full replacement in DB (delete all + re-insert) — this is the simplest correct approach
- When `send_config=True`, call two MQTT methods instead of one:
  - If `added`: send `{"addMetrics": [names...]}`
  - If `removed`: send `{"removeMetrics": [names...]}`

**`backend/app/services/mqtt_publisher.py`**

- Add `send_device_config_remove(device_code, metrics)` method
  - Publishes `{"removeMetrics": metrics}` to `{device_code}/to/config`
- Keep existing `send_device_config` for add (rename concept to `send_metrics_add` internally or keep name — either way the payload stays `{"addMetrics": [...]}`)

**`fake_device.py`**

- Add handler for `"removeMetrics"` key in `on_message`:
  ```python
  if "removeMetrics" in payload:
      for m in payload["removeMetrics"]:
          enabled_metrics.discard(m)
      print(f"  CONFIG received: disabled {payload['removeMetrics']}  (active: {sorted(enabled_metrics)})")
  ```

### Files

| File                                     | Change                                                  |
| ---------------------------------------- | ------------------------------------------------------- |
| `backend/app/routers/admin_devices.py`   | Diff old vs new metric IDs, send incremental add/remove |
| `backend/app/services/mqtt_publisher.py` | Add `send_device_config_remove()` method                |
| `fake_device.py`                         | Handle `removeMetrics` in config messages               |

---

## 3. Auto-Generated UID Visible (Greyed Out)

### Problem

When "Auto-generate device UID" is checked, the UID field disappears entirely. The user can't see the generated UID until after submission. It should remain visible but greyed out, showing that it will be auto-generated.

### Plan

**`frontend/src/routes/_authenticated/admin/devices.tsx`**

- When `autoCode` is true: show the device code input field as **disabled** with placeholder text "Auto-generated on save" and grey styling (`bg-gray-100 text-gray-400`)
- When `autoCode` is false: show the input field as normal (editable)
- Remove the conditional hide (`{!autoCode && ...}`) and replace with always-shown input that toggles `disabled` based on `autoCode`

### Files

| File                                                   | Change                                                            |
| ------------------------------------------------------ | ----------------------------------------------------------------- |
| `frontend/src/routes/_authenticated/admin/devices.tsx` | Always show UID input, disable+grey when auto-generate is checked |

---

## 4. Exclude Platform Org from User Creation Dropdown

### Problem

The "Create User" form shows all organisations in the dropdown, including "Platform". Platform is reserved for admin users only — client users should never be assigned to it.

### Plan

**Option A — Frontend filter (simpler, chosen):**

**`frontend/src/routes/_authenticated/admin/users.tsx`**

- Filter the `orgs` list in the create user form dropdown to exclude any org named "Platform"
- `{orgs?.filter(o => o.name !== 'Platform').map(...)}`
- The list/filter view of users can still show Platform org users (admins) — just can't create new ones there

**Why not backend:** A backend endpoint change (e.g. `GET /api/admin/organisations?exclude_platform=true`) adds unnecessary complexity. The Platform org name is stable and known. If it needs to change later, a single constant update is simpler.

### Files

| File                                                 | Change                                             |
| ---------------------------------------------------- | -------------------------------------------------- |
| `frontend/src/routes/_authenticated/admin/users.tsx` | Filter "Platform" from org dropdown in create form |

---

## 5. Admin Sees All Devices from "Devices" Top Menu (with Filters)

### Problem

When an admin clicks "Devices" in the top nav, they see `/dashboard` which calls `GET /api/devices` — scoped to their own org (Platform). Since Platform has no devices, they see nothing. Admins should see all devices across all clients with the same filters available on the admin devices page.

### Plan

**`frontend/src/routes/_authenticated/dashboard/index.tsx`**

- Check `user.role === 'admin'`
- If admin: render the admin-style devices table (with org, device type, metric filters) using `useAdminDevices` + `useDeviceTypes` + `useMetrics` + `useAdminOrgs` hooks
- If viewer: keep existing card grid with `useDevices()` (org-scoped, no filters)
- Admin views devices on this page as **read-only** (no provision/delete/metrics buttons) — just a view of all devices with filters and a link to device dashboard page for metrics vieweing.
- Each device row links to the device detail page (`/dashboard/{deviceId}`)

**`frontend/src/hooks/useDevices.ts`**

- No changes needed — admin will use `useAdminDevices` from `useAdmin.ts`

**Alternative considered:** Redirect admin's "Devices" link to `/admin/devices`. Rejected because the top-level "Devices" page should be a viewing experience (with drill-down to Grafana embeds), not the admin provisioning page.

### Files

| File                                                     | Change                                                     |
| -------------------------------------------------------- | ---------------------------------------------------------- |
| `frontend/src/routes/_authenticated/dashboard/index.tsx` | Admin gets table view with filters; viewer keeps card grid |

---

## 6. Filters Below Provisioning Form

### Problem

On the admin devices page, the filter dropdowns are above the "Provision New Device" form. When the form is open, filters should be below it so the provisioning form doesn't push filters out of view.

### Plan

**`frontend/src/routes/_authenticated/admin/devices.tsx`**

- Move the filter `<div>` (containing org, device type, metric dropdowns) to be **after** the `{showCreate && ...}` block
- Order becomes: header → provision button → create form (when open) → filters → devices table

### Files

| File                                                   | Change                                  |
| ------------------------------------------------------ | --------------------------------------- |
| `frontend/src/routes/_authenticated/admin/devices.tsx` | Move filter div below create form block |

---

## 7. Device Type as Dropdown from Config

### Problem

Device type in the provisioning form is a free-text input. Should be a dropdown populated from existing device types.
There will be no option to create new one. With item 1's data model restructure, `GET /api/admin/device-types` returns `DeviceType` objects from the database table.

### Plan

**`frontend/src/routes/_authenticated/admin/devices.tsx`**

- Replace the device type `<input type="text">` with a `<select>` dropdown
- Populate from `useDeviceTypes()` hook (now returns `DeviceType[]` objects from item 1)
- Use `device_type_id` as the select value
- Default selection: first available type
- When device type changes, filter available metric checkboxes to only show metrics allowed by the selected type (via `device_type_metrics`)

**Backend already handled by item 1** — `GET /api/admin/device-types` returns device types with their allowed metrics.

### Files

| File                                                   | Change                                                  |
| ------------------------------------------------------ | ------------------------------------------------------- |
| `frontend/src/routes/_authenticated/admin/devices.tsx` | Replace device type text input with FK dropdown from DB |

---

## 8. Inline Device Editing from Admin

### Problem

Admin devices page has no UI for editing device fields (name, type, active status). The `PUT /api/admin/devices/{id}` endpoint exists and accepts `name`, `device_type`, `is_active` — but there's no frontend form to use it.

### Plan

**`frontend/src/routes/_authenticated/admin/devices.tsx`**

- Add an "Edit" button per device row (next to Metrics / Re-send / Delete)
- Clicking "Edit" opens inline editing on that row (similar pattern to users page):
  - Name: text input (pre-filled)
  - Device type: dropdown (using `useDeviceTypes()`, same as create form — uses `device_type_id` from item 1)
  - Active: checkbox
- "Save" calls `useUpdateDevice` mutation; "Cancel" reverts
- Add state: `editDeviceId`, `editDeviceForm`

### Files

| File                                                   | Change                                                        |
| ------------------------------------------------------ | ------------------------------------------------------------- |
| `frontend/src/routes/_authenticated/admin/devices.tsx` | Add inline edit mode for device name, type, and active status |

---

## 9. Alert Metric Dropdown from Device's Enabled Metrics

### Problem

Alert creation (`/alerts/new`) and editing (`/alerts/{id}/edit`) have a hardcoded metric dropdown with only `<option value="temperature">Temperature</option>`. Users should be able to create alerts for any metric enabled on the selected device.

### Current State

- `alerts/new.tsx` line 78: hardcoded `<option value="temperature">`
- `alerts/$alertId.edit.tsx` line 89: hardcoded `<option value="temperature">`
- Backend `POST /api/alerts`: no validation that the metric exists on the device
- `GET /api/devices/{id}/metrics` already returns enabled metrics for a device

### Plan

**`frontend/src/hooks/useDevices.ts`**

- Add `useDeviceMetrics(deviceId)` hook — calls `GET /api/devices/{deviceId}/metrics`
- Returns `DeviceMetric[]` with `metric_name`, `metric_unit`, etc.

**`frontend/src/routes/_authenticated/alerts/new.tsx`**

- When user selects a device, fetch that device's metrics via `useDeviceMetrics(deviceId)`
- Replace hardcoded metric `<select>` with dynamic one populated from device metrics
- If device has no metrics, show disabled dropdown with "No metrics configured"
- Reset metric selection when device changes
- Default to first available metric

**`frontend/src/routes/_authenticated/alerts/$alertId.edit.tsx`**

- Fetch the alert's device metrics using `useDeviceMetrics(alert.device_id)` (device_id from alert, need to add it to the component — it's available via `alert.device_id`)
- Replace hardcoded metric `<select>` with dynamic one
- Pre-select the alert's current metric

**`backend/app/routers/alerts.py`** — `create_alert` endpoint (optional but recommended)

- After verifying device ownership, validate that `body.metric` matches an enabled metric on the device:
  ```python
  dm = db.query(DeviceMetric).join(Metric).filter(
      DeviceMetric.device_id == body.device_id,
      Metric.name == body.metric,
      DeviceMetric.is_enabled.is_(True),
  ).first()
  if not dm:
      raise HTTPException(status_code=400, detail="Metric not enabled on this device")
  ```
- Same validation in `update_alert` if metric field is being changed

### Files

| File                                                          | Change                                                |
| ------------------------------------------------------------- | ----------------------------------------------------- |
| `frontend/src/hooks/useDevices.ts`                            | Add `useDeviceMetrics(deviceId)` hook                 |
| `frontend/src/routes/_authenticated/alerts/new.tsx`           | Dynamic metric dropdown from device's enabled metrics |
| `frontend/src/routes/_authenticated/alerts/$alertId.edit.tsx` | Dynamic metric dropdown from device's enabled metrics |
| `backend/app/routers/alerts.py`                               | Validate metric exists on device (create + update)    |

---

## Files Summary

| File                                                          | Changes                                                                |
| ------------------------------------------------------------- | ---------------------------------------------------------------------- |
| `backend/app/models.py`                                       | Add DeviceType, DeviceTypeMetric; rename tables; FK restructure        |
| `backend/app/schemas.py`                                      | DeviceTypeOut/Create; update Device schemas for FK                     |
| `backend/app/routers/admin_devices.py`                        | Validate metrics ⊆ device_type_metrics; incremental MQTT diff          |
| `backend/app/routers/admin_device_types.py`                   | NEW — CRUD for device types + allowed metrics                          |
| `backend/app/routers/alerts.py`                               | Validate metric enabled on device; update imports                      |
| `backend/app/routers/devices.py`                              | Update imports for renamed models                                      |
| `backend/app/routers/organisations.py`                        | Update imports for renamed models                                      |
| `backend/app/services/grafana_client.py`                      | Update imports for renamed models                                      |
| `backend/app/services/mqtt_publisher.py`                      | Add `send_device_config_remove()` method                               |
| `backend/app/main.py`                                         | Register admin_device_types router                                     |
| `backend/app/seed.py`                                         | Seed device types + device_type_metrics                                |
| `backend/alembic/versions/003_*.py`                           | Migration: new tables, rename, data backfill                           |
| `backend/tests/conftest.py`                                   | Update model imports + seed fixtures for device types                  |
| `backend/tests/test_admin_devices.py`                         | Update for device_type_id FK                                           |
| `fake_device.py`                                              | Handle `removeMetrics` config messages                                 |
| `frontend/src/types/api.ts`                                   | DeviceType interface; update Device types for FK                       |
| `frontend/src/hooks/useAdmin.ts`                              | useDeviceTypes returns objects; add device type CRUD hooks             |
| `frontend/src/hooks/useDevices.ts`                            | Add `useDeviceMetrics()` hook                                          |
| `frontend/src/routes/_authenticated/admin/devices.tsx`        | UID visibility, filter placement, device type FK dropdown, inline edit |
| `frontend/src/routes/_authenticated/admin/users.tsx`          | Filter Platform from org dropdown                                      |
| `frontend/src/routes/_authenticated/dashboard/index.tsx`      | Admin gets filtered table view of all devices                          |
| `frontend/src/routes/_authenticated/alerts/new.tsx`           | Dynamic metric dropdown per device                                     |
| `frontend/src/routes/_authenticated/alerts/$alertId.edit.tsx` | Dynamic metric dropdown per device                                     |

---

## Verification

1. **Data model migration**: `docker compose exec backend alembic upgrade head` — migration 003 runs, tables renamed, device_types populated from existing data
2. **Device types CRUD**: `GET /api/admin/device-types` returns device types with their allowed metrics
3. **Device type constraint**: Try to assign a metric not in `device_type_metrics` → 400 error "Metrics not supported by this device type"
4. **Incremental MQTT**: Change device metrics (add humidity, remove temperature) → fake_device log shows `removeMetrics: ["temperature"]` then `addMetrics: ["humidity"]` — not the full list
5. **UID visibility**: Open provision form → auto-generate checked → greyed-out UID field visible with placeholder
6. **Platform exclusion**: Open create user form → org dropdown does NOT show "Platform"
7. **Admin devices view**: Login as admin → click "Devices" in top nav → see all devices from all orgs with filter dropdowns
8. **Filter placement**: Open provision form → filters are below it, not above
9. **Device type dropdown**: In provision form → device type is a dropdown from `device_types` table, not free text
10. **Metric filtering by type**: In provision form → select device type → metric checkboxes show only metrics allowed by that type
11. **Inline device edit**: On admin devices page → click "Edit" on a device → edit name/type/active inline
12. **Alert metrics**: Create new alert → select a device → metric dropdown shows only that device's enabled metrics
13. **Alert metric validation**: Try `POST /api/alerts` with a metric not on the device → 400 error
14. **Tests**: `docker compose exec backend python -m pytest tests/ -v` — all pass
15. **Seed data**: Fresh `docker compose down -v && docker compose up` → device types seeded, devices link to types via FK
