# Sprint 3 Bugfix 1 — Features Delivered

## Accomplished

### Role Enforcement — Admin = Platform Owner Only
- **Hardcoded viewer role** — `POST /api/admin/users` always creates users with `role="viewer"`, regardless of request body
- **Role update removed** — `PUT /api/admin/users/{id}` no longer accepts a `role` field; role cannot be changed via API
- **Role dropdown removed from create form** — admin user creation UI no longer shows role selection
- **Role dropdown removed from edit form** — inline user editing no longer allows role changes
- **Role badge still displayed** — the users table still shows the role badge (admin/viewer) as read-only info

### Platform Organisation
- **Dedicated Platform org** — new "Platform" organisation in seed data for admin users
- **Admin user moved** — `admin@iotdash.com` belongs to Platform org (was `admin@democorp.com` in Demo Corp)
- **Client orgs viewer-only** — Demo Corp gets `viewer@democorp.com`, Acme IoT keeps `viewer@acmeiot.com`
- **Clean tenant examples** — Demo Corp and Acme IoT are pure client tenants with no admin privilege

### Admin Device Filters
- **Device type filter** — dropdown populated from `GET /api/admin/devices/device-types` (distinct values from database)
- **Metric type filter** — dropdown populated from existing `useMetrics()` hook (temperature, humidity, engine_rpm)
- **Three-way AND filtering** — organisation + device type + metric type filters combine with AND logic
- **Server-side filtering** — all filters applied as query params (`org_id`, `device_type`, `metric_name`), processed in the backend query

### Grafana Organisation Auto-Provisioning
- **Automatic Grafana org creation** — creating an organisation via admin UI provisions a Grafana org via `POST /api/orgs`
- **Automatic datasource** — InfluxDB datasource created in the new Grafana org with correct bucket/token config
- **Automatic dashboard** — IoT Metrics dashboard template deployed to the new Grafana org
- **Database records updated** — `grafana_org_id` stored on Organisation, `GrafanaDashboard` record created
- **Graceful failure** — org created in Postgres even if Grafana provisioning fails

### Testing
- **78 total backend tests** — all passing, up from 71 in Sprint 3
- **7 new tests added:**
  - `test_create_user_always_viewer` — verifies role is always viewer
  - `test_update_user_cannot_change_role` — verifies role stays unchanged on update
  - `test_list_device_types` — verifies device types endpoint
  - `test_list_devices_filter_by_device_type` — verifies device type filter
  - `test_list_devices_filter_by_metric_name` — verifies metric name filter
  - `test_list_devices_filter_by_nonexistent_metric` — verifies empty result for unknown metric
  - `test_list_devices_combined_filters` — verifies AND logic across org + device type
- **Updated org tests** — `test_create_org` and `test_delete_empty_org` verify Grafana mock calls

## Business Value
- **Security hardening** — clients can never be given admin access through the UI, closing a privilege escalation gap
- **Faster device lookup** — admins managing hundreds of devices across orgs can filter by company, device type, and metric type
- **Zero-touch org onboarding** — creating an organisation auto-provisions Grafana with datasource and dashboard; new client can see live data immediately without manual Grafana setup

## Gaps Remaining
- **No metric creation UI** — admin can only use seeded metrics
- **No bulk device import** — devices provisioned one at a time
- **No device search/pagination** — filtering helps but doesn't scale to thousands of devices
- **No Grafana org cleanup on org delete** — deleting a Postgres org does not remove the Grafana org
- **No admin user provisioning UI** — admin users must be created via seed or direct database access
