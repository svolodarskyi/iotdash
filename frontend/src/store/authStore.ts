import { create } from 'zustand'

// Placeholder for Week 4 auth implementation
interface AuthState {
  token: string | null
}

export const useAuthStore = create<AuthState>()(() => ({
  token: null,
}))
