# Sprint 0 — Feature Accomplishments & Business Context

## What was accomplished

| # | Feature | Business Value |
|---|---------|---------------|
| 1 | **Full IoT data pipeline running locally** (EMQX → Telegraf → InfluxDB → Grafana) | Proves the core product works: a physical device can send data and it appears on a dashboard in real time. This is the foundational value proposition — without it, nothing else matters. |
| 2 | **PostgreSQL database with schema for orgs, users, devices, dashboards, alerts** | The application data model is production-ready. Multi-tenant structure (org → devices, org → users) is in place, meaning the platform can serve multiple clients from day one once auth is added. |
| 3 | **REST API with read endpoints** (health, devices, organisations, embed URLs) | The backend can serve data to any frontend — web app, mobile app, or third-party integration. Swagger UI at `/docs` already lets stakeholders explore the API and see what's possible. |
| 4 | **Grafana iframe embedding with anonymous access** | A client's dashboard can be shown inside our own web app, not just inside Grafana. This is critical for the product — clients see a branded IoT dashboard, not a generic Grafana instance. |
| 5 | **Seed data (Demo Corp, 2 sensors)** | Demo-ready in one command. Any stakeholder can `docker compose up`, run the seed, and see a working system with realistic data. Useful for investor demos, sales calls, and onboarding new team members. |
| 6 | **Updated MQTT topic scheme** (`{device_id}/from/message`) | Future-proof topic structure. Supports bidirectional communication (device-to-cloud and cloud-to-device commands), multiple message types, and cleaner device identification. |
| 7 | **Automated test suite (13 tests)** | Reduces regression risk as the product evolves. Every Sprint 1+ change runs against these tests, catching broken endpoints before they reach production. |
| 8 | **Docker-based development environment** | Any developer (or future hire) can clone the repo, run `docker compose up`, and have the entire platform running in minutes. Zero "works on my machine" issues. |

---

## What this allows from a business perspective

**Right now (with Sprint 0 alone), you can:**
- Demo the data pipeline to investors or potential clients using Grafana + Swagger UI
- Show that device data flows from sensor → broker → database → dashboard in real time
- Let technical evaluators explore the API via Swagger UI
- Prove multi-tenant data isolation design (org → device relationship)

**What you cannot do yet (and why):**
- Users cannot log in — no authentication exists. Anyone who knows the URL sees everything.
- There is no web frontend — the API works but end users need a browser-friendly interface.
- Alerts cannot be created — the alert table exists but there's no create/edit API or Grafana integration.
- Admins cannot onboard new clients — no admin panel or provisioning workflow.
- Nothing is deployed to the cloud — everything runs on localhost.

---

## How each gap gets closed in upcoming sprints

| Gap | Resolved In | What Gets Built | Business Outcome |
|-----|------------|-----------------|-----------------|
| **No login / auth** | Sprint 1 (Week 3-4) | JWT authentication, login/logout endpoints, org-scoped queries, protected routes | Each client sees only their own data. Platform is secure enough for real users. |
| **No web frontend** | Sprint 1 (Week 3-4) | React app with device list page, embedded Grafana iframes per device | First "wow" demo moment — client logs in, sees their live dashboard in a branded web app. |
| **No alert system** | Sprint 2 (Week 5-6) | Alert CRUD API, Grafana alert rule integration, email notifications via SMTP | Clients can set "email me if temperature > 30" — the primary paid feature that justifies the platform subscription. |
| **No admin panel** | Sprint 3 (Week 7-8) | Admin CRUD for orgs/devices/users, Grafana org auto-provisioning, onboarding wizard | Client onboarding drops to <10 minutes. Scales from 1 client to 50 without custom setup work per client. |
| **No cloud deployment** | Sprint 4 (Week 9-10) | Terraform for Azure Container Apps, CI/CD via GitHub Actions, DNS + HTTPS | Product is accessible at `app.yourdomain.com`. Clients can access it from anywhere. Automated deploys on every merge to main. |
| **No security hardening** | Sprint 5 (Week 11-12) | MQTT device auth, rate limiting, HTTPS, structured logging, backups, monitoring | Production-grade reliability. Meets enterprise security expectations. **MVP is complete.** |

---

## Sprint-over-sprint value accumulation

```
Sprint 0  →  "It works" (data pipeline + API + DB)
Sprint 1  →  "It's usable" (login + frontend + multi-tenant)
Sprint 2  →  "It's valuable" (alerts + email = the paid feature)
Sprint 3  →  "It's scalable" (admin panel = fast client onboarding)
Sprint 4  →  "It's accessible" (cloud deploy = anyone can use it)
Sprint 5  →  "It's sellable" (security + reliability = enterprise-ready)
```

Each sprint builds on the previous one. Nothing in Sprint 0 gets thrown away — it becomes the foundation that every future sprint enhances.
