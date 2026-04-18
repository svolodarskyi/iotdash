# Sprint 3 — Technical Decisions

## Admin Role Guard

Admin routes live under `/api/admin/*` and use a `require_admin` FastAPI dependency that checks `current_user.role == "admin"`. Regular users get 403. User-facing endpoints (`/api/devices`, `/api/alerts`) are unchanged.

## Metrics Catalog Table

A `metrics` table stores supported metric types (temperature, humidity, engine_rpm) with units and data types. Seeded on first run. Extensible — admin can add new metric types later. Replaces hardcoded metric assumptions.

## DeviceMetric Join Table

A single `device_metrics` table links devices to metrics with an `is_enabled` flag. This avoids a large schema overhaul (no separate provisions table needed) while supporting per-device metric enablement. Composite unique constraint on (device_id, metric_id).

## MQTT Publisher via paho-mqtt

The backend publishes to `{device_code}/to/config` with `{"addMetrics": [...]}` when an admin enables metrics on a device. Synchronous publish with fire-and-forget QoS 0. Singleton MqttPublisher with lazy connection via FastAPI dependency injection. Mocked in tests.

## Parametric Grafana Dashboard

Replaced the static `temperature.json` with a single `iot-metrics.json` dashboard that uses template variables (`$device_id` and `$metric`). Each embed URL passes `var-device_id=sensor01&var-metric=temperature`. One dashboard template handles all metrics — no per-metric dashboard files.

## Device UID Generation

`POST /api/admin/devices` accepts an optional `device_code`. If omitted, an 8-char hex prefix is generated: `dev-{uuid4().hex[:8]}`. If provided, uniqueness is validated. The admin UI toggles between auto-generate and manual entry modes.

## Auto-Enable on Provision

Device creation form includes an "auto-enable" option. If set, after creating the device and metric assignments, the backend immediately publishes the MQTT config message. Otherwise the device is created silently and admin can send config later via "Re-send Config".

## Embed URL Strategy

Devices with enabled metrics get one embed URL per metric using the parametric dashboard. Devices without metrics fall back to the old panel-based GrafanaDashboard table approach for backwards compatibility.
