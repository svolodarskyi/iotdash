export interface Organisation {
  id: string
  name: string
  grafana_org_id: number | null
  created_at: string
  updated_at: string
}

export interface Device {
  id: string
  device_code: string
  name: string
  organisation_id: string
  device_type: string
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
