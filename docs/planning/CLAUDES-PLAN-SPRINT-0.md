# Claude's Plan — Sprint 0: Repo & Local Stack

> **Version:** 1.0
> **Date:** 2026-04-12
> **Status:** Pending approval

---

## Context

The IoTDash project has a working IoT data pipeline (EMQX → Telegraf → InfluxDB → Grafana) with a fake device simulator, but **no application layer**. Sprint 0 establishes: git repo, project structure, PostgreSQL, FastAPI backend scaffold with CRUD API, Alembic migrations, seed data, automated tests, and a manual QA document. All development runs inside Docker containers.

**User requirements:**
- Work on Sprint 0 (Week 1 + Week 2 from TECH-LEAD-PLAYBOOK.md)
- All work tested by automated tests (pytest)
- Create a manual QA document
- Work in Docker containers; install libraries there
- Create necessary skills/prerequisites before starting

---

## Step 1: Project Structure & Git Init

Create the folder structure and initialize git:

```
iotdash/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app, /api/health
│   │   ├── config.py            # Settings via pydantic-settings
│   │   ├── database.py          # SQLAlchemy engine/session
│   │   ├── models.py            # SQLAlchemy ORM models
│   │   ├── schemas.py           # Pydantic request/response schemas
│   │   ├── seed.py              # Seed script (python -m app.seed)
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── health.py
│   │       ├── devices.py
│   │       └── organisations.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py          # Fixtures: test DB, test client
│   │   ├── test_health.py
│   │   ├── test_devices.py
│   │   └── test_organisations.py
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── alembic.ini
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                    # Empty placeholder
├── infra/                       # Empty placeholder
├── grafana/                     # Existing provisioning
├── telegraf.conf                # Existing (update topics)
├── fake_device.py               # Existing (update topics)
├── docker-compose.yml           # Extend with postgres + backend
├── .env.example
├── .gitignore
└── docs/
```

**Files to create:** `.gitignore`, `.env.example`, restructured `backend/` tree
**Files to modify:** `docker-compose.yml`, `telegraf.conf`, `fake_device.py`

---

## Step 2: Docker Configuration

### 2a. Backend Dockerfile (`backend/Dockerfile`)
- Python 3.12-slim base
- Install dependencies from requirements.txt
- Copy app code
- CMD: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

### 2b. Extend `docker-compose.yml`
Add two services:

**postgres:**
- Image: postgres:16
- Env: POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD from .env
- Volume: postgres_data
- Healthcheck: pg_isready
- Network: iot_net

**backend:**
- Build from `./backend`
- Ports: 8000:8000
- Env: DATABASE_URL, INFLUXDB_URL, INFLUXDB_TOKEN, GRAFANA_URL
- Volumes: `./backend:/app` (for hot-reload in dev)
- Depends on: postgres (healthy), influxdb (healthy)
- Network: iot_net

### 2c. `.env.example`
```
POSTGRES_DB=iotdash
POSTGRES_USER=iotdash
POSTGRES_PASSWORD=iotdash_dev
DATABASE_URL=postgresql://iotdash:iotdash_dev@postgres:5432/iotdash
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=mytoken123
INFLUXDB_ORG=iotorg
INFLUXDB_BUCKET=iot
GRAFANA_URL=http://grafana:3000
```

---

## Step 3: FastAPI Backend Scaffold

### 3a. `pyproject.toml` / `requirements.txt`
Dependencies:
- fastapi, uvicorn[standard]
- sqlalchemy, alembic, psycopg2-binary
- pydantic, pydantic-settings
- python-dotenv
- httpx (for Grafana API calls later)
- pytest, pytest-asyncio, httpx (test deps)

### 3b. `app/config.py`
Pydantic Settings class reading from env vars:
- DATABASE_URL, INFLUXDB_URL, GRAFANA_URL, etc.

### 3c. `app/database.py`
- SQLAlchemy engine from DATABASE_URL
- SessionLocal factory
- get_db dependency

### 3d. `app/models.py`
SQLAlchemy models matching PLANNING.md Section 6.2:
- Organisation (id, name, grafana_org_id, created_at, updated_at)
- User (id, email, password_hash, full_name, organisation_id, role, is_active, timestamps)
- Device (id, device_code, name, organisation_id, device_type, metadata, is_active, timestamps)
- GrafanaDashboard (id, organisation_id, title, grafana_uid, grafana_org_id, panel_ids, embed_base_url, timestamps)
- Alert (id, device_id, created_by, metric, condition, threshold, duration_seconds, notification_email, is_enabled, grafana_rule_uid, timestamps)

### 3e. `app/main.py`
- FastAPI app with title "IoTDash API"
- Include routers: health, devices, organisations
- CORS middleware (allow all origins for dev)

### 3f. Routers
- `health.py`: GET /api/health -> {"status": "ok"}
- `devices.py`:
  - GET /api/devices -> list all devices (hardcoded org for now)
  - GET /api/devices/{id} -> single device
  - GET /api/devices/{id}/embed-urls -> construct Grafana iframe URLs
- `organisations.py`:
  - GET /api/organisations -> list orgs
  - GET /api/organisations/{id} -> org details
  - GET /api/organisations/{id}/devices -> devices for org

---

## Step 4: Alembic Migrations

- `alembic init` inside backend/
- Configure `alembic/env.py` to use app.database and app.models
- Create first migration with all 5 tables (organisations, users, devices, grafana_dashboards, alerts)
- Migration runs automatically on container start (via entrypoint script)

---

## Step 5: Seed Script (`app/seed.py`)

Creates initial data:
- 1 organisation: "Demo Corp"
- 1 admin user: admin@democorp.com / password hashed with bcrypt
- 2 devices: sensor01 (temperature), sensor02 (temperature)
- 1 grafana_dashboard entry pointing to existing temperature dashboard

Run via: `docker compose exec backend python -m app.seed`

---

## Step 6: Update MQTT Topics & Fake Device

### 6a. Update `telegraf.conf`
Change subscription from `sensors/+/temperature` to new scheme: `+/from/message`
Update topic parsing for `device_id/direction/message_type`

### 6b. Update `fake_device.py`
Change topic from `sensors/sensor01/temperature` to `sensor01/from/message`
Keep same payload format

---

## Step 7: Grafana Embedding Config

Add environment variables to Grafana service in docker-compose.yml:
```yaml
GF_SECURITY_ALLOW_EMBEDDING: "true"
GF_AUTH_ANONYMOUS_ENABLED: "true"
GF_AUTH_ANONYMOUS_ORG_NAME: iotorg
```

---

## Step 8: Automated Tests (pytest)

### 8a. `tests/conftest.py`
- Create test PostgreSQL database (use separate test DB or SQLite for simplicity)
- TestClient fixture with dependency override for get_db
- Auto-create tables via SQLAlchemy metadata.create_all
- Seed fixture for test data

### 8b. Test files
- `test_health.py`: GET /api/health returns 200 + {"status": "ok"}
- `test_devices.py`:
  - GET /api/devices returns list
  - GET /api/devices/{id} returns device
  - GET /api/devices/{id} with bad id returns 404
  - GET /api/devices/{id}/embed-urls returns URLs
- `test_organisations.py`:
  - GET /api/organisations returns list
  - GET /api/organisations/{id} returns org
  - GET /api/organisations/{id}/devices returns filtered devices

### 8c. Run tests
Tests run inside Docker: `docker compose exec backend pytest -v`
Use SQLite in-memory for test DB (no external dependency needed).

---

## Step 9: Linting & Formatting

Add to backend/pyproject.toml:
- ruff (linting + formatting, replaces both black and flake8)
- Configuration in pyproject.toml [tool.ruff] section

Run: `docker compose exec backend ruff check .` and `ruff format .`

---

## Step 10: Manual QA Document

Create `docs/SPRINT-0-MANUAL-QA.md` with step-by-step checklist:

1. **Docker Compose Up** — `docker compose up --build` succeeds, all services healthy
2. **Health Endpoint** — `curl localhost:8000/api/health` returns `{"status":"ok"}`
3. **Swagger UI** — Open `localhost:8000/docs`, all endpoints visible
4. **Database Seeded** — `curl localhost:8000/api/organisations` returns Demo Corp
5. **Devices Listed** — `curl localhost:8000/api/devices` returns sensor01, sensor02
6. **Device Detail** — `curl localhost:8000/api/devices/{id}` returns single device
7. **Org Devices** — `curl localhost:8000/api/organisations/{id}/devices` returns filtered list
8. **Embed URLs** — `curl localhost:8000/api/devices/{id}/embed-urls` returns Grafana iframe URLs
9. **Grafana Embed** — Paste embed URL in browser, Grafana panel renders without login
10. **Fake Device Data** — Run fake_device.py, check Grafana shows live data
11. **EMQX Dashboard** — Open `localhost:18083`, see device connected
12. **InfluxDB Data** — Open `localhost:8086`, query iot bucket, see temperature data

---

## Verification (End-to-End)

After implementation:
1. `docker compose up --build -d` — all 6 services start (emqx, telegraf, influxdb, grafana, postgres, backend)
2. `docker compose exec backend alembic upgrade head` — migrations apply cleanly
3. `docker compose exec backend python -m app.seed` — seed data created
4. `docker compose exec backend pytest -v` — all tests pass
5. `curl localhost:8000/api/health` -> `{"status":"ok"}`
6. `curl localhost:8000/docs` -> Swagger UI loads
7. `python fake_device.py` -> data flows to InfluxDB -> visible in Grafana
8. `docker compose exec backend ruff check .` -> no lint errors

---

## File Summary

### Files Created (new)
- `.gitignore`
- `.env.example`
- `backend/Dockerfile`
- `backend/requirements.txt`
- `backend/pyproject.toml`
- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/versions/001_initial_schema.py`
- `backend/app/__init__.py`
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/database.py`
- `backend/app/models.py`
- `backend/app/schemas.py`
- `backend/app/seed.py`
- `backend/app/routers/__init__.py`
- `backend/app/routers/health.py`
- `backend/app/routers/devices.py`
- `backend/app/routers/organisations.py`
- `backend/tests/__init__.py`
- `backend/tests/conftest.py`
- `backend/tests/test_health.py`
- `backend/tests/test_devices.py`
- `backend/tests/test_organisations.py`
- `docs/SPRINT-0-MANUAL-QA.md`

### Files Modified (existing)
- `docker-compose.yml` — add postgres + backend services, Grafana embed env vars
- `telegraf.conf` — update topic subscription to new scheme
- `fake_device.py` — update topic to new scheme

### Not In Scope (deferred)
- Authentication (Sprint 1)
- Frontend (Sprint 1)
- Azure/CI/CD (Sprint 2+)
- MQTT device auth (Sprint 2+)
- Audit log table (nice to have, defer)

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-12 | Initial plan |
