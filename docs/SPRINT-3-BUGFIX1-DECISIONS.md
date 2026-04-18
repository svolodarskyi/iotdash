# Sprint 3 Bugfix 1 — Technical Decisions

## 1. Admin = Platform Owner, Clients = Viewer Only

**Decision:** Removed the `role` field from `UserCreate` and `UserUpdate` schemas entirely. The backend hardcodes `role="viewer"` when creating users via the admin API. Role cannot be changed via any API endpoint.

**Why:** The original Sprint 3 implementation allowed admins to create other admins and change user roles via the UI. This was a security gap — any admin could escalate a client user to admin, giving them full platform access. Admins should be platform owners only, provisioned directly in the database or via seed. Client users are always viewers.

**Impact:** The `role` field was removed from:
- `UserCreate` schema (backend + frontend type)
- `UserUpdate` schema (backend + frontend type)
- Create user form (frontend — role dropdown removed)
- Edit user form (frontend — role dropdown removed)
- `update_user` endpoint (role assignment line removed)

## 2. Platform Organisation for Admin Users

**Decision:** Created a dedicated "Platform" organisation in seed data. The admin user (`admin@iotdash.com`) belongs to the Platform org. Client organisations (Demo Corp, Acme IoT) only contain viewer users.

**Why:** Previously the admin user lived inside Demo Corp, blurring the line between platform operators and client users. The Platform org makes the boundary explicit — admin users belong to the platform, client users belong to their organisation. This also means Demo Corp and Acme IoT are clean examples of client tenants with no admin-level users.

**Seed credentials changed:**
- Admin: `admin@iotdash.com` / `admin123` (was `admin@democorp.com`)
- Demo Corp viewer: `viewer@democorp.com` / `viewer123` (new)
- Acme IoT viewer: `viewer@acmeiot.com` / `viewer123` (unchanged)

## 3. Admin Device Filters via Query Params

**Decision:** Added `device_type` and `metric_name` as optional query parameters to `GET /api/admin/devices`. All three filters (org_id, device_type, metric_name) use AND logic.

**Why:** With growing device counts across multiple orgs, the admin devices table needed better filtering to find specific devices quickly. Filtering server-side keeps the API consistent and avoids loading all devices to filter client-side.

**Implementation detail:** The `metric_name` filter joins through `DeviceMetric → Metric` which can produce duplicate rows. A post-query deduplication step (set-based on device ID) ensures unique results. This is simpler and more correct than `DISTINCT` with eager-loaded relationships.

## 4. Device Types Endpoint

**Decision:** Added `GET /api/admin/devices/device-types` which returns distinct device type strings from the Device table.

**Why:** The device type filter dropdown needs to be populated dynamically. Rather than hardcoding device types in the frontend or extracting them client-side from loaded devices (which would miss types not in the current page/filter), a dedicated endpoint returns the full list from the database.

**Route ordering:** The `/device-types` route is registered before the `/{device_id}` catch-all to avoid FastAPI treating "device-types" as a UUID path parameter.

## 5. Grafana Organisation Auto-Provisioning

**Decision:** When an admin creates a new organisation, the backend automatically provisions a Grafana org with an InfluxDB datasource and the default IoT Metrics dashboard.

**Why:** Previously, creating an org in the admin UI only created a Postgres record. The Grafana org, datasource, and dashboard had to be set up manually or were missing entirely. This meant new client organisations couldn't view dashboards until someone manually configured Grafana. Auto-provisioning eliminates this gap — a new org is fully functional immediately.

**Implementation:** Three new methods on `GrafanaClient`:
- `create_org(name)` — `POST /api/orgs`, returns Grafana org ID
- `add_datasource_to_org(org_id)` — creates InfluxDB datasource using `X-Grafana-Org-Id` header
- `create_dashboard_in_org(org_id, dashboard_json)` — creates dashboard from template

The `_org_request` helper is a variant of `_request` that adds the `X-Grafana-Org-Id` header for org-scoped operations. This avoids switching the admin user's active org.

## 6. Graceful Grafana Failure on Org Creation

**Decision:** If Grafana provisioning fails during org creation, the organisation is still created in Postgres (without `grafana_org_id`). A warning is logged.

**Why:** Consistent with the Sprint 2 pattern for alert sync (Decision 7 in Sprint 2). The database is the source of truth. Grafana provisioning is a side effect that can be retried. If Grafana is starting up or temporarily unreachable, the admin shouldn't lose their org creation. The org will work for user/device management even without Grafana, and the dashboard can be provisioned later.

## 7. Dashboard Template Loaded from File

**Decision:** The `create_org` endpoint reads `iot-metrics.json` from disk to get the dashboard template, resets `id` to `null`, and posts it to Grafana's dashboard API.

**Why:** The dashboard JSON is already maintained as a provisioning file for Grafana's file-based provisioning. Reusing the same file ensures consistency — any dashboard changes (new panels, updated queries) automatically apply to newly provisioned orgs. No need to maintain a separate dashboard definition in Python code.
