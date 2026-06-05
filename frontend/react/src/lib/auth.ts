const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const TOKEN_KEY = 'gafferos_token'

export async function login(username: string, password: string) {
  const res = await fetch(`${API}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })

  if (!res.ok) {
    throw new Error('Invalid username or password')
  }

  const data = await res.json()
  localStorage.setItem(TOKEN_KEY, data.token)
  return data
}

export function logout() {
  localStorage.removeItem(TOKEN_KEY)
}

export function getToken() {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(TOKEN_KEY)
}

export function getAuthHeaders(): Record<string, string> {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export function isLoggedIn() {
  return Boolean(getToken())
}