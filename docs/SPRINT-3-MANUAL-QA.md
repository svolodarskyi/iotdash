# Sprint 3 — Manual QA Checklist

## Environment Setup

- [ ] `docker compose down -v && docker compose up --build -d` — 8 services start
- [ ] `docker compose exec backend alembic upgrade head` — migrations 001 + 002 run
- [ ] `docker compose exec backend python -m app.seed` — seeds orgs, users, devices, alerts, metrics, device-metric links

## Authentication & Role Guard

- [ ] Login as `admin@democorp.com` / `admin123` — header shows "Admin" nav link
- [ ] Login as `viewer@acmeiot.com` / `viewer123` — no "Admin" link visible
- [ ] Viewer navigating to `/admin` redirects to `/dashboard`

## Admin — Organisations

- [ ] Navigate to `/admin/organisations` — see "Demo Corp" and "Acme IoT"
- [ ] Click "Create Organisation" — enter "Beta Corp" — appears in table
- [ ] Edit "Beta Corp" to "Beta Corp Ltd" — name updates
- [ ] Delete "Beta Corp Ltd" (empty org) — succeeds
- [ ] Attempt to delete "Demo Corp" — fails with error (has devices/users)

## Admin — Users

- [ ] Navigate to `/admin/users` — see admin and viewer users
- [ ] Filter by organisation — shows only matching users
- [ ] Create new user: email, password, name, org, role — appears in list
- [ ] Edit user name/role — updates immediately
- [ ] Deactivate user — user marked inactive

## Admin — Devices

- [ ] Navigate to `/admin/devices` — see sensor01, sensor02, sensor03 with temperature badge
- [ ] Filter by organisation — filters correctly
- [ ] Click "Provision Device" — fill form:
  - Device name: "Humidity Sensor"
  - UID: auto-generate (checkbox checked)
  - Organisation: "Demo Corp"
  - Metrics: check temperature + humidity
  - Auto-enable: checked
- [ ] Device created with auto-generated UID (starts with `dev-`)
- [ ] Metric badges show "temperature" and "humidity"
- [ ] Click "Metrics" on a device — modal shows metric checkboxes
- [ ] Add engine_rpm metric with "Send config" checked — saves
- [ ] Click "Re-send Config" — succeeds (check backend logs for MQTT publish)
- [ ] Delete a test device — removed from list

## Multi-Metric Dashboard

- [ ] Navigate to device detail page for sensor01 — shows temperature graph
- [ ] Provision a device with temperature + humidity metrics
- [ ] Navigate to new device's detail page — see two embedded graphs
- [ ] Click metric pills to filter — deselect temperature — only humidity shown
- [ ] Click "Show All" — all graphs restored
- [ ] Click "Refresh Panels" — iframes reload

## Fake Device Simulator

- [ ] `python3 fake_device.py` — publishes temperature every 1s
- [ ] Send MQTT config via admin "Re-send Config" for sensor01 with humidity
- [ ] Fake device log shows: CONFIG received, starts publishing humidity
- [ ] `python3 fake_device.py --all-metrics` — publishes all 3 metrics from start
- [ ] `python3 fake_device.py --device-id sensor02` — uses correct device ID

## Grafana Dashboard

- [ ] Open `http://localhost:3000` — "IoT Metrics Dashboard" loads
- [ ] Verify dashboard has template variables (device_id, metric)
- [ ] Embed URLs include `var-device_id` and `var-metric` parameters

## Backend Tests

- [ ] `docker compose run --rm --no-deps backend pytest -v` — 71 tests pass
- [ ] All new admin tests pass (orgs, users, devices, metrics)
- [ ] Existing tests still pass (auth, devices, alerts, org isolation)

## End-to-End Demo Flow

- [ ] Admin provisions new device with temperature + humidity + auto-enable
- [ ] Start fake_device with matching device-id — receives config, publishes both metrics
- [ ] Dashboard shows two live graphs updating in real-time
- [ ] Admin creates new org "Beta Corp" → adds user → adds device
- [ ] Login as new user → see own dashboard with own devices
