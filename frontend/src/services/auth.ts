export interface User {
  id: string
  username: string
  email: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}

export interface RegisterResponse {
  id: string
  username: string
  email: string
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api'

export async function login(username: string, password: string): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Login failed' }))
    throw new Error(err.detail ?? 'Login failed')
  }
  return response.json() as Promise<LoginResponse>
}

export async function register(
  username: string,
  email: string,
  password: string,
): Promise<RegisterResponse> {
  const response = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password }),
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Registration failed' }))
    throw new Error(err.detail ?? 'Registration failed')
  }
  return response.json() as Promise<RegisterResponse>
}
