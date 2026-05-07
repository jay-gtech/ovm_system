import { get, post } from './client'

export interface LoginPayload {
  organization_slug: string
  email: string
  password: string
}

export interface AuthUser {
  id: string
  email: string
  full_name: string
  organization_id: string
  is_superuser: boolean
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: AuthUser
}

export interface RefreshResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export const authApi = {
  login: (payload: LoginPayload) =>
    post<LoginResponse>('/auth/login', payload),

  logout: () =>
    post<void>('/auth/logout'),

  refresh: (refresh_token: string) =>
    post<RefreshResponse>('/auth/refresh', { refresh_token }),

  me: () =>
    get<AuthUser>('/users/me'),
}
