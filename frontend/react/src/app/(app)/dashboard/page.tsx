'use client'

import { useEffect, useMemo, useState } from 'react'

import DashboardGreeting from '@/components/dashboard/DashboardGreeting'
import UpcomingMatchCard from '@/components/dashboard/UpcomingMatchCard'
import SquadHealthCard from '@/components/dashboard/SquadHealthCard'
import QuickActions from '@/components/dashboard/QuickActions'

import { getUpcomingMatch, getPlayers } from '@/lib/api'
import { getClub } from '@/lib/storage'

import { Match } from '@/types/match'
import { Player } from '@/types/player'

import styles from './dashboard.module.css'

export default function DashboardPage() {
  const [club, setClub] = useState<any>(null)

  const [match, setMatch] = useState<Match | null>(null)

  const [players, setPlayers] = useState<Player[]>([])

  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setClub(getClub())

    async function load() {
      try {
        const [matchData, playerData] = await Promise.all([
          getUpcomingMatch().catch(() => null),
          getPlayers().catch(() => []),
        ])

        setMatch(matchData)
        setPlayers(Array.isArray(playerData) ? playerData : [])
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [])

  const availablePlayers = useMemo(() => {
    return players.filter(
      (p) => p.is_active !== false
    ).length
  }, [players])

  const avgRating = useMemo(() => {
    if (!players.length) return '--'

    const total = players.reduce(
      (sum, p) => sum + (p.overall_rating || 0),
      0
    )

    return (total / players.length).toFixed(1)
  }, [players])

  return (
    <div className={styles.page}>
      <DashboardGreeting
        teamName={club?.teamName || 'FC Bangalore'}
      />

      <section className={styles.topRow}>
        <UpcomingMatchCard
          loading={loading}
          match={match}
        />

        <SquadHealthCard
          totalPlayers={players.length}
          availablePlayers={availablePlayers}
          avgRating={avgRating}
        />
      </section>

      <QuickActions />
    </div>
  )
}