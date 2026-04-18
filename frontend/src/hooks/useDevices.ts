import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../lib/api'
import type { Device, DeviceMetric } from '../types/api'

export function useDevices() {
  return useQuery({
    queryKey: ['devices'],
    queryFn: () => apiFetch<Device[]>('/api/devices'),
  })
}

export function useDeviceMetrics(deviceId: string | undefined) {
  return useQuery({
    queryKey: ['devices', deviceId, 'metrics'],
    queryFn: () => apiFetch<DeviceMetric[]>(`/api/devices/${deviceId}/metrics`),
    enabled: !!deviceId,
  })
}
