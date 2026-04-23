export interface Organisation {
  id: string
  name: string
  grafana_org_id: number | null
  created_at: string
  updated_at: string
}

export interface DeviceType {
  id: string
  name: string
  description: string | null
  allowed_metrics: DeviceTypeMetric[]
  created_at: string
}

export interface DeviceTypeMetric {
  metric_id: string
  metric_name: string
  metric_unit: string | null
}

export interface Device {
  id: string
  device_code: string
  name: string
  organisation_id: string
  device_type_id: string
  device_type_name: string
  metadata_: Record<string, unknown> | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface EmbedUrl {
  dashboard_title: string
  panel_id: number
  url: string
}

export interface DeviceEmbedUrls {
  device_id: string
  device_code: string
  urls: EmbedUrl[]
}

export interface User {
  id: string
  email: string
  full_name: string
  organisation_id: string
  role: string
}

export interface MeResponse {
  id: string
  email: string
  full_name: string
  organisation_id: string
  organisation_name: string
  role: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  user: User
}

export interface Alert {
  id: string
  device_id: string
  device_code: string
  organisation_name: string | null
  created_by: string | null
  metric: string
  condition: string
  threshold: number
  duration_seconds: number
  notification_email: string | null
  is_enabled: boolean
  grafana_rule_uid: string | null
  created_at: string
  updated_at: string
}

export interface AlertCreate {
  device_id: string
  metric: string
  condition: string
  threshold: number
  duration_seconds: number
  notification_email: string
}

export interface AlertUpdate {
  metric?: string
  condition?: string
  threshold?: number
  duration_seconds?: number
  notification_email?: string
}

export interface AlertToggle {
  is_enabled: boolean
}

// ── Metrics ──────────��──────────────────────────────
export interface Metric {
  id: string
  name: string
  unit: string | null
  data_type: string
  description: string | null
}

export interface DeviceMetric {
  metric_id: string
  metric_name: string
  metric_unit: string | null
  is_enabled: boolean
  enabled_at: string
  disabled_at: string | null
}

// ── Admin types ─────────────────────────────────────
export interface DeviceAdmin {
  id: string
  device_code: string
  name: string
  organisation_id: string
  organisation_name: string
  device_type_id: string
  device_type_name: string
  is_active: boolean
  metrics: DeviceMetric[]
  created_at: string
  updated_at: string
}

export interface DeviceCreate {
  device_code?: string
  name: string
  organisation_id: string
  device_type_id: string
  metric_ids: string[]
  auto_enable: boolean
}

export interface DeviceUpdate {
  name?: string
  device_type_id?: string
  is_active?: boolean
}

export interface DeviceMetricUpdate {
  metric_ids: string[]
  send_config: boolean
}

export interface OrgCreate {
  name: string
}

export interface OrgUpdate {
  name?: string
}

export interface UserCreate {
  email: string
  password: string
  full_name: string
  organisation_id: string
}

export interface UserUpdate {
  email?: string
  full_name?: string
  is_active?: boolean
}

export interface DeviceSendConfigResponse {
  device_code: string
  metrics_sent: string[]
  success: boolean
}

export interface DeviceTypeCreate {
  name: string
  description?: string
  metric_ids: string[]
}

export interface DeviceTypeUpdate {
  name?: string
  description?: string
  metric_ids?: string[]
}

export interface ExternalServices {
  grafana_url: string
  influxdb_url: string
  emqx_url: string
}
