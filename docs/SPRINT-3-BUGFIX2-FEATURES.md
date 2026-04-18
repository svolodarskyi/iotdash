# Sprint 3 Bugfix 2 — Features Delivered

## Accomplished

### 1. Data Model Restructure — Device Types as First-Class Entity
- **`device_types` table** — catalog of device models (e.g. `temperature_sensor`, `engine_monitor`) with name, description
- **`device_type_metrics` table** — defines allowed metrics per device type (e.g. temperature_sensor supports temperature + humidity)
- **Table renames** — `devices` → `devices_provisioned`, `device_metrics` → `device_provisioned_metrics`
- **FK constraint** — `device_type` free-text string replaced with `device_type_id` UUID FK to `device_types`
- **Alembic migration 003** — creates new tables, backfills from existing data, renames tables, updates FKs
- **Metric subset validation** — provisioning or updating device metrics checks `requested ⊆ device_type_metrics`; HTTP 400 on violation

### 2. Incremental MQTT Metric Add/Remove
- **Diff computation** — backend computes added/removed metrics before sending MQTT
- **Separate MQTT messages** — `{"addMetrics": [...]}` for additions, `{"removeMetrics": [...]}` for removals
- **`send_device_config_remove()`** — new method on MqttPublisher for remove messages
- **fake_device.py** — handles `removeMetrics` key, removes metrics from active set

### 3. Auto-Generated UID Visible (Greyed Out)
- **Always-visible UID field** — when auto-generate is checked, input shows disabled with placeholder "Auto-generated on save"
- **Grey styling** — `bg-gray-100 text-gray-400` makes it clear the field is auto-managed
- **Editable when manual** — unchecking auto-generate enables the field for manual entry

### 4. Platform Org Excluded from User Creation
- **Frontend filter** — Platform organisation hidden from the org dropdown in the create user form
- **Still visible in list** — admin users in Platform org are shown in the users table (read-only info)
- **No backend change** — simple `o.name !== 'Platform'` filter in the component

### 5. Admin Sees All Devices from "Devices" Top Menu
- **Role-based view** — `/dashboard` detects `user.role === 'admin'` and renders admin table vs viewer cards
- **All devices from all orgs** — admin view uses `useAdminDevices` hook showing every device across tenants
- **Three-way filtering** — organisation, device type, and metric type filter dropdowns (AND logic)
- **Read-only with drill-down** — each row links to the device's Grafana dashboard page, no provisioning controls
- **Viewer unchanged** — non-admin users see the existing card grid scoped to their org

### 6. Filter Placement Fix
- **Filters below form** — on the admin devices page, filter dropdowns moved below the "Provision New Device" form
- **Layout order** — header → provision button → create form (when open) → filters → devices table

### 7. Device Type as Dropdown from Config
- **`<select>` from database** — device type field in create form is a dropdown populated from `GET /api/admin/device-types`
- **`DeviceType` objects** — dropdown shows name, uses `device_type_id` as value
- **Metric filtering** — changing device type filters available metric checkboxes to only show allowed metrics for that type
- **No free-text** — impossible to enter an unrecognized device type

### 8. Inline Device Editing from Admin
- **Edit button per row** — "Edit" action on each device in the admin devices table
- **Inline editing** — name (text input), device type (dropdown), active (checkbox) — all editable in-place
- **Save/Cancel** — "Save" calls `PUT /api/admin/devices/{id}`, "Cancel" reverts to read-only
- **Type change awareness** — changing device type during edit uses the same `DeviceType` dropdown as create

### 9. Alert Metric Dropdown from Device's Enabled Metrics
- **Dynamic metric dropdown** — `/alerts/new` and `/alerts/{id}/edit` fetch device's enabled metrics via `useDeviceMetrics(deviceId)`
- **Device-change reset** — selecting a different device resets metric to first available
- **Disabled states** — "Select a device first" or "No metrics configured" shown when appropriate
- **Backend validation** — `POST /api/alerts` and `PUT /api/alerts/{id}` reject metrics not enabled on the device (HTTP 400)

### Device Types CRUD (Admin API)
- **`GET /api/admin/device-types`** — list all device types with allowed metrics
- **`POST /api/admin/device-types`** — create device type with name, description, metric_ids
- **`PUT /api/admin/device-types/{id}`** — update name, description, or allowed metrics
- **`DELETE /api/admin/device-types/{id}`** — delete (blocked if devices reference it, HTTP 400)

### Testing
- **88 total backend tests** — all passing, up from 78 in Sprint 3 Bugfix 1
- **10 new tests added:**
  - `test_provision_device_invalid_metric_for_type` — metric not in device type → 400
  - `test_update_device_type` — change device type via API
  - `test_update_device_metrics_invalid_for_type` — update metrics outside type → 400
  - `test_update_device_metrics_incremental_mqtt` — verify add MQTT sent for new metrics
  - `test_update_device_metrics_incremental_mqtt_remove` — verify remove MQTT sent for dropped metrics
  - `test_list_device_types_crud` — list device types returns seeded types
  - `test_create_device_type` — create new type with metrics
  - `test_create_device_type_duplicate` — duplicate name → 400
  - `test_delete_device_type_blocked_by_devices` — type in use → 400
  - `test_delete_device_type_no_devices` — unused type → deleted successfully

### Seed Data Updates
- **Device types seeded** — `temperature_sensor` (temperature + humidity), `engine_monitor` (engine_rpm + temperature)
- **Devices use FK** — all seeded devices reference `device_type_id` instead of string
- **Seed output** — shows device types and metrics alongside orgs, users, and devices

## Business Value
- **Data integrity** — device types define allowed metrics; impossible to assign sensors that don't exist on a device model
- **Operator clarity** — metric checkboxes filtered by device type means admins only see relevant options
- **Efficient device updates** — incremental MQTT means firmware only processes changes, not full reconfiguration
- **Self-service alerts** — users pick from available metrics per device, eliminating invalid alert configurations
- **Admin overview** — platform admins see all devices from top nav without navigating to the provisioning page

## Gaps Remaining
- **No device types management UI** — device types created via seed or API only; no admin page for CRUD (API exists, frontend page deferred)
- **No metric creation UI** — admin can only use seeded metrics
- **No bulk device import** — devices provisioned one at a time
- **No device search/pagination** — filtering helps but doesn't scale to thousands
- **No Grafana org cleanup on org delete** — deleting a Postgres org does not remove the Grafana org
