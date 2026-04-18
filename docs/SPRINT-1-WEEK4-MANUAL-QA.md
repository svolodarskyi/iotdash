# Sprint 1 Week 4 — Manual QA Checklist

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
- [ ] 7 services running: emqx, telegraf, influxdb, grafana, postgres, backend, frontend
- [ ] Alembic runs migration `001` (creates tables)
- [ ] Seed output shows 2 orgs, 2 users, 3 devices

### 2. Login redirect
- [ ] Open `http://localhost:5173`
- [ ] Redirects to `/login`
- [ ] Login form visible with email + password fields

### 3. Login as Demo Corp admin
- [ ] Enter `admin@democorp.com` / `admin123`
- [ ] Click "Sign in"
- [ ] Redirects to `/dashboard`
- [ ] Header shows "Admin User — Demo Corp" and Logout button

### 4. Device list — Demo Corp
- [ ] See 2 device cards: Temperature Sensor 01, Temperature Sensor 02
- [ ] sensor03 does NOT appear (belongs to Acme IoT)
- [ ] Cards show device code, type, active status

### 5. Device detail + Grafana embeds
- [ ] Click a device card → `/dashboard/{id}`
- [ ] Grafana iframe panels render
- [ ] "Refresh Panels" button works

### 6. Logout
- [ ] Click "Logout" in header
- [ ] Redirects to `/login`
- [ ] Navigating to `/dashboard` redirects back to `/login`

### 7. Login as Acme IoT viewer
- [ ] Enter `viewer@acmeiot.com` / `viewer123`
- [ ] Redirects to `/dashboard`
- [ ] Header shows "Acme Viewer — Acme IoT"

### 8. Device list — Acme IoT (org isolation)
- [ ] See only 1 device: Temperature Sensor 03
- [ ] sensor01 and sensor02 do NOT appear

### 9. Cookie verification
- [ ] Open DevTools → Application → Cookies → localhost
- [ ] `access_token` cookie present
- [ ] HttpOnly column shows checkmark (JS cannot read it)

### 10. Session persistence
- [ ] Close tab while logged in
- [ ] Open new tab to `http://localhost:5173`
- [ ] Goes straight to `/dashboard` (cookie persists)

### 11. API returns 401 without auth
```bash
curl http://localhost:8000/api/devices
```
- [ ] Returns 401 `{"detail":"Not authenticated"}`

### 12. Health endpoint still public
```bash
curl http://localhost:8000/api/health
```
- [ ] Returns 200 `{"status":"ok"}`

### 13. Tests pass
```bash
docker compose run --rm --no-deps backend pytest -v
docker compose exec frontend npm test
```
- [ ] Backend: 27 tests pass
- [ ] Frontend: 4 tests pass

### 14. Login error handling
- [ ] Enter wrong password → "Invalid email or password" message
- [ ] Enter nonexistent email → same error message
