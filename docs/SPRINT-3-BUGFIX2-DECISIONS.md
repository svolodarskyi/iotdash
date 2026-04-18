# Sprint 3 Bugfix 2 — Technical Decisions

## 1. Data Model Restructure: DeviceType as First-Class Entity

**Decision:** Introduced `device_types` and `device_type_metrics` tables. Renamed `devices` → `devices_provisioned` and `device_metrics` → `device_provisioned_metrics`. Replaced the free-text `device_type` VARCHAR column with a `device_type_id` UUID FK.

**Why:** The original `device_type` was a free-text string on the device — no validation, no constraint on which metrics a device type supports, and no way to manage device types as a catalog. With the new schema, device types define *allowed* metrics (`device_type_metrics`), and provisioned devices can only enable a subset of those (`device_provisioned_metrics`). The invariant `device_provisioned_metrics ⊆ device_type_metrics` is enforced at the API level on both provision and metric update endpoints.

**Impact:** Cascaded through the entire stack — models, schemas, all routers referencing devices/metrics, seed data, test fixtures, frontend types, hooks, and components. Migration 003 handles the rename + backfill from existing data.

## 2. Metric Subset Validation on Provision and Update

**Decision:** When provisioning a device or updating its metrics, the backend validates that all requested metric IDs exist in `device_type_metrics` for the device's type. Invalid metrics return HTTP 400 with a clear error message listing the rejected metric IDs.

**Why:** Without this validation, a device could be assigned metrics its type doesn't support (e.g., `engine_rpm` on a temperature sensor). This creates confusing dashboards and invalid alert configurations. The validation is cheap (single query on an indexed table) and catches errors at write time rather than producing mysterious data gaps at read time.

## 3. Alembic Migration with Data Backfill

**Decision:** Migration 003 creates the new tables, populates them from existing data (`SELECT DISTINCT device_type FROM devices`), backfills the `device_type_id` FK, then drops the old column and renames tables. All in a single migration.

**Why:** A multi-step migration (create tables in one, backfill in another, drop columns in a third) adds unnecessary complexity for a development-phase schema change. The single migration is atomic on PostgreSQL (transactional DDL), so it either fully applies or rolls back. For tests using SQLite, the models create the target schema directly — no migration needed.

**Trade-off:** The migration is non-trivial (CREATE, INSERT, UPDATE, ALTER, DROP, RENAME) but it's a one-time operation. Having it self-contained means `alembic upgrade head` on a fresh or existing database just works.

## 4. Incremental MQTT Messages (Diff-Based)

**Decision:** When device metrics are updated, the backend computes the diff (`added = new - old`, `removed = old - new`) and sends separate MQTT messages: `{"addMetrics": [...]}` for additions and `{"removeMetrics": [...]}` for removals.

**Why:** The previous approach sent the full metric list as `{"addMetrics": [...]}` every time, which meant the device had no way to know what changed. Real IoT devices need to know specifically which sensors to start or stop reading. Sending incremental diffs matches how embedded firmware typically handles configuration changes — process additions and removals independently.

**Database approach:** The DB still does a full delete + re-insert of metric rows (simplest correct approach). The diff is computed in memory before the delete, then MQTT messages are sent after the commit. This avoids complex partial updates in the DB while still giving devices precise change information.

## 5. Device Type CRUD as Separate Router

**Decision:** Created `backend/app/routers/admin_device_types.py` as a new router rather than adding endpoints to `admin_devices.py`.

**Why:** Device types are a separate resource with their own lifecycle (create, list, update, delete). Mixing them into the devices router would blur the REST resource boundary. The separate router keeps each file focused — `admin_devices.py` handles provisioned device CRUD, `admin_device_types.py` handles device type catalog management.

**Delete protection:** `DELETE /api/admin/device-types/{id}` returns 400 if any provisioned devices reference the type. This prevents orphaned devices with invalid type references.

## 6. Frontend Metric Filtering by Device Type

**Decision:** In the admin devices page, metric checkboxes in both the create form and the metrics modal are filtered to only show metrics allowed by the selected device type. When device type changes during inline editing, incompatible metrics are automatically deselected.

**Why:** Without filtering, an admin could check a metric box that would be rejected by the backend validation (Decision 2). Filtering the UI to match the backend constraint eliminates round-trip validation errors and makes the allowed metrics visually obvious.

## 7. Alert Metric Validation Against Device's Enabled Metrics

**Decision:** `POST /api/alerts` and `PUT /api/alerts/{id}` validate that the specified metric is actually enabled on the target device. Returns HTTP 400 if the metric is not in the device's `device_provisioned_metrics`.

**Why:** Previously, alerts could reference any metric string — including metrics not configured on the device. This would create a Grafana alert rule that queries data that doesn't exist, producing perpetual `NoData` state. Validating at creation time catches the error immediately.

## 8. Platform Org Exclusion (Frontend-Only)

**Decision:** The Platform organisation is filtered out of the user creation dropdown on the frontend. No backend change.

**Why:** The Platform org exists only for admin users. Creating viewer users in Platform is logically wrong (they'd have no devices to view). A frontend filter on `o.name !== 'Platform'` is the simplest correct approach. A backend endpoint change (`?exclude_platform=true`) would add API surface for a single UI concern.

## 9. Admin Devices View on Dashboard Page (Read-Only)

**Decision:** When an admin navigates to `/dashboard` (the "Devices" top nav), they see a table of all devices across all orgs with filters — the same data as `/admin/devices` but read-only (no provision/delete/metrics buttons). Each row links to the device's Grafana dashboard page.

**Why:** The admin's own org (Platform) has no devices, so the standard viewer dashboard shows "No devices found." Redirecting to `/admin/devices` was considered but rejected — the top-level Devices page should be a viewing experience (drill-down to Grafana embeds), not a provisioning page. The admin admin devices page remains at `/admin/devices` for provisioning workflows.
