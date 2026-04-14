const API_BASE = import.meta.env.VITE_API_BASE_URL as string || ''

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    const token = this.getToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    return headers
  }

  private getToken(): string | null {
    if (typeof window === 'undefined') return null
    try {
      const stored = localStorage.getItem('auth-storage')
      if (stored) {
        const parsed = JSON.parse(stored)
        return parsed.state?.token ?? null
      }
    } catch {}
    return null
  }

  async get<T>(path: string): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      headers: this.getHeaders(),
    })
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Request failed' }))
      throw new Error(error.detail || `HTTP ${res.status}`)
    }
    return res.json()
  }

  async post<T>(path: string, body: unknown): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(body),
    })
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Request failed' }))
      throw new Error(error.detail || `HTTP ${res.status}`)
    }
    return res.json()
  }

  async patch<T>(path: string, body: unknown): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: 'PATCH',
      headers: this.getHeaders(),
      body: JSON.stringify(body),
    })
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Request failed' }))
      throw new Error(error.detail || `HTTP ${res.status}`)
    }
    return res.json()
  }

  async postForm<T>(path: string, formData: FormData): Promise<T> {
    const headers = this.getHeaders()
    delete headers['Content-Type']
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers,
      body: formData,
    })
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Request failed' }))
      throw new Error(error.detail || `HTTP ${res.status}`)
    }
    return res.json()
  }
}

export const api = new ApiClient(API_BASE)

export const getMessages = (sessionId: string) =>
  api.get<Array<{ id: string; session_id: string; role: string; content: string; timestamp: string; turn_index: number }>>(`/sessions/${sessionId}/messages`)