import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiDelete, apiFetch, apiPatch, apiPost, apiPut } from '../lib/api'
import type { Alert, AlertCreate, AlertToggle, AlertUpdate } from '../types/api'

export function useAlerts() {
  return useQuery({
    queryKey: ['alerts'],
    queryFn: () => apiFetch<Alert[]>('/api/alerts'),
    staleTime: 30_000,
  })
}

export function useAlert(alertId: string) {
  return useQuery({
    queryKey: ['alerts', alertId],
    queryFn: () => apiFetch<Alert>(`/api/alerts/${alertId}`),
  })
}

export function useCreateAlert() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: AlertCreate) => apiPost<Alert>('/api/alerts', body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
    },
  })
}

export function useUpdateAlert() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: AlertUpdate }) =>
      apiPut<Alert>(`/api/alerts/${id}`, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
    },
  })
}

export function useDeleteAlert() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => apiDelete(`/api/alerts/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
    },
  })
}

export function useToggleAlert() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: AlertToggle }) =>
      apiPatch<Alert>(`/api/alerts/${id}/toggle`, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
    },
  })
}
