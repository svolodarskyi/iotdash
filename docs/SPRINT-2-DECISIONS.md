# Sprint 2 — Technical Decisions

## 1. Grafana Provisioning API for Alert Rules

**Decision:** Use Grafana's Provisioning API (`/api/v1/provisioning/alert-rules`) rather than the Ruler API.

**Why:** The Provisioning API works with Grafana's built-in alertmanager out of the box — no Cortex/Mimir backend required. It supports full CRUD for alert rules, contact points, and notification policies. The `X-Disable-Provenance` header allows the backend to own these resources programmatically while still allowing manual inspection in the Grafana UI.

## 2. Mailhog for Local Email Testing

**Decision:** Added Mailhog container to docker-compose. Grafana's SMTP points to `mailhog:1025`. Mailhog web UI at `localhost:8025`.

**Why:** Real SMTP (SendGrid, SES) is unnecessary for development and costs money. Mailhog catches all outbound email in a web inbox, making it trivial to verify alert emails arrive with correct content. No configuration, no API keys, no risk of accidentally emailing real users.

**Production:** Replace Mailhog with Azure Communication Services or SendGrid (Sprint 4 Azure deployment).

## 3. Grafana Basic Auth from Backend

**Decision:** Backend calls Grafana API using basic auth (`admin:admin`) via `GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD` env vars. No service account token.

**Why:** For MVP, basic auth is simpler — one fewer secret to manage. The backend runs on the same Docker network as Grafana (internal access only). Service account tokens add complexity (creation, rotation, scope management) that isn't justified until production. The admin credentials are already in docker-compose for Grafana's own login.

**Production:** Switch to a Grafana service account token with minimal scoped permissions (Sprint 4).

## 4. httpx for Backend HTTP Client

**Decision:** Use `httpx` (already in requirements.txt) for backend → Grafana API calls.

**Why:** httpx is the modern Python HTTP client — cleaner API than `requests`, supports both sync and async, handles timeouts well, and is widely used in the FastAPI ecosystem. It was already listed as a dependency, so no new install needed.

## 5. Synchronous Grafana Sync on Alert CRUD

**Decision:** When a user creates/updates/deletes an alert, the backend immediately calls Grafana's API in the same request. No background queue.

**Why:** At MVP scale (single-digit users, single-digit alerts), the extra latency of a Grafana API call (~100-200ms) is acceptable. A background task queue (Celery, Redis, etc.) adds significant infrastructure complexity for no user-visible benefit at this scale. If Grafana is unreachable, the alert is saved to the database without a Grafana rule, and logged as a warning.

**Revisit:** If alert creation latency exceeds 2 seconds or Grafana reliability becomes an issue, add a background sync worker.

## 6. Notification Routing via Labels

**Decision:** Each alert rule gets a label `iotdash_alert_id={uuid}`. A notification policy child route matches this label and routes to a contact point `alert-{uuid}`.

**Why:** Without per-alert routing, all alerts would fire to the default contact point (the Grafana admin email). The label-based approach means each alert has its own email recipient. When an alert is deleted, its route and contact point are cleaned up. This scales cleanly — 100 alerts means 100 independent routing paths, each with its own email.

## 7. Graceful Grafana Failure

**Decision:** If Grafana API calls fail during alert creation, the alert is still saved to the database (with `grafana_rule_uid = null`) and a warning is logged.

**Why:** The database is the source of truth. Grafana sync is a side effect. If Grafana is temporarily down (restart, health check), users shouldn't lose their alert configuration. A future admin sync endpoint (Sprint 3) can reconcile any mismatches. The frontend shows `grafana_rule_uid` status so users can see if sync succeeded.

## 8. FastAPI Dependency Override for Grafana Mock in Tests

**Decision:** Tests use `app.dependency_overrides[get_grafana_client]` to inject a `MagicMock` instead of `@patch` decorators.

**Why:** The Grafana client is injected via `Depends(get_grafana_client)` in route handlers. FastAPI resolves dependencies at the framework level, so `unittest.mock.patch` on the module path doesn't intercept the dependency injection. `dependency_overrides` is FastAPI's official mechanism for this and works reliably. The mock is created once in a `conftest.py` fixture and shared across all tests.

## 9. Dynamic Datasource UID Lookup

**Decision:** `GrafanaClient.get_datasource_uid()` queries `GET /api/datasources` at runtime to find the InfluxDB datasource UID, rather than hardcoding it.

**Why:** Grafana assigns internal UIDs to provisioned datasources (e.g. `P951FEA4DE68E13C5`), which differ from the logical name (`InfluxDB`). Hardcoding a UID would break across environments or after a `docker compose down -v`. The lookup adds one extra HTTP call per alert sync but guarantees the correct UID regardless of environment.

## 10. Flux Query Filters Match Telegraf Tags Only

**Decision:** The Flux query in alert rules filters on `device_id` and `_field` only — no `message_type` filter.

**Why:** Telegraf's `topic_parsing` configuration extracts `device_id` from the MQTT topic (`+/from/message`) and adds `topic` and `host` as tags. There is no `message_type` tag in the data. An earlier version included `filter(fn: (r) => r.message_type == "message")` which silently matched zero rows, causing Grafana to report `NoData` for every rule. Removed to match the actual tag schema.

**Lesson:** Always verify Flux queries against real InfluxDB data before embedding them in alert rules. A filter on a non-existent tag returns empty results without error.

## 11. Automatic Grafana Re-sync on Update/Toggle

**Decision:** When updating or toggling an alert that has `grafana_rule_uid = null`, the backend creates the Grafana rule (+ contact point + notification policy) instead of skipping the sync.

**Why:** Under the graceful failure model (Decision 7), alerts can exist in the database without a Grafana rule if Grafana was unreachable at creation time. The original code only synced updates `if alert.grafana_rule_uid` — meaning orphaned alerts could never be recovered without a dedicated admin endpoint. Now any update or toggle acts as an automatic re-sync, creating the missing Grafana resources on the fly. This eliminates the need for a separate reconciliation mechanism.

## 12. Alert Org Scoping via Device Join

**Decision:** Alert queries join through `Device` to check `Device.organisation_id == current_user.organisation_id`. Alerts don't have their own `organisation_id` column.

**Why:** Alerts belong to devices, and devices belong to organisations. Adding a redundant `organisation_id` to the alerts table would create a denormalization that could drift out of sync. The join is cheap (indexed FK) and enforces the invariant at the data model level — an alert can never reference a device from a different org.
