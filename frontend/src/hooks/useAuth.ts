import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch, apiPost } from '../lib/api'
import { useAuthStore } from '../store/authStore'
import type { LoginRequest, LoginResponse, MeResponse } from '../types/api'

export function useMe() {
  const { setUser, clearUser } = useAuthStore()

  return useQuery({
    queryKey: ['auth', 'me'],
    queryFn: async () => {
      try {
        const data = await apiFetch<MeResponse>('/api/auth/me')
        setUser(data)
        return data
      } catch {
        clearUser()
        return null
      }
    },
    retry: false,
    staleTime: 5 * 60 * 1000,
  })
}

export function useLogin() {
  const { setUser } = useAuthStore()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (credentials: LoginRequest) =>
      apiPost<LoginResponse>('/api/auth/login', credentials),
    onSuccess: (data) => {
      setUser({
        ...data.user,
        organisation_name: '',
      })
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] })
    },
  })
}

export function useLogout() {
  const { clearUser } = useAuthStore()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => apiPost<{ detail: string }>('/api/auth/logout', {}),
    onSuccess: () => {
      clearUser()
      queryClient.clear()
    },
  })
}
