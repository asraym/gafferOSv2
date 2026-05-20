const KEYS = {
  CLUB: 'gafferos_club',
  SETUP_DONE: 'gafferos_setup_done',
}

export function getClub() {
  if (typeof window === 'undefined') return null
  const raw = localStorage.getItem(KEYS.CLUB)
  return raw ? JSON.parse(raw) : null
}

export function setClub(club: { name: string; city: string; teamName: string }) {
  localStorage.setItem(KEYS.CLUB, JSON.stringify(club))
}

export function isSetupDone(): boolean {
  if (typeof window === 'undefined') return false
  return localStorage.getItem(KEYS.SETUP_DONE) === 'true'
}

export function markSetupDone() {
  localStorage.setItem(KEYS.SETUP_DONE, 'true')
}

export function clearAll() {
  Object.values(KEYS).forEach(k => localStorage.removeItem(k))
}