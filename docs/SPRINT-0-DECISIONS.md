# Sprint 0 — Architecture Decisions & Code Review Guide

This document captures the key design decisions, trade-offs, and rationale behind the Sprint 0 implementation. It serves as a reference for reviewers assessing the dev work.

---

## 1. Technology Choices

### PostgreSQL 16 (relational DB)
**Decision:** Use PostgreSQL for application data (orgs, users, devices, dashboards, alerts).
**Rationale:** The application data is relational with foreign-key constraints (org → devices, device → alerts). InfluxDB remains for time-series sensor data. PostgreSQL gives us JSONB for flexible fields (device metadata, panel_ids) without a separate document store.
**Alternative considered:** SQLite — rejected because it lacks UUID support, JSONB, and concurrent writes needed in production.

### SQLAlchemy 2.x + Alembic
**Decision:** Use SQLAlchemy ORM with declarative mapped_column style and Alembic for migrations.
**Rationale:** SQLAlchemy 2.x mapped_column provides type-safe column definitions. Alembic gives version-controlled, reversible migrations. The migration runs on container start so the DB is always up-to-date.
**Trade-off:** Hand-written migration (001_initial_schema.py) instead of autogenerate, to keep full control over the DDL.

### FastAPI
**Decision:** FastAPI for the backend REST API.
**Rationale:** Native async support, automatic OpenAPI/Swagger docs, Pydantic validation, dependency injection for DB sessions. Matches the team's Python ecosystem.

### Pydantic Settings
**Decision:** Use pydantic-settings for configuration management.
**Rationale:** Type-safe env var parsing, `.env` file support, and validation at startup — fails fast if config is missing.

---

## 2. Project Structure Decisions

### Flat app layout (not nested packages)
**Decision:** Single `app/` package with `models.py`, `schemas.py`, `config.py` at the top level, and `routers/` sub-package.
**Rationale:** With only 5 models and 3 routers, a domain-driven nested structure would be over-engineering. Easy to refactor into domains later if the app grows.

### Separate schemas from models
**Decision:** `models.py` contains SQLAlchemy ORM models, `schemas.py` contains Pydantic response models.
**Rationale:** Clear separation between database layer and API contract. Prevents leaking internal fields (e.g., password_hash) in API responses.

### Seed script as a module
**Decision:** `python -m app.seed` rather than a management command or fixture.
**Rationale:** Simple, zero dependencies beyond the app itself. Idempotent (checks if data exists before inserting). Easy to run in any environment.

---

## 3. Database Schema Decisions

### UUIDs as primary keys
**Decision:** All tables use UUID v4 primary keys with `gen_random_uuid()` server default.
**Rationale:** Prevents enumeration attacks on API endpoints, safe for multi-tenant future, no collision risk in distributed systems. PostgreSQL has native UUID type.
**Trade-off:** Slightly larger index size vs. integer PKs. Acceptable at this scale.

### ORM uses generic `Uuid`; migration uses PostgreSQL `UUID`
**Decision:** ORM models use SQLAlchemy's generic `Uuid` type, while Alembic migration uses `sqlalchemy.dialects.postgresql.UUID`.
**Rationale:** Generic `Uuid` works on both PostgreSQL and SQLite, enabling fast in-memory tests. The migration runs only against PostgreSQL, so it uses the dialect-specific type for correctness.

### JSONB for metadata and panel_ids
**Decision:** Device `metadata` and GrafanaDashboard `panel_ids` use JSONB columns in PostgreSQL.
**Rationale:** These fields have variable structure per device type or dashboard. JSONB allows querying inside the JSON while keeping schema flexibility.
**Note:** `metadata_` attribute name in Python (with trailing underscore) avoids shadowing SQLAlchemy's internal `metadata`. The DB column is named `metadata`.
**Note:** ORM uses `JSON().with_variant(JSONB(), "postgresql")` for cross-dialect compatibility in tests.

### Timestamps with timezone
**Decision:** All tables have `created_at` and `updated_at` with `DateTime(timezone=True)`.
**Rationale:** Timezone-aware timestamps prevent timezone bugs. `server_default=func.now()` ensures consistency. `onupdate=func.now()` on `updated_at` tracks modifications.

### No cascade deletes
**Decision:** Foreign keys do not cascade on delete.
**Rationale:** Prefer explicit handling of deletions to prevent accidental data loss. Soft-delete (`is_active` flag) is the intended pattern for devices and users.

---

## 4. API Design Decisions

### URL structure: `/api/` prefix
**Decision:** All endpoints prefixed with `/api/` (e.g., `/api/devices`, `/api/health`).
**Rationale:** Clean separation when frontend is served from the same domain. Standard REST convention.

### Read-only endpoints for Sprint 0
**Decision:** Only GET endpoints implemented. No POST/PUT/DELETE.
**Rationale:** Sprint 0 focuses on infrastructure and data pipeline. Write operations depend on authentication (Sprint 1). Seed script handles initial data.

### Embed URLs constructed server-side
**Decision:** `/api/devices/{id}/embed-urls` builds Grafana iframe URLs on the backend.
**Rationale:** The frontend doesn't need to know Grafana URL structure. The backend can apply per-org or per-device filtering to which dashboards/panels are visible.

### CORS allow-all for development
**Decision:** `allow_origins=["*"]` in CORS middleware.
**Rationale:** Development convenience. Will be locked down to specific origins in production (Sprint 2+).

---

## 5. Testing Decisions

### SQLite in-memory for tests
**Decision:** Tests use SQLite in-memory DB, not PostgreSQL.
**Rationale:** Zero setup, fast execution, no Docker dependency for running tests locally. Tests validate API logic and routing, not PostgreSQL-specific features.
**Trade-off:** JSONB columns default to JSON (SQLite handles this transparently via SQLAlchemy). UUID columns work as strings in SQLite. If PostgreSQL-specific behavior matters, integration tests against a real PostgreSQL instance should be added later.

### Fixture-based seeding
**Decision:** Test data injected via pytest fixtures (`seed_data`), not by calling the seed script.
**Rationale:** Test isolation — each test gets a fresh DB. Deterministic UUIDs for assertions.

### TestClient (synchronous)
**Decision:** Use FastAPI's `TestClient` (sync) rather than `AsyncClient`.
**Rationale:** All current endpoints are synchronous. TestClient is simpler and sufficient. Async test support can be added when async endpoints are introduced.

---

## 6. Docker & DevEx Decisions

### Volume mount for hot-reload
**Decision:** `./backend:/app` volume mount + `--reload` flag on uvicorn.
**Rationale:** Code changes reflect immediately without rebuilding the container. Standard practice for Python dev containers.

### Entrypoint migration strategy
**Decision:** Migrations run via manual `alembic upgrade head` (documented in QA checklist) rather than an auto-running entrypoint script.
**Rationale:** Explicit control during development. Prevents migration conflicts when multiple developers work on schema changes. For production, an entrypoint script or CI/CD step is recommended.

### Grafana embedding env vars
**Decision:** `GF_SECURITY_ALLOW_EMBEDDING=true` and anonymous auth enabled.
**Rationale:** Required for iframe embedding of Grafana panels in the frontend. Anonymous access scoped to `iotorg` org. In production, this should use Grafana auth proxy or API keys instead.

---

## 7. MQTT Topic Scheme Change

### Old: `sensors/{device_id}/temperature`
### New: `{device_id}/from/message`

**Decision:** Change MQTT topic scheme to `{device_id}/from/message`.
**Rationale:** More generic — supports multiple message types beyond temperature. The `from` direction indicates device-to-cloud messages. Future `{device_id}/to/command` enables cloud-to-device commands. Aligns with IoT hub conventions.

---

## 8. What's NOT in Sprint 0 (and why)

| Deferred Item | Reason |
|---|---|
| Authentication (JWT/OAuth) | Sprint 1 — requires frontend integration |
| Write API endpoints (POST/PUT/DELETE) | Sprint 1 — depends on auth |
| Frontend (React + TanStack Router/Query + Zustand) | Sprint 1 |
| CI/CD pipeline | Sprint 2 — needs cloud infrastructure |
| MQTT device authentication | Sprint 2 — requires device provisioning flow |
| Audit log table | Nice-to-have — no current requirement |
| Multi-tenancy isolation | Sprint 2 — single-tenant deployment first |

---

## Review Checklist for Assessors

- [ ] **Models match schema spec** — compare `models.py` with PLANNING.md Section 6.2
- [ ] **Migration is reversible** — `downgrade()` drops tables in correct dependency order
- [ ] **API responses don't leak internals** — no `password_hash`, no internal IDs without purpose
- [ ] **Test coverage** — all endpoints have happy-path and error-case tests
- [ ] **No hardcoded secrets** — all config via env vars / `.env.example`
- [ ] **Docker setup reproducible** — `docker compose up --build` works from a clean clone
- [ ] **Idempotent seed** — running seed twice doesn't crash or duplicate data
- [ ] **Linting clean** — `ruff check .` passes with zero warnings
