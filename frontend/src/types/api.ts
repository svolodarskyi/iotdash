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
