import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../lib/api'
import type { Device } from '../types/api'

export function useDevices() {
  return useQuery({
    queryKey: ['devices'],
    queryFn: () => apiFetch<Device[]>('/api/devices'),
  })
}
