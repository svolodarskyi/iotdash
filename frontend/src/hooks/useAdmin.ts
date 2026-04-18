import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiDelete, apiFetch, apiPatch, apiPost, apiPut } from '../lib/api'
import type {
  DeviceAdmin,
  DeviceCreate,
  DeviceMetricUpdate,
  DeviceSendConfigResponse,
  DeviceType,
  DeviceTypeCreate,
  DeviceTypeUpdate,
  DeviceUpdate,
  Metric,
  Organisation,
  OrgCreate,
  OrgUpdate,
  User,
  UserCreate,
  UserUpdate,
} from '../types/api'

// ── Organisations ──────────��────────────────────────
export function useAdminOrgs() {
  return useQuery({
    queryKey: ['admin', 'organisations'],
    queryFn: () => apiFetch<Organisation[]>('/api/admin/organisations'),
  })
}

export function useCreateOrg() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: OrgCreate) => apiPost<Organisation>('/api/admin/organisations', body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'organisations'] }),
  })
}

export function useUpdateOrg() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: OrgUpdate }) =>
      apiPut<Organisation>(`/api/admin/organisations/${id}`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'organisations'] }),
  })
}

export function useDeleteOrg() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => apiDelete(`/api/admin/organisations/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'organisations'] }),
  })
}

// ── Users ───��───────────────────────────────────────
export function useAdminUsers(orgId?: string) {
  return useQuery({
    queryKey: ['admin', 'users', orgId],
    queryFn: () =>
      apiFetch<User[]>(`/api/admin/users${orgId ? `?org_id=${orgId}` : ''}`),
  })
}

export function useCreateUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: UserCreate) => apiPost<User>('/api/admin/users', body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'users'] }),
  })
}

export function useUpdateUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: UserUpdate }) =>
      apiPut<User>(`/api/admin/users/${id}`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'users'] }),
  })
}

export function useDeleteUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => apiDelete(`/api/admin/users/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'users'] }),
  })
}

// ── Devices ───���───────────────────────────���─────────
export function useAdminDevices(orgId?: string, deviceTypeId?: string, metricName?: string) {
  return useQuery({
    queryKey: ['admin', 'devices', orgId, deviceTypeId, metricName],
    queryFn: () => {
      const params = new URLSearchParams()
      if (orgId) params.set('org_id', orgId)
      if (deviceTypeId) params.set('device_type_id', deviceTypeId)
      if (metricName) params.set('metric_name', metricName)
      const qs = params.toString()
      return apiFetch<DeviceAdmin[]>(`/api/admin/devices${qs ? `?${qs}` : ''}`)
    },
  })
}

export function useDeviceTypes() {
  return useQuery({
    queryKey: ['admin', 'device-types'],
    queryFn: () => apiFetch<DeviceType[]>('/api/admin/device-types'),
  })
}

export function useCreateDeviceType() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: DeviceTypeCreate) =>
      apiPost<DeviceType>('/api/admin/device-types', body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'device-types'] }),
  })
}

export function useUpdateDeviceType() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: DeviceTypeUpdate }) =>
      apiPut<DeviceType>(`/api/admin/device-types/${id}`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'device-types'] }),
  })
}

export function useDeleteDeviceType() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => apiDelete(`/api/admin/device-types/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'device-types'] }),
  })
}

export function useCreateDevice() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: DeviceCreate) =>
      apiPost<DeviceAdmin>('/api/admin/devices', body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'devices'] }),
  })
}

export function useUpdateDevice() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: DeviceUpdate }) =>
      apiPut<DeviceAdmin>(`/api/admin/devices/${id}`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'devices'] }),
  })
}

export function useDeleteDevice() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => apiDelete(`/api/admin/devices/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'devices'] }),
  })
}

export function useUpdateDeviceMetrics() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: DeviceMetricUpdate }) =>
      apiPatch<DeviceAdmin>(`/api/admin/devices/${id}/metrics`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'devices'] }),
  })
}

export function useSyncDeviceConfig() {
  return useMutation({
    mutationFn: (id: string) =>
      apiPost<DeviceSendConfigResponse>(`/api/admin/devices/${id}/sync-config`, {}),
  })
}

// ── Metrics ─────────────────────────────────────────
export function useMetrics() {
  return useQuery({
    queryKey: ['metrics'],
    queryFn: () => apiFetch<Metric[]>('/api/metrics'),
  })
}
