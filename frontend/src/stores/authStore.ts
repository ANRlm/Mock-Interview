import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { api } from '@/services/api'

interface User {
  id: string
  email: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: async (email, password) => {
        const data = await api.post<{ access_token: string; user: User }>('/auth/login', {
          email,
          password,
        })
        set({ user: data.user, token: data.access_token, isAuthenticated: true })
      },

      register: async (email, password) => {
        await api.post('/auth/register', { email, password })
      },

      logout: () => {
        set({ user: null, token: null, isAuthenticated: false })
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token, user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
)