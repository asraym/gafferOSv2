import type { SimulationPackage, ScenarioKey } from './types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function getOppositionProfile(matchId: number) {
  const res = await fetch(`/api/opposition/profile?match_id=${matchId}`)
  if (!res.ok) throw new Error('No opposition profile')
  return res.json()
}

export async function fetchSimulationPackage({
  matchId,
  teamId,
  scenarios,
}: {
  matchId: number
  teamId: number
  scenarios?: ScenarioKey[]
}): Promise<SimulationPackage> {
  const res = await fetch(`${API_BASE}/api/matches/simulate-package`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      match_id: matchId,
      team_id: teamId,
      ...(scenarios ? { scenarios } : {}),
    }),
  })

  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `Simulation package failed: ${res.status}`)
  }

  return res.json()
}