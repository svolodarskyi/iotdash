# IoTDash — API Specification

> **Version:** 0.1.0-draft
> **Date:** 2026-04-12
> **Base URL:** `https://app.iotdash.example.com/api`

---

## Authentication

All endpoints (except `/auth/login`) require a valid JWT token passed as an `httponly` cookie named `access_token`.

**Token payload:**
```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "org_id": "org-uuid",
  "role": "viewer",
  "exp": 1712000000
}
```

---

## Endpoints

### Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/login` | None | Login with email + password |
| `POST` | `/auth/logout` | Required | Clear session cookie |
| `GET` | `/auth/me` | Required | Get current user info |

#### `POST /auth/login`

**Request:**
```json
{
  "email": "alice@example.com",
  "password": "secret123"
}
```

**Response (200):**
```json
{
  "user": {
    "id": "uuid",
    "email": "alice@example.com",
    "full_name": "Alice Smith",
    "organisation_id": "uuid",
    "role": "viewer"
  }
}
```
*Sets `access_token` httponly cookie.*

**Response (401):**
```json
{ "detail": "Invalid email or password" }
```

#### `GET /auth/me`

**Response (200):**
```json
{
  "id": "uuid",
  "email": "alice@example.com",
  "full_name": "Alice Smith",
  "organisation_id": "uuid",
  "organisation_name": "Acme Corp",
  "role": "viewer"
}
```

---

### Organisations

| Method | Path | Auth | Role | Description |
|--------|------|------|------|-------------|
| `GET` | `/organisations` | Required | admin | List all organisations |
| `GET` | `/organisations/{id}` | Required | * | Get organisation details (users see own org) |
| `GET` | `/organisations/{id}/devices` | Required | * | List org's devices |
| `GET` | `/organisations/{id}/dashboards` | Required | * | List org's dashboard embeds |

#### `GET /organisations/{id}`

**Response (200):**
```json
{
  "id": "uuid",
  "name": "Acme Corp",
  "grafana_org_id": 2,
  "device_count": 5,
  "user_count": 3,
  "created_at": "2026-01-15T10:00:00Z"
}
```

#### `GET /organisations/{id}/devices`

**Response (200):**
```json
{
  "devices": [
    {
      "id": "uuid",
      "device_code": "sensor01",
      "name": "Warehouse Temp Sensor",
      "device_type": "temperature",
      "is_active": true,
      "metadata": { "location": "Building A, Floor 2" }
    }
  ]
}
```

#### `GET /organisations/{id}/dashboards`

**Response (200):**
```json
{
  "dashboards": [
    {
      "id": "uuid",
      "title": "Temperature Dashboard",
      "grafana_uid": "iot-temperature",
      "panel_ids": [1, 2, 3]
    }
  ]
}
```

---

### Devices

| Method | Path | Auth | Role | Description |
|--------|------|------|------|-------------|
| `GET` | `/devices` | Required | * | List user's org devices |
| `GET` | `/devices/{id}` | Required | * | Get device details |
| `GET` | `/devices/{id}/embed-urls` | Required | * | Get Grafana embed URLs for device |
| `GET` | `/devices/{id}/status` | Required | * | Get latest device status |

#### `GET /devices/{id}/embed-urls`

**Response (200):**
```json
{
  "device_id": "uuid",
  "device_code": "sensor01",
  "embeds": [
    {
      "dashboard_title": "Temperature Dashboard",
      "panel_id": 1,
      "panel_title": "Temperature (Live)",
      "embed_url": "https://grafana.iotdash.example.com/d-solo/iot-temperature/iot-temperature-dashboard?orgId=2&panelId=1&var-device_id=sensor01&from=now-1h&to=now&refresh=10s&theme=light&kiosk"
    },
    {
      "dashboard_title": "Temperature Dashboard",
      "panel_id": 2,
      "panel_title": "Current Temperature",
      "embed_url": "https://grafana.iotdash.example.com/d-solo/iot-temperature/iot-temperature-dashboard?orgId=2&panelId=2&var-device_id=sensor01&from=now-5m&to=now&refresh=10s&theme=light&kiosk"
    }
  ]
}
```

---

### Alerts

| Method | Path | Auth | Role | Description |
|--------|------|------|------|-------------|
| `GET` | `/alerts` | Required | * | List user's org alerts |
| `POST` | `/alerts` | Required | * | Create new alert |
| `GET` | `/alerts/{id}` | Required | * | Get alert details |
| `PUT` | `/alerts/{id}` | Required | * | Update alert |
| `DELETE` | `/alerts/{id}` | Required | * | Delete alert |
| `PATCH` | `/alerts/{id}/toggle` | Required | * | Enable/disable alert |

#### `POST /alerts`

**Request:**
```json
{
  "device_id": "uuid",
  "metric": "temperature",
  "condition": "above",
  "threshold": 30.0,
  "duration_seconds": 300,
  "notification_email": "alice@example.com"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "device_id": "uuid",
  "device_code": "sensor01",
  "metric": "temperature",
  "condition": "above",
  "threshold": 30.0,
  "duration_seconds": 300,
  "notification_email": "alice@example.com",
  "is_enabled": true,
  "grafana_rule_uid": "grafana-rule-xyz",
  "created_at": "2026-04-12T10:00:00Z"
}
```

#### `PUT /alerts/{id}`

**Request:**
```json
{
  "threshold": 28.0,
  "duration_seconds": 600,
  "notification_email": "alice@example.com"
}
```

#### `PATCH /alerts/{id}/toggle`

**Request:**
```json
{
  "is_enabled": false
}
```

---

### Admin Endpoints

All admin endpoints require `role: "admin"`.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/admin/organisations` | admin | Create organisation |
| `PUT` | `/admin/organisations/{id}` | admin | Update organisation |
| `POST` | `/admin/organisations/{id}/devices` | admin | Add device to org |
| `PUT` | `/admin/devices/{id}` | admin | Update device |
| `DELETE` | `/admin/devices/{id}` | admin | Deactivate device |
| `POST` | `/admin/organisations/{id}/users` | admin | Create user in org |
| `PUT` | `/admin/users/{id}` | admin | Update user |
| `DELETE` | `/admin/users/{id}` | admin | Deactivate user |
| `POST` | `/admin/organisations/{id}/dashboards` | admin | Add dashboard embed config |
| `POST` | `/admin/grafana/sync` | admin | Sync all orgs/dashboards to Grafana |
| `POST` | `/admin/grafana/sync/{org_id}` | admin | Sync specific org to Grafana |

#### `POST /admin/organisations`

**Request:**
```json
{
  "name": "Acme Corp"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "name": "Acme Corp",
  "grafana_org_id": 2,
  "created_at": "2026-04-12T10:00:00Z"
}
```
*Backend also creates corresponding Grafana org, datasource, and default dashboards.*

#### `POST /admin/organisations/{id}/devices`

**Request:**
```json
{
  "device_code": "sensor01",
  "name": "Warehouse Temp Sensor",
  "device_type": "temperature",
  "metadata": { "location": "Building A, Floor 2" }
}
```

#### `POST /admin/organisations/{id}/users`

**Request:**
```json
{
  "email": "alice@example.com",
  "password": "initial-password",
  "full_name": "Alice Smith",
  "role": "viewer"
}
```

#### `POST /admin/grafana/sync`

Syncs the PostgreSQL state to Grafana:
1. For each org: ensure Grafana org exists, create if missing
2. For each org: ensure datasource exists with correct InfluxDB config
3. For each org: provision dashboard templates
4. For each alert: ensure Grafana alert rule + contact point exists

**Response (200):**
```json
{
  "synced_orgs": 3,
  "synced_dashboards": 6,
  "synced_alerts": 12,
  "errors": []
}
```

---

### Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | None | Health check |
| `GET` | `/health/ready` | None | Readiness check (DB + Grafana reachable) |

#### `GET /health`

**Response (200):**
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

---

## Error Format

All errors follow:

```json
{
  "detail": "Human-readable error message",
  "code": "ERROR_CODE"
}
```

| HTTP Status | Code | Description |
|-------------|------|-------------|
| 400 | `VALIDATION_ERROR` | Invalid request body |
| 401 | `UNAUTHORIZED` | Missing or invalid token |
| 403 | `FORBIDDEN` | Insufficient role |
| 404 | `NOT_FOUND` | Resource not found |
| 409 | `CONFLICT` | Duplicate resource |
| 500 | `INTERNAL_ERROR` | Server error |

---

*Companion to [`PLANNING.md`](./PLANNING.md) and [`ARCHITECTURE.md`](./ARCHITECTURE.md).*
