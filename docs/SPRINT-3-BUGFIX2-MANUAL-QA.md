# Sprint 3 Bugfix 2 — Manual QA Checklist

## Prerequisites
- Docker and Docker Compose installed
- Fresh database (run `docker compose down -v` first)

## QA Steps

### 1. All services start with updated seed
```bash
docker compose down -v
docker compose up --build -d
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.seed
```
- [ ] 8 services running: emqx, telegraf, influxdb, grafana, postgres, backend, frontend, mailhog
- [ ] Migration 003 runs: "Device types restructure"
- [ ] Seed output shows **3 orgs**: Platform, Demo Corp, Acme IoT
- [ ] Seed output shows **2 device types**: temperature_sensor, engine_monitor
- [ ] Seed output shows **3 metrics**: temperature, humidity, engine_rpm
- [ ] Seed output shows admin user: `admin@iotdash.com`
- [ ] Seed output shows Demo Corp viewer: `viewer@democorp.com`
- [ ] Seed output shows Acme IoT viewer: `viewer@acmeiot.com`

### 2. Backend tests pass
```bash
docker compose exec backend python -m pytest tests/ -v
```
- [ ] **88 tests pass** (up from 78 in Bugfix 1)
- [ ] New tests included:
  - `test_provision_device_invalid_metric_for_type`
  - `test_update_device_type`
  - `test_update_device_metrics_invalid_for_type`
  - `test_update_device_metrics_incremental_mqtt`
  - `test_update_device_metrics_incremental_mqtt_remove`
  - `test_list_device_types_crud`
  - `test_create_device_type`
  - `test_create_device_type_duplicate`
  - `test_delete_device_type_blocked_by_devices`
  - `test_delete_device_type_no_devices`

---

## Data Model Restructure

### 3. Device types API
```bash
# Login as admin
curl -s -c cookies.txt -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@iotdash.com","password":"admin123"}'

# List device types
curl -s -b cookies.txt http://localhost:8000/api/admin/device-types | python3 -m json.tool
```
- [ ] Returns 2 device types: `temperature_sensor` and `engine_monitor`
- [ ] `temperature_sensor` has allowed_metrics: temperature (°C), humidity (%)
- [ ] `engine_monitor` has allowed_metrics: engine_rpm (rpm), temperature (°C)

### 4. Device type metric constraint — provision
```bash
# Get IDs
TEMP_TYPE_ID=$(curl -s -b cookies.txt http://localhost:8000/api/admin/device-types | python3 -c 'import json,sys;[print(t["id"]) for t in json.load(sys.stdin) if t["name"]=="temperature_sensor"]')
RPM_METRIC_ID=$(curl -s -b cookies.txt http://localhost:8000/api/admin/device-types | python3 -c 'import json,sys;[print(m["metric_id"]) for t in json.load(sys.stdin) for m in t["allowed_metrics"] if m["metric_name"]=="engine_rpm"]')
ORG_ID=$(curl -s -b cookies.txt http://localhost:8000/api/admin/organisations | python3 -c 'import json,sys;[print(o["id"]) for o in json.load(sys.stdin) if o["name"]=="Demo Corp"]')

# Try to assign engine_rpm to a temperature_sensor device
curl -s -b cookies.txt -X POST http://localhost:8000/api/admin/devices \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Bad Device\",\"organisation_id\":\"$ORG_ID\",\"device_type_id\":\"$TEMP_TYPE_ID\",\"metric_ids\":[\"$RPM_METRIC_ID\"],\"is_active\":true}"
```
- [ ] Returns HTTP 400: "Metrics ... not supported by device type 'temperature_sensor'"

### 5. Devices table renamed
```bash
docker compose exec postgres psql -U iotuser -d iotdash -c "\dt devices_provisioned"
docker compose exec postgres psql -U iotuser -d iotdash -c "\dt device_provisioned_metrics"
```
- [ ] `devices_provisioned` table exists
- [ ] `device_provisioned_metrics` table exists
- [ ] Old `devices` and `device_metrics` table names no longer exist

---

## Incremental MQTT

### 6. MQTT diff messages
- [ ] Start fake_device: `python fake_device.py`
- [ ] Login as admin at `http://localhost:5173`
- [ ] Navigate to `/admin/devices`
- [ ] Find sensor01, click "Metrics" button
- [ ] Add "humidity" metric checkbox, click "Save Metrics" with "Send config" checked
- [ ] In fake_device terminal: see `addMetrics: ["humidity"]` (NOT the full list)
- [ ] Open Metrics modal again, uncheck "temperature", click "Save Metrics"
- [ ] In fake_device terminal: see `removeMetrics: ["temperature"]` (NOT the full list)

---

## UI Changes

### 7. Auto-generated UID visible (greyed out)
- [ ] Navigate to `/admin/devices`
- [ ] Click "Provision Device"
- [ ] "Auto-generate device UID" is checked by default
- [ ] UID input field is **visible** but disabled (greyed out, placeholder "Auto-generated on save")
- [ ] Uncheck auto-generate → UID field becomes editable
- [ ] Re-check auto-generate → field becomes disabled again

### 8. Platform org excluded from user creation
- [ ] Navigate to `/admin/users`
- [ ] Click "Create User"
- [ ] Organisation dropdown shows Demo Corp and Acme IoT
- [ ] **"Platform" does NOT appear** in the dropdown
- [ ] Platform users (admin) still visible in the users table with role badge

### 9. Admin sees all devices from "Devices" top menu
- [ ] Login as `admin@iotdash.com`
- [ ] Click "Devices" in the top navigation
- [ ] See a **table** (not cards) with all devices from all organisations
- [ ] Table columns: UID, Name, Organisation, Type, Metrics, Active, View
- [ ] Three filter dropdowns visible: Organisation, Device Type, Metric Type
- [ ] No provisioning controls (no "Provision Device" button, no delete/edit)
- [ ] Click "Dashboard" link on a device row → navigates to `/dashboard/{deviceId}`

### 10. Admin device filters on dashboard page
- [ ] On `/dashboard` (admin view), select Organisation: "Demo Corp"
- [ ] Only Demo Corp devices shown (sensor01, sensor02)
- [ ] Select Organisation: "Acme IoT"
- [ ] Only Acme IoT devices shown (sensor03)
- [ ] Reset to "All organisations"
- [ ] Select Device Type: "temperature_sensor" → all 3 devices shown (all are temp sensors in seed)
- [ ] Select Metric Type: "temperature" → devices with temperature metric shown
- [ ] Select Metric Type: "humidity" → 0 devices (no devices have humidity enabled in seed)

### 11. Filters below provisioning form
- [ ] Navigate to `/admin/devices`
- [ ] Click "Provision Device" to open the create form
- [ ] Filter dropdowns are **below** the create form, not above it
- [ ] Close the form — filters still visible above the devices table

### 12. Device type as dropdown
- [ ] Navigate to `/admin/devices`
- [ ] Click "Provision Device"
- [ ] Device Type field is a **dropdown** (not text input)
- [ ] Dropdown shows: "temperature_sensor", "engine_monitor"
- [ ] Select "temperature_sensor" → metric checkboxes show: temperature, humidity
- [ ] Select "engine_monitor" → metric checkboxes show: engine_rpm, temperature
- [ ] Cannot type a custom device type

### 13. Inline device editing
- [ ] Navigate to `/admin/devices`
- [ ] Click "Edit" on sensor01
- [ ] Row switches to inline edit mode:
  - Name: text input pre-filled with "Temperature Sensor 01"
  - Device Type: dropdown pre-selected with "temperature_sensor"
  - Active: checkbox (checked)
- [ ] Change name to "Updated Sensor 01", click "Save"
- [ ] Row reverts to read mode with updated name
- [ ] Click "Edit" on same device → "Cancel" → no changes saved

---

## Alert Metric Dropdown

### 14. Create alert — dynamic metric dropdown
- [ ] Logout, login as `viewer@democorp.com` / `viewer123`
- [ ] Navigate to `/alerts` → click "New Alert"
- [ ] Device dropdown shows sensor01, sensor02
- [ ] **Before selecting device**: metric dropdown shows "Select a device first" (disabled)
- [ ] Select sensor01 → metric dropdown enables with "temperature" option
- [ ] Select sensor02 → metric resets to first available (temperature)
- [ ] Create alert with temperature above 40 → saves successfully

### 15. Edit alert — dynamic metric dropdown
- [ ] Click "Edit" on an existing alert
- [ ] Device field shows the device code (read-only)
- [ ] Metric dropdown shows metrics enabled on that device
- [ ] If device has only temperature, dropdown shows only temperature
- [ ] Change threshold and save → updates successfully

### 16. Alert metric validation (API)
```bash
# Login as viewer
curl -s -c vcookies.txt -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"viewer@democorp.com","password":"viewer123"}'

# Get device ID
DEVICE_ID=$(curl -s -b vcookies.txt http://localhost:8000/api/devices | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d[0]["id"])')

# Try to create alert with metric not on device
curl -s -b vcookies.txt -X POST http://localhost:8000/api/alerts \
  -H "Content-Type: application/json" \
  -d "{\"device_id\":\"$DEVICE_ID\",\"metric\":\"engine_rpm\",\"condition\":\"above\",\"threshold\":100,\"duration_seconds\":60,\"notification_email\":\"test@test.com\"}"
```
- [ ] Returns HTTP 400: "Metric 'engine_rpm' not enabled on this device"

---

## Device Types CRUD (API)

### 17. Create device type
```bash
TEMP_ID=$(curl -s -b cookies.txt http://localhost:8000/api/admin/device-types | python3 -c 'import json,sys;[print(m["metric_id"]) for t in json.load(sys.stdin) for m in t["allowed_metrics"] if m["metric_name"]=="temperature"]' | head -1)

curl -s -b cookies.txt -X POST http://localhost:8000/api/admin/device-types \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"pressure_sensor\",\"description\":\"Pressure monitoring unit\",\"metric_ids\":[\"$TEMP_ID\"]}" | python3 -m json.tool
```
- [ ] New device type created with name "pressure_sensor" and temperature as allowed metric

### 18. Delete device type
```bash
# Get the new type ID
NEW_TYPE_ID=$(curl -s -b cookies.txt http://localhost:8000/api/admin/device-types | python3 -c 'import json,sys;[print(t["id"]) for t in json.load(sys.stdin) if t["name"]=="pressure_sensor"]')

# Delete it (should succeed — no devices use it)
curl -s -b cookies.txt -X DELETE "http://localhost:8000/api/admin/device-types/$NEW_TYPE_ID"
```
- [ ] Returns HTTP 200 (deleted successfully)

### 19. Delete device type blocked by devices
```bash
TEMP_TYPE_ID=$(curl -s -b cookies.txt http://localhost:8000/api/admin/device-types | python3 -c 'import json,sys;[print(t["id"]) for t in json.load(sys.stdin) if t["name"]=="temperature_sensor"]')

curl -s -b cookies.txt -X DELETE "http://localhost:8000/api/admin/device-types/$TEMP_TYPE_ID"
```
- [ ] Returns HTTP 400: "Cannot delete device type — devices are still using it"

---

## Grafana Organisation Provisioning (from Bugfix 1, still works)

### 20. Create org provisions Grafana
- [ ] Login as admin, navigate to `/admin/organisations`
- [ ] Create "Test Corp"
- [ ] Org appears with `grafana_org_id` value (non-null)
```bash
curl -s -u admin:admin http://localhost:3000/api/orgs
```
- [ ] "Test Corp" appears in Grafana orgs list

---

## Viewer Experience Unchanged

### 21. Viewer login and dashboard
- [ ] Logout, login as `viewer@democorp.com` / `viewer123`
- [ ] "Devices" top nav → see card grid (NOT the admin table)
- [ ] Cards show sensor01, sensor02 with device type name and active badge
- [ ] Click a card → device detail page with Grafana embeds
- [ ] No "Admin" nav link visible
- [ ] Navigating to `/admin` redirects to `/dashboard`

---

## Troubleshooting

### Migration 003 fails
If the migration fails with "table already exists", you likely have a partially applied migration. Run `docker compose down -v` to wipe volumes and start fresh.

### Device type dropdown empty
Device types come from the database. If seed didn't run or database is empty, the dropdown will have no options. Run `docker compose exec backend python -m app.seed`.

### Metric checkboxes don't filter by device type
Verify `GET /api/admin/device-types` returns allowed_metrics for each type. The frontend filters metric checkboxes based on the `allowed_metrics` array of the selected device type.

### Alert creation fails with "Metric not enabled on this device"
This is expected if the device doesn't have that metric assigned. Check the device's metrics via `/admin/devices` — only enabled metrics can be used in alerts.

### fake_device doesn't show removeMetrics
Make sure you're running the latest `fake_device.py` which handles the `removeMetrics` key. The old version only handled `addMetrics`.
