import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../lib/api'
import type { Device } from '../types/api'

export function useDevice(id: string) {
  return useQuery({
    queryKey: ['devices', id],
    queryFn: () => apiFetch<Device>(`/api/devices/${id}`),
  })
}
