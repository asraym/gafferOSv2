'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { login } from '@/lib/auth'

export default function LoginPage() {
  const router = useRouter()
  const [username, setUsername] = useState('coach')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login(username, password)
      router.push('/dashboard')
    } catch {
      setError('Invalid username or password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main style={{
      minHeight: '100vh',
      display: 'grid',
      placeItems: 'center',
      background: '#0f0f0f',
      color: '#fff',
      padding: 24,
    }}>
      <form
        onSubmit={handleSubmit}
        style={{
          width: '100%',
          maxWidth: 380,
          display: 'grid',
          gap: 16,
        }}
      >
        <h1>GafferOS Login</h1>

        <input
          value={username}
          onChange={e => setUsername(e.target.value)}
          placeholder="Username"
          style={{ padding: 12 }}
        />

        <input
          value={password}
          onChange={e => setPassword(e.target.value)}
          placeholder="Password"
          type="password"
          style={{ padding: 12 }}
        />

        {error && <p style={{ color: '#ff6b6b' }}>{error}</p>}

        <button type="submit" disabled={loading} style={{ padding: 12 }}>
          {loading ? 'Signing in...' : 'Sign in'}
        </button>
      </form>
    </main>
  )
}