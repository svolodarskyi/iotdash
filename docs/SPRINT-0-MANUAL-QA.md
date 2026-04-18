# Sprint 0 — Manual QA Checklist

Run through each step after `docker compose up --build -d` completes.

## Prerequisites

```bash
docker compose up --build -d
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.seed
```

---

## 1. Docker Compose Up

- [ ] `docker compose up --build` succeeds without errors
- [ ] `docker compose ps` shows 6 services: emqx, telegraf, influxdb, grafana, postgres, backend
- [ ] All services show status "healthy" or "running"

## 2. Health Endpoint

```bash
curl http://localhost:8000/api/health
```

- [ ] Returns HTTP 200
- [ ] Body: `{"status":"ok"}`

## 3. Swagger UI

- [ ] Open `http://localhost:8000/docs` in browser
- [ ] All endpoints visible: health, devices, organisations

## 4. Database Seeded

```bash
curl http://localhost:8000/api/organisations
```

- [ ] Returns JSON array with one org: "Demo Corp"

## 5. Devices Listed

```bash
curl http://localhost:8000/api/devices
```

- [ ] Returns 2 devices: sensor01, sensor02
- [ ] Each device has `id`, `device_code`, `name`, `device_type`, `is_active`

## 6. Device Detail

```bash
curl http://localhost:8000/api/devices/{id}
```

(Replace `{id}` with actual UUID from step 5)

- [ ] Returns single device with all fields
- [ ] Returns 404 for non-existent UUID

## 7. Organisation Devices

```bash
curl http://localhost:8000/api/organisations/{org_id}/devices
```

- [ ] Returns filtered list of 2 devices belonging to Demo Corp
- [ ] Returns 404 for non-existent org UUID

## 8. Embed URLs

```bash
curl http://localhost:8000/api/devices/{id}/embed-urls
```

- [ ] Returns `device_id`, `device_code`, and `urls` array
- [ ] URLs contain `d-solo/` path, `panelId`, and `var-device_id` query param

## 9. Grafana Embed

- [ ] Copy an embed URL from step 8
- [ ] Replace `grafana:3000` with `localhost:3000` in the URL
- [ ] Open in browser — Grafana panel renders without requiring login

## 10. Fake Device Data Flow

```bash
python fake_device.py
```

- [ ] Script connects and publishes to `sensor01/from/message`
- [ ] Open Grafana at `http://localhost:3000` — temperature chart shows live data

## 11. EMQX Dashboard

- [ ] Open `http://localhost:18083` (default: admin / public)
- [ ] See connected client when fake_device.py is running

## 12. InfluxDB Data

- [ ] Open `http://localhost:8086` (admin / admin1234)
- [ ] Navigate to Data Explorer
- [ ] Query `iot` bucket → see temperature measurements with `device_id` tag

## 13. Automated Tests

```bash
docker compose exec backend pytest -v
```

- [ ] All tests pass (expected: 12+ tests)

## 14. Linting

```bash
docker compose exec backend ruff check .
```

- [ ] No lint errors
