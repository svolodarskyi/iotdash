import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../lib/api'
import type { DeviceEmbedUrls } from '../types/api'

export function useDeviceEmbedUrls(id: string) {
  return useQuery({
    queryKey: ['devices', id, 'embed-urls'],
    queryFn: () => apiFetch<DeviceEmbedUrls>(`/api/devices/${id}/embed-urls`),
  })
}
