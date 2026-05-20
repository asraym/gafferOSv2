const API = 'http://localhost:8000'

export const TEAM_ID = 1
export const CLUB_ID = 1
export const SEASON_ID = 1

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const error = await res.text()
    throw new Error(error || `Request failed: ${res.status}`)
  }
  return res.json()
}

// Players
export const getPlayers = () =>
  request(`/api/players?team_id=${TEAM_ID}`)

export const getPlayerForm = (id: number, n = 5) =>
  request(`/api/players/${id}/form?n=${n}`)

export const getPlayerTraits = (id: number) =>
  request(`/api/players/${id}/traits`)

export const registerPlayer = (body: object) =>
  request('/api/players/register', { method: 'POST', body: JSON.stringify(body) })

export const importPlayersCSV = (formData: FormData) =>
  fetch(`${API}/api/players/import-csv?club_id=${CLUB_ID}&team_id=${TEAM_ID}`, {
    method: 'POST',
    body: formData,
  }).then(r => r.json())

export const uploadPhysicalCSV = (formData: FormData) =>
  fetch(`${API}/api/players/physical-csv?team_id=${TEAM_ID}`, {
    method: 'POST',
    body: formData,
  }).then(r => r.json())

// Matches
export const getUpcomingMatch = () =>
  request(`/api/matches/upcoming?team_id=${TEAM_ID}`)

export const registerMatch = (body: object) =>
  request('/api/matches/register', { method: 'POST', body: JSON.stringify(body) })

export const analyseMatch = (matchId: number) =>
  request('/api/matches/analyse', {
    method: 'POST',
    body: JSON.stringify({ match_id: matchId, team_id: TEAM_ID }),
  })

export const submitFeedback = (body: object) =>
  request('/api/matches/feedback', { method: 'POST', body: JSON.stringify(body) })

// Opposition
export const parseOpposition = (body: object) =>
  request('/api/opposition/parse', { method: 'POST', body: JSON.stringify(body) })