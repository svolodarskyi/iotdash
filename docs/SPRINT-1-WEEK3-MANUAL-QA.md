# Sprint 1 Week 3 — Manual QA Checklist

## Prerequisites
- Docker and Docker Compose installed
- Seed data loaded (sensor01, sensor02 devices exist in PostgreSQL)

## QA Steps

### 1. All services start
```bash
docker compose up --build -d
docker compose ps
```
- [ ] 7 services running: emqx, telegraf, influxdb, grafana, postgres, backend, **frontend**
- [ ] No restart loops

### 2. Frontend loads
- [ ] Open `http://localhost:5173`
- [ ] Redirects to `/dashboard`
- [ ] Page renders with "IoT Dashboard" header

### 3. Device list
- [ ] Device cards visible (sensor01, sensor02)
- [ ] Each card shows name, device code, type, active status
- [ ] Cards are clickable links

### 4. Device detail + Grafana embeds
- [ ] Click a device card → navigates to `/dashboard/{id}`
- [ ] "Back to devices" link visible and works
- [ ] Grafana iframe panels render (may show "No data" if no MQTT data yet)
- [ ] Panel titles display correctly

### 5. Live data in panels
```bash
python fake_device.py
```
- [ ] Run fake_device.py to publish MQTT data
- [ ] Data appears in embedded Grafana panels within ~10 seconds
- [ ] Panels auto-refresh (configured with `refresh=5s`)

### 6. Refresh button
- [ ] Click "Refresh Panels" button on device detail page
- [ ] Iframes reload (panels briefly flash/reload)

### 7. Hot module reload
- [ ] Edit `frontend/src/components/Layout.tsx` — change header text
- [ ] Browser updates without full page reload

### 8. Tests pass
```bash
docker compose exec frontend npm test
```
- [ ] All tests pass (rewriteGrafanaUrl tests)

### 9. API still works
```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/devices
```
- [ ] Backend returns 200 with valid JSON
