# Sprint 2 — Manual QA Checklist

## Prerequisites
- Docker and Docker Compose installed
- Fresh database (run `docker compose down -v` first)

## QA Steps

### 1. All services start
```bash
docker compose down -v
docker compose up --build -d
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.seed
```
- [ ] 8 services running: emqx, telegraf, influxdb, grafana, postgres, backend, frontend, mailhog
- [ ] Alembic runs migration `001` (creates tables)
- [ ] Seed output shows 2 orgs, 2 users, 3 devices, 2 alerts

### 2. Login as Demo Corp admin
- [ ] Open `http://localhost:5173`
- [ ] Redirects to `/login`
- [ ] Enter `admin@democorp.com` / `admin123`
- [ ] Redirects to `/dashboard`
- [ ] Header shows "Devices" and "Alerts" nav links

### 3. Navigate to Alerts
- [ ] Click "Alerts" in header → `/alerts`
- [ ] See 1 seeded alert: sensor01, temperature above 30
- [ ] Toggle switch shows enabled state
- [ ] Edit and Delete actions visible

### 4. Create new alert
- [ ] Click "New Alert" button
- [ ] Redirects to `/alerts/new`
- [ ] Device dropdown shows sensor01 and sensor02
- [ ] Select sensor02, temperature above 25, duration 60s, email admin@democorp.com
- [ ] Click "Create Alert"
- [ ] Redirects to `/alerts`
- [ ] New alert appears in list

### 5. Edit alert
- [ ] Click "Edit" on the new alert
- [ ] Redirects to `/alerts/{id}/edit`
- [ ] Device field shows "sensor02" (read-only)
- [ ] Change threshold to 28
- [ ] Click "Save Changes"
- [ ] Redirects to `/alerts` with updated threshold

### 6. Toggle alert
- [ ] Click toggle switch on an alert
- [ ] Toggle changes to disabled state (gray)
- [ ] Click again — re-enabled (blue)

### 7. Delete alert
- [ ] Click "Delete" on the alert created in step 4
- [ ] Confirm dialog appears
- [ ] Click OK — alert removed from list

### 8. Org isolation — Acme IoT
- [ ] Click "Logout"
- [ ] Login as `viewer@acmeiot.com` / `viewer123`
- [ ] Navigate to `/alerts`
- [ ] See only 1 alert: sensor03, temperature above 35
- [ ] sensor01 alert does NOT appear

### 9. Grafana alert rule verification
- [ ] Login as Demo Corp admin
- [ ] Create alert: sensor01, temperature below 25, duration 10s, email admin@democorp.com
- [ ] Alert in list should show a `grafana_rule_uid` (non-null)
- [ ] Open `http://localhost:3000/alerting/list` (Grafana, login admin/admin)
- [ ] See "iotdash-alerts" folder with alert rule
- [ ] Rule title: "sensor01 — temperature below 25.0"
- [ ] Click rule → verify Flux query filters on `device_id` and `_field` only (no `message_type`)

### 10. End-to-end email notification
- [ ] Ensure fake_device.py is running (publishes ~19–22°C temperature)
```bash
python fake_device.py
```
- [ ] Create alert: sensor01, temperature below 25, duration 10s, email admin@democorp.com
- [ ] Wait ~2-3 minutes for Grafana to evaluate the rule (1m evaluation interval + 10s pending duration)
- [ ] Open `http://localhost:8025` (Mailhog web UI)
- [ ] Email from "IoTDash Alerts" `<alerts@iotdash.local>` should appear
- [ ] Subject contains `[FIRING:1]` and the rule title
- [ ] Email is addressed to the notification_email specified in the alert

### 11. Grafana re-sync on toggle (recovery from failed sync)
This verifies that alerts with `grafana_rule_uid = null` (from a failed Grafana sync) are automatically synced when toggled or updated.
- [ ] If any seeded alerts show `grafana_rule_uid: null`, toggle them off then on
- [ ] After toggling, the alert should now show a non-null `grafana_rule_uid`
- [ ] The rule appears in Grafana alerting list (`localhost:3000/alerting/list`)

### 12. Delete alert cleans up Grafana
- [ ] Delete the alert created in step 10
- [ ] Refresh Grafana alerting page (`localhost:3000/alerting/list`)
- [ ] Alert rule should be removed
- [ ] Contact point `alert-{uuid}` should be removed from Grafana

### 13. Mailhog accessible
- [ ] Open `http://localhost:8025`
- [ ] Mailhog web UI loads
- [ ] Shows any alert emails received

### 14. API returns 401 without auth
```bash
curl http://localhost:8000/api/alerts
```
- [ ] Returns 401 `{"detail":"Not authenticated"}`

### 15. Health endpoint still public
```bash
curl http://localhost:8000/api/health
```
- [ ] Returns 200 `{"status":"ok"}`

### 16. Tests pass
```bash
docker compose run --rm --no-deps backend pytest -v
docker compose exec frontend npm test
```
- [ ] Backend: 42 tests pass
- [ ] Frontend: 4 tests pass

### 17. Devices nav still works
- [ ] Click "Devices" in header
- [ ] Device list loads correctly
- [ ] Click a device → Grafana embeds render

---

## Troubleshooting

### Alerts show `grafana_rule_uid: null`
The Grafana sync failed at creation time (Grafana may have been starting up or had stale volumes). Fix: toggle the alert off then on, or edit and save — the backend will automatically create the missing Grafana rule.

### Grafana rules show `NoData`
Verify the Flux query matches the actual InfluxDB tag schema. The query should filter on `device_id` and `_field` only. Run this to confirm data exists:
```bash
curl -s -H "Authorization: Token mytoken123" -H "Content-Type: application/vnd.flux" \
  -X POST "http://localhost:8086/api/v2/query?org=iotorg" \
  -d 'from(bucket: "iot") |> range(start: -5m) |> filter(fn: (r) => r.device_id == "sensor01") |> filter(fn: (r) => r._field == "temperature") |> last()'
```

### Grafana API returns 403 on alerting endpoints
Stale Grafana volumes can cause RBAC permission issues. Fix: `docker compose down -v` to clear volumes, then rebuild. Basic auth with `admin:admin` works on a fresh Grafana instance.
