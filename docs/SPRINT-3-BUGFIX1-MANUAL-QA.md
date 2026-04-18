# Sprint 3 Bugfix 1 — Manual QA Checklist

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
- [ ] Seed output shows **3 orgs**: Platform, Demo Corp, Acme IoT
- [ ] Seed output shows admin user: `admin@iotdash.com`
- [ ] Seed output shows Demo Corp viewer: `viewer@democorp.com`
- [ ] Seed output shows Acme IoT viewer: `viewer@acmeiot.com`

### 2. Login with new admin credentials
- [ ] Open `http://localhost:5173`
- [ ] Old admin login (`admin@democorp.com`) does NOT work
- [ ] Login with `admin@iotdash.com` / `admin123`
- [ ] Header shows "Admin" nav link
- [ ] `/api/auth/me` shows organisation_name: "Platform"

### 3. Client logins are viewer-only
- [ ] Logout, login as `viewer@democorp.com` / `viewer123`
- [ ] No "Admin" nav link visible
- [ ] Navigating to `/admin` redirects to `/dashboard`
- [ ] Logout, login as `viewer@acmeiot.com` / `viewer123`
- [ ] Same viewer-only experience

---

## Role Enforcement

### 4. Create user — no role dropdown
- [ ] Login as `admin@iotdash.com`
- [ ] Navigate to `/admin/users`
- [ ] Click "Create User"
- [ ] Form shows: Email, Password, Full Name, Organisation dropdown
- [ ] **No role dropdown** in the form
- [ ] Create user with email `test@democorp.com`, assign to Demo Corp
- [ ] User appears in list with role badge showing "viewer"

### 5. Edit user — no role dropdown
- [ ] Click "Edit" on the user created above
- [ ] Inline edit shows: Email field, Name field
- [ ] **No role dropdown** in the edit row
- [ ] Change name, click "Save" — updates correctly
- [ ] Role badge still shows "viewer"

### 6. API rejects role escalation attempts
```bash
# Try to create user with admin role via API (should be ignored)
curl -s -b cookies.txt -X POST http://localhost:8000/api/admin/users \
  -H "Content-Type: application/json" \
  -d '{"email":"sneaky@test.com","password":"pass","full_name":"Sneaky","organisation_id":"<org_id>","role":"admin"}'
```
- [ ] User created successfully but role is "viewer" (role field ignored)

---

## Admin Device Filters

### 7. Filter dropdowns present
- [ ] Navigate to `/admin/devices`
- [ ] See **three filter dropdowns** side by side:
  - Organisation (All organisations)
  - Device Type (All device types)
  - Metric Type (All metrics)

### 8. Device type filter
- [ ] Open "Device Type" dropdown — should show "temperature" (from seed data)
- [ ] Select "temperature" — only temperature-type devices shown
- [ ] Select "All device types" — all devices shown again

### 9. Metric type filter
- [ ] Open "Metric Type" dropdown — should show temperature, humidity, engine_rpm
- [ ] Select "temperature" — only devices with temperature metric shown
- [ ] Select "humidity" — shows empty or only devices with humidity metric
- [ ] Select "All metrics" — all devices shown again

### 10. Combined filters
- [ ] Select Organisation: "Demo Corp" + Device Type: "temperature"
- [ ] Only Demo Corp temperature devices shown (sensor01, sensor02)
- [ ] Add Metric Type: "temperature"
- [ ] Same result (AND logic, all three filters applied)
- [ ] Change Organisation to "Acme IoT" — shows sensor03 only
- [ ] Reset all filters — all devices from all orgs shown

### 11. Device types endpoint
```bash
curl -s -b cookies.txt http://localhost:8000/api/admin/devices/device-types
```
- [ ] Returns JSON array of distinct device types, e.g. `["temperature"]`

---

## Grafana Organisation Auto-Provisioning

### 12. Create org provisions Grafana
- [ ] Login as `admin@iotdash.com`
- [ ] Navigate to `/admin/organisations`
- [ ] Click "Create Organisation" — enter "Beta Corp"
- [ ] Org appears in table with a `grafana_org_id` value (non-null)

### 13. Verify Grafana org exists
```bash
curl -s -u admin:admin http://localhost:3000/api/orgs
```
- [ ] "Beta Corp" appears in the Grafana orgs list
- [ ] Note the Grafana org ID

### 14. Verify datasource provisioned
```bash
curl -s -u admin:admin -H "X-Grafana-Org-Id: <grafana_org_id>" \
  http://localhost:3000/api/datasources
```
- [ ] InfluxDB datasource exists in the new org
- [ ] Type is "influxdb", URL points to InfluxDB

### 15. Verify dashboard provisioned
```bash
curl -s -u admin:admin -H "X-Grafana-Org-Id: <grafana_org_id>" \
  http://localhost:3000/api/search?type=dash-db
```
- [ ] "IoT Metrics Dashboard" appears in the new org
- [ ] Dashboard has template variables (device_id, metric)

### 16. Grafana failure doesn't block org creation
- [ ] Stop Grafana: `docker compose stop grafana`
- [ ] Create org "Gamma Corp" via admin UI
- [ ] Org created successfully (check table — appears with name)
- [ ] `grafana_org_id` is null (Grafana was unreachable)
- [ ] Restart Grafana: `docker compose start grafana`

---

## Backend Tests

### 17. All tests pass
```bash
docker compose exec backend python -m pytest tests/ -v
```
- [ ] **78 tests pass** (up from 71 in Sprint 3)
- [ ] New tests included:
  - `test_create_user_always_viewer`
  - `test_update_user_cannot_change_role`
  - `test_list_device_types`
  - `test_list_devices_filter_by_device_type`
  - `test_list_devices_filter_by_metric_name`
  - `test_list_devices_filter_by_nonexistent_metric`
  - `test_list_devices_combined_filters`

---

## Troubleshooting

### Old admin login doesn't work
The admin user moved from `admin@democorp.com` (Demo Corp) to `admin@iotdash.com` (Platform org). If you're seeing login failures, make sure you ran `docker compose down -v` and re-seeded.

### Grafana org creation returns 502
Check that Grafana is fully started. On first boot Grafana can take 10-15 seconds to be ready. The backend logs a warning and continues without Grafana provisioning. Re-creating the org (after deleting it) will retry.

### Device type dropdown is empty
The device types endpoint returns distinct values from the database. If no devices exist yet (empty database), the dropdown will be empty. Seed data or provision at least one device first.
