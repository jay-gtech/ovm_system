import { create } from 'zustand'
import type { AuthUser } from '../api/auth'

interface AuthState {
  user: AuthUser | null
  token: string | null
  setAuth: (user: AuthUser, token: string) => void
  logout: () => void
}

function loadPersistedAuth(): { user: AuthUser | null; token: string | null } {
  try {
    const token = localStorage.getItem('ovm_token')
    const raw = localStorage.getItem('ovm_user')
    const user: AuthUser | null = raw ? (JSON.parse(raw) as AuthUser) : null
    return { token, user }
  } catch {
    return { user: null, token: null }
  }
}

export const useAuthStore = create<AuthState>((set) => ({
  ...loadPersistedAuth(),
  setAuth: (user, token) => {
    localStorage.setItem('ovm_token', token)
    localStorage.setItem('ovm_user', JSON.stringify(user))
    set({ user, token })
  },
  logout: () => {
    localStorage.removeItem('ovm_token')
    localStorage.removeItem('ovm_user')
    set({ user: null, token: null })
  },
}))
