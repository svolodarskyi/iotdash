# IoTDash — Tech Lead Playbook

> **Version:** 0.1.0-draft
> **Date:** 2026-04-12
> **Audience:** You, as the solo tech lead / founder-engineer

---

## 1. Mindset: Solo Tech Lead on a Product Build

You are wearing every hat: architect, backend dev, frontend dev, DevOps, QA. The trap is spending weeks planning and never shipping. The antidote is:

**Ship a vertical slice first. Widen later.**

A vertical slice = one user can log in, see one real device's data on one embedded graph, and create one alert that sends an email. That's your MVP. Everything else is iteration.

---

## 2. The 4 Rules

1. **Never build infrastructure before you have something to deploy.** Get the app working locally in docker-compose first. Azure comes after.
2. **Never build the frontend before the API exists.** Start backend-first. Use Swagger UI as your frontend for the first few days.
3. **Never build auth before you have something to protect.** Hardcode a test user at first. Add real auth once there's a page worth protecting.
4. **Never abstract before you have duplication.** Don't build a "device type plugin system" when you have one sensor type.

---

## 3. Where to Start (Sprint 0, Week 1)

You already have the data pipeline working (EMQX → Telegraf → InfluxDB → Grafana). That's the hard part done. What's missing is the **application layer** on top.

### First-Day Checklist

```
[ ] Init git repo (git init, .gitignore, first commit)
[ ] Restructure into backend/ frontend/ infra/ folders
[ ] Add PostgreSQL to docker-compose.yml
[ ] Scaffold FastAPI project (backend/)
[ ] Create the database schema (Alembic init + first migration)
[ ] Seed one org + one user + one device via a script
[ ] Boot everything: docker compose up
```

That's it. No frontend. No Azure. No CI/CD. Just get a database running alongside your existing stack with one org/user/device in it.

---

## 4. Development Sequence (What to Build, In What Order)

### Sprint 0 — Repo & Local Stack (Week 1-2)

**Goal:** Clean repo, all services running locally, database seeded, backend scaffold with basic CRUD.

**Week 1 — Foundation:**

```
1. git init + .gitignore (Python, Node, .env, docker volumes)
2. Move existing files into structure:
   iotdash/
   ├── backend/
   ├── frontend/          (empty for now)
   ├── infra/             (empty for now)
   ├── grafana/           (existing)
   ├── telegraf.conf      (existing, update topics)
   ├── docker-compose.yml (existing, extend)
   ├── .env.example
   └── docs/
3. Add to docker-compose.yml:
   - postgres service
   - backend service (FastAPI, Dockerfile)
4. backend/:
   - pyproject.toml (fastapi, uvicorn, sqlalchemy, alembic, psycopg2, pydantic)
   - Dockerfile
   - app/main.py → hello world with /api/health
   - alembic init
5. Create first migration with full schema
6. Seed script: python -m app.seed (creates admin org + user + device)
7. Update telegraf.conf to new topic scheme
8. Update fake_device.py to use new topic scheme
9. docker compose up — verify everything connects
```

**Week 2 — Backend Core:**

```
1. SQLAlchemy models matching the schema
2. GET /api/devices → list devices (hardcoded org filter for now)
3. GET /api/devices/{id}/embed-urls → construct Grafana iframe URLs
4. GET /api/organisations/{id} → org details
5. GET /api/organisations/{id}/devices → devices for org
6. Configure Grafana for embedding:
   - GF_SECURITY_ALLOW_EMBEDDING=true
   - GF_AUTH_ANONYMOUS_ENABLED=true
   - GF_AUTH_ANONYMOUS_ORG_NAME=iotorg
7. Test: hit /api/devices/{id}/embed-urls, paste URL in browser,
   see Grafana panel render without login
8. Write basic tests for API endpoints (pytest)
9. Set up linting/formatting (ruff, black)
```

**Sprint Review Deliverable:** `curl localhost:8000/api/health` returns `{"status":"ok"}`. Swagger UI at `localhost:8000/docs` — all endpoints callable. DB has seeded data. Fake device data flows to Grafana. Grafana embed URLs work in browser.

**Why no auth yet:** You need to prove the Grafana embedding works before building login. If embedding breaks, you'll waste time on auth for a broken product.

---

### Sprint 1 — Frontend + Auth (Week 3-4)

**Goal:** User opens browser, logs in, sees only their org's dashboard with embedded Grafana panels.

**Week 3 — Frontend Scaffold + Embed:**

```
1. cd frontend && npm create vite@latest . -- --template react-ts
2. Install: @tanstack/react-router, @tanstack/react-query, zustand, tailwindcss
3. Pages:
   - /dashboard → fetches /api/devices, shows list
   - /dashboard/:deviceId → fetches /api/devices/{id}/embed-urls,
     renders <iframe> for each panel
4. No login page yet — everyone sees everything
5. Add frontend to docker-compose (or just npm run dev locally)
6. Style it minimally — it just needs to not look broken
```

**Week 4 — Authentication:**

```
1. Backend:
   - POST /api/auth/login (bcrypt verify, return JWT in httponly cookie)
   - GET /api/auth/me (decode JWT, return user)
   - POST /api/auth/logout (clear cookie)
   - Auth middleware: extract JWT, inject user context into all routes
   - Scope all queries by user's organisation_id
2. Frontend:
   - /login page (email + password form)
   - Auth store (Zustand — useAuthStore)
   - Protected route wrapper (redirect to /login if no session)
   - Show user name + org in header, logout button
3. Test with two orgs: org A sees device A, org B sees device B
```

**Sprint Review Deliverable:** Open `localhost:5173`, get redirected to login. Log in as user A — see org A's devices with live Grafana embeds. Log out. Log in as user B — see only org B's. This is your **first demo moment**. Screen-record it.

---

### Sprint 2 — Alerts (Week 5-6)

**Goal:** User creates an alert in the web app, Grafana evaluates it, email arrives.

**Week 5 — Alert Backend + Grafana Integration:**

```
1. Backend:
   - CRUD /api/alerts
   - GrafanaClient service (uses Grafana HTTP API with service account token)
   - On alert create/update:
     a. Save to DB
     b. Call Grafana API to create alert rule in user's org
     c. Create/update contact point with user's email
     d. Create notification policy
   - On alert delete: remove Grafana rule + contact point
2. Grafana:
   - Create service account + token (store in .env)
   - Configure SMTP (use Mailhog locally for testing)
   - Test: create alert via API, trigger threshold, check email
3. Add Mailhog to docker-compose for local email testing
```

**Week 6 — Alert Frontend + Polish:**

```
1. Frontend:
   - /alerts page: list alerts with status badges
   - /alerts/new: form (select device, metric, condition, threshold, email)
   - Edit/delete/toggle on existing alerts
2. End-to-end testing of alert lifecycle
3. Error handling for Grafana API failures (retry, surface errors to user)
4. Alert validation (duplicate detection, threshold bounds)
```

**Sprint Review Deliverable:** Create alert "temperature > 30 for sensor01". Modify fake_device.py to send temps > 30. Receive email in Mailhog. Delete alert. Verify Grafana rule removed.

---

### Sprint 3 — Admin Panel + Device Provisioning + Multi-Metric (Week 7-8)

**Goal:** Admin can manage orgs, devices, and users from the web app. Devices are provisioned with selectable metrics (temperature, humidity, engine RPM). Enablement sends MQTT config to devices. Dashboards show one graph per metric. Client onboarding takes 10 minutes.

**Week 7 — Admin Backend + Device Provisioning + MQTT Publisher:**

```
1. Database: migration 002 — metrics catalog table + device_metrics join table
2. Seed: 3 default metrics (temperature, humidity, engine_rpm)
3. Backend admin endpoints (require admin role):
   - CRUD orgs, devices, users
   - Device provisioning: UID auto-gen or manual entry, metric assignment
   - POST /admin/devices/{id}/send-config — (re)send MQTT config to device
4. MQTT publisher service (paho-mqtt):
   - Publishes {device_code}/to/config with {"addMetrics": [...]}
   - Fire on auto-enable at provision time, or manual "Re-send Config"
5. Admin middleware: require admin role for /admin/* routes
6. Parametric Grafana dashboard: iot-metrics.json with $device_id + $metric variables
7. Updated embed URL logic: one URL per enabled metric per device
8. GET /api/metrics — public metrics catalog for dashboard + alert forms
```

**Week 8 — Admin Frontend + Multi-Metric Dashboard:**

```
1. Frontend /admin section:
   - Org management (list + create/edit/delete)
   - User management (list + create/edit/deactivate, org filter)
   - Device provisioning (UID toggle auto/manual, metric checkboxes,
     auto-enable checkbox, "Re-send Config" button)
2. Updated device detail page:
   - Metric selector pills (show one or all enabled metrics)
   - One Grafana iframe per selected metric
3. Role-based UI: admin sees /admin nav item, viewers don't
4. Updated fake_device.py: subscribes to config topic, starts multi-metric
5. ~20 admin + metrics tests (~62 total backend tests)
6. Sprint docs: decisions, features, manual QA
```

**Sprint Review Deliverable:** Admin provisions "Humidity Sensor" with temperature + humidity → MQTT config sent → fake device starts sending both → dashboard shows 2 graphs. Create org "Beta Corp", add user, add device. Login as that user → see their dashboard. Full client onboarding in <10 minutes.

---

### Sprint 4 — Soak Test Deployment + CI/CD (Week 9-10)

**Goal:** Deploy the full stack to Azure for a multi-week soak test with 1000 simulated devices at 5-second intervals (~200 msg/s). Find memory leaks, disk growth, connection instability, and breaking points before committing to a production architecture.

**Why soak test before production deploy?** We need answers about InfluxDB compaction behavior, EMQX memory growth under sustained load, and disk growth rates. These determine the production VM size, retention policies, and monitoring thresholds. Cheaper to learn on a single VM than to discover problems in a Container Apps deployment.

**Week 9 — Infrastructure as Code + Production Images:**

```
1. Terraform (infra/soak-test/):
   - Resource group, VNet + subnet
   - NSG: SSH (restricted IP), MQTT, backend, frontend, Grafana, EMQX
   - D2s_v5 VM (2 vCPU, 8 GB, no CPU credit throttling)
   - 128 GB Premium SSD, cloud-init automated setup
   - Cost: ~EUR 4/day (~EUR 110-130/month)
2. Production Dockerfiles:
   - backend/Dockerfile.prod: multi-stage, gunicorn + uvicorn workers
   - frontend/Dockerfile.prod: multi-stage, npm build → nginx
3. docker-compose.soak.yml: memory limits for 8 GB VM, mailhog disabled
4. telegraf.soak.conf: batch_size=10000, flush_interval=5s, gzip
5. Async device simulator (tools/soak_simulator.py):
   - 1000 devices, 5s interval, staggered ramp, reconnect backoff
   - Matches existing fake_device.py MQTT schema
```

**Week 10 — CI/CD + Monitoring + Stress Testing:**

```
1. GitHub Actions:
   - soak-deploy.yml: build images → push to GHCR → SSH deploy to VM
   - soak-collect.yml: weekly download of soak-metrics.csv as artifact
2. Monitoring (cron on VM):
   - soak_monitor.sh (every 5 min): system + container + EMQX + InfluxDB metrics → CSV
   - soak_alerter.sh (every 15 min): container restarts, disk >80%, RAM >90%,
     EMQX connection drops → webhook alert
3. Performance test phases:
   - Day 1: baseline (30-50% CPU, 5-6 GB RAM, ~200 msg/s)
   - Days 2-14: stability soak (watch memory growth, compaction storms)
   - Day 14+: stress tests (connection storms, service restarts, memory pressure)
   - Day 14+: capacity ceiling (increase devices until breaking point)
4. Teardown: infra/soak-test/teardown.sh (terraform destroy)
```

**Sprint Review Deliverable:** VM running full stack with 1000 simulated devices. Grafana shows live data. Metrics CSV collecting every 5 minutes. CI/CD deploys new images via GitHub Actions. Baseline performance recorded. First week of soak data analyzed.

---

### Sprint 5 — Hardening + Production Readiness (Week 11-12)

**Goal:** Production-grade security, reliability, and observability.

**Week 11 — Security:**

```
- MQTT device auth (EMQX username/password per device)
- HTTPS everywhere (Azure managed certs)
- Rate limiting on API (slowapi)
- Input validation hardening
- Password reset flow (email link)
- CORS configuration
- Security headers (CSP, HSTS)
```

**Week 12 — Reliability + Observability:**

```
- Structured logging (JSON, correlation IDs)
- Monitoring (Azure Log Analytics + alerts)
- Health check endpoints for all services
- Backup strategy (PostgreSQL pg_dump, InfluxDB backup)
- Error tracking (Sentry or similar)
- Load testing (k6 or locust — simulate 100 devices)
- Documentation: runbook for common operations
```

**Sprint Review Deliverable:** All OWASP top-10 mitigated. Monitoring dashboard shows system health. Backups run nightly. Runbook covers incident response. **MVP is complete.**

---

## 5. Sprint Cadence

**Sprint length:** 2 weeks (10 working days)

| Sprint   | Weeks | Focus                                          | Demo Deliverable                  |
| -------- | ----- | ---------------------------------------------- | --------------------------------- |
| Sprint 0 | 1-2   | Repo, local stack, backend CRUD, Grafana embed | Swagger UI + working embed URLs   |
| Sprint 1 | 3-4   | Frontend, auth, multi-org isolation            | Login → see org's live dashboards |
| Sprint 2 | 5-6   | Alert system (backend + Grafana + frontend)    | Create alert → receive email      |
| Sprint 3 | 7-8   | Admin panel, device provisioning, multi-metric | Provision device + multi-metric dashboard |
| Sprint 4 | 9-10  | Soak test deployment, CI/CD, perf testing      | 1000 devices soak running in Azure |
| Sprint 5 | 11-12 | Security hardening, monitoring, backups        | **MVP complete**                  |

**Sprint ceremonies (keep lightweight):**

- **Sprint Planning** (Day 1, 1 hour): Pick tasks for the sprint, define sprint goal
- **Daily standup** (async, 5 min): Write 3 bullets in a log — done/doing/blocked
- **Sprint Review** (Day 10, 30 min): Demo the deliverable, screen-record it
- **Retro** (Day 10, 15 min): One thing that went well, one thing to change

**Total timeline:** ~12 weeks (3 months) to production-ready MVP.

---

## 6. How to Start Deving Right Now (Literally Today)

**Step 1:** Initialize the repo.

```bash
cd /Users/erfolg/Documents/projects/iotdash
git init
```

**Step 2:** Create `.gitignore`.

**Step 3:** Create the backend scaffold.

```bash
mkdir -p backend/app/{api,models,schemas,services,core}
mkdir -p backend/alembic
mkdir -p frontend
mkdir -p infra
```

**Step 4:** Add PostgreSQL to `docker-compose.yml`:

```yaml
postgres:
  image: postgres:16
  container_name: postgres
  ports:
    - "5432:5432"
  environment:
    POSTGRES_DB: iotdash
    POSTGRES_USER: iotdash
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-localdev123}
  volumes:
    - postgres_data:/var/lib/postgresql/data
  networks:
    - iot_net
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U iotdash"]
    interval: 5s
    timeout: 3s
    retries: 10
```

**Step 5:** Write the FastAPI hello world (`backend/app/main.py`):

```python
from fastapi import FastAPI

app = FastAPI(title="IoTDash API")

@app.get("/api/health")
def health():
    return {"status": "ok"}
```

**Step 6:** `docker compose up`. Verify health endpoint. First commit.

That's your starting point. Everything else follows from the sprint sequence above. You've got 2 weeks for Sprint 0 — no rush on day one, but aim to have the full backend CRUD + embed URLs working by the end of week 2.

---

## 7. Decision Log

Track every non-trivial decision here as you go. Future you will thank present you.

| #   | Date       | Decision                                             | Rationale                                                  | Revisit?       |
| --- | ---------- | ---------------------------------------------------- | ---------------------------------------------------------- | -------------- |
| D1  | 2026-04-12 | FastAPI for backend                                  | Python already in use, async, auto OpenAPI docs            | No             |
| D2  | 2026-04-12 | React + Vite + Zustand + TanStack Router/Query       | Type-safe routing, declarative data fetching, simple state | No             |
| D3  | 2026-04-12 | Tag-based InfluxDB isolation (not bucket-per-org)    | Simpler, adequate for embedded model                       | At 50+ orgs    |
| D4  | 2026-04-12 | Grafana public with anonymous access for embed       | Simpler than proxying, acceptable for MVP                  | At prod launch |
| D5  | 2026-04-12 | MQTT topic: `{device_id}/{direction}/{message_type}` | Clean separation, extensible                               | No             |
| D6  |            |                                                      |                                                            |                |

---

## 8. Risk Register

| Risk                                                       | Likelihood | Impact   | Mitigation                                                                             |
| ---------------------------------------------------------- | ---------- | -------- | -------------------------------------------------------------------------------------- |
| Grafana iframe embed blocked by browser CORS/CSP           | Medium     | High     | Test on Day 6 before building more frontend. Set `allow_embedding`, `cookie_samesite`. |
| Grafana Alerting API doesn't support all needed operations | Medium     | High     | Prototype alert creation on Day 12 before building alert UI.                           |
| Azure Container Apps TCP ingress for MQTT has limitations  | Medium     | Medium   | Test MQTT connectivity early in Sprint 6. Fallback: Azure IoT Hub or VM for EMQX.      |
| InfluxDB performance with tag-based multi-tenancy at scale | Low        | Medium   | Monitor query latency. Revisit bucket-per-org if >50 orgs.                             |
| Solo developer burnout                                     | High       | Critical | Ship vertical slice fast, demo it, get validation. Don't gold-plate.                   |

---

## 9. What NOT to Build Yet

Resist the urge to build these until MVP is proven:

| Thing                                 | Why Not Yet                                                    |
| ------------------------------------- | -------------------------------------------------------------- |
| Device type plugin system             | You have one sensor type. Hardcode it.                         |
| User self-registration                | Admin creates users for now. 5 clients don't need self-serve.  |
| Mobile app                            | Responsive web is enough.                                      |
| Real-time WebSocket dashboard updates | Grafana iframe auto-refreshes. Good enough.                    |
| Multi-region deployment               | You don't have users in multiple regions yet.                  |
| Kubernetes                            | Container Apps is simpler. Move to AKS only if you outgrow it. |
| Microservices                         | Monolith backend. Split when you have a reason, not before.    |
| OAuth / SSO / SAML                    | Password login. Add SSO when an enterprise client requires it. |
| Custom charting library               | Grafana does the charting. Don't rebuild it.                   |
| Billing / subscription management     | Invoice manually. Build billing at 20+ clients.                |

---

## 10. Client Onboarding Checklist (Admin Workflow)

Once MVP is done, this is how you onboard a new client:

```
1. Admin panel → Create Organisation "ClientName"
   (backend auto-creates Grafana org + datasource + dashboards)

2. Admin panel → Add Device(s) to org
   - device_code: the ID the physical device will use in MQTT topics
   - device_type: temperature (or other)

3. Admin panel → Add User(s) to org
   - email, temporary password, role=viewer

4. Configure physical IoT device:
   - MQTT broker: mqtt.yourdomain.com:1883
   - Topic: {device_code}/from/message
   - Payload: {"temperature": 22.5}

5. Verify: log in as client user, see data flowing on dashboard

6. Client sets alerts in web app as needed
```

Time to onboard a client: ~10 minutes (once platform is running).

---

## 11. Definition of Done — MVP

The MVP is done when ALL of these are true:

- [ ] A client user can log in with email + password
- [ ] They see only their organisation's devices
- [ ] Each device shows embedded Grafana panels with live data
- [ ] They can create an alert (metric > threshold → email)
- [ ] They receive an email when the alert fires
- [ ] Admin can create orgs, devices, users from the admin panel
- [ ] Everything runs in Azure Container Apps
- [ ] CI/CD deploys on push to main
- [ ] Secrets are in Azure Key Vault (not in code)
- [ ] A real IoT device (or simulator) sends data through the pipeline

Once all boxes are checked, you have a product you can sell.

---

_Companion to [`PLANNING.md`](./PLANNING.md), [`ARCHITECTURE.md`](./ARCHITECTURE.md), and [`API-SPEC.md`](./API-SPEC.md)._
