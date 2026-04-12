import { create } from 'zustand'
import { persist } from 'zustand/middleware'

import * as auth from '@/services/auth'

interface AuthState {
  token: string | null
  user: auth.User | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,

      login: async (email: string, password: string) => {
        const resp = await auth.login(email, password)
        set({
          token: resp.access_token,
          user: resp.user,
          isAuthenticated: true,
        })
      },

      register: async (email: string, password: string) => {
        await auth.register(email, password)
      },

      logout: () => {
        set({ token: null, user: null, isAuthenticated: false })
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token, user: state.user }),
    },
  ),
)
