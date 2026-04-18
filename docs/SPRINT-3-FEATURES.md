# Sprint 3 — Features Delivered

## Admin Panel

Full CRUD admin interface for managing organisations, users, and devices. Admin-only navigation link visible when `user.role === "admin"`. Route guard redirects non-admins.

### Organisation Management
- List all organisations
- Create new organisation (name uniqueness validated)
- Edit organisation name
- Delete empty organisations (blocked if devices or users exist)

### User Management
- List all users with org filter
- Create user with email, password, name, org assignment, role
- Edit user profile (name, email, role)
- Deactivate users (soft delete)

### Device Provisioning
- List all devices across orgs with metric badges
- Provision new device with optional UID auto-generation
- Select metrics from catalog (temperature, humidity, engine_rpm)
- Auto-enable: send MQTT config immediately on creation
- Edit device details (name, type, active status)
- Manage device metrics via modal (add/remove with optional config push)
- Re-send MQTT config button for retry scenarios
- Delete device (cascades alerts and metric links)

## Metrics Catalog

Database-backed metric type registry with 3 seeded metrics. Extensible for future metric types. Used by admin device provisioning, dashboard metric selector, and alert creation.

## Multi-Metric Dashboards

- Parametric Grafana dashboard with `$device_id` and `$metric` template variables
- One embed URL per enabled metric per device
- Device detail page shows metric selector pills
- "Show All" default with individual metric filtering
- Each metric renders as a separate live time-series graph

## Multi-Metric Device Simulator

- `fake_device.py` subscribes to `{device_id}/to/config` topic
- Starts publishing temperature by default
- On receiving `{"addMetrics": [...]}`, starts publishing additional metrics
- Supports `--all-metrics` flag and `--device-id` flag
- Generates realistic data: temperature (~22C), humidity (~55%), engine_rpm (~2500)

## Business Value

Full client onboarding in under 10 minutes: admin provisions device with metrics, device receives config via MQTT, dashboard shows live multi-metric graphs. No manual database editing required.

## Gaps Remaining

- No metric creation UI (admin can only use seeded metrics)
- No bulk device import
- No device search/pagination for large deployments
- No audit logging for admin actions
- Alert creation doesn't validate against metrics catalog
