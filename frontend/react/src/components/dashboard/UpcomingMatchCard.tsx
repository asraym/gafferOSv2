'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { Match } from '@/types/match'
import styles from './dashboard-components.module.css'

interface Props {
  loading: boolean
  match: Match | null
}

export default function UpcomingMatchCard({
  loading,
  match,
}: Props) {
  return (
    <motion.div
      className={`${styles.surfaceCard} ${styles.matchCard}`}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45 }}
    >
      <div className={styles.cardHeader}>
        <p className={styles.metaLabel}>Upcoming fixture</p>
      </div>

      {loading ? (
        <p className={styles.loading}>Loading match data...</p>
      ) : match ? (
        <>
          <div className={styles.fixtureBlock}>
            <h2 className={styles.matchOpponent}>
              vs {match.opponent_name}
            </h2>

            <div className={styles.matchMeta}>
              <span className={styles.metaTag}>
                {new Date(match.match_date).toLocaleDateString('en-GB', {
                  weekday: 'short',
                  day: 'numeric',
                  month: 'short',
                })}
              </span>

              <span className={styles.metaTag}>
                {match.venue.charAt(0).toUpperCase() + match.venue.slice(1)}
              </span>
            </div>
          </div>

          <div className={styles.matchActions}>
            <Link
              href="/opposition"
              className={styles.secondaryButton}
            >
              Scouting notes
            </Link>

            <Link
              href="/analysis"
              className={styles.primaryButton}
            >
              Run analysis →
            </Link>
          </div>
        </>
      ) : (
        <div className={styles.emptyState}>
          <p className={styles.emptyText}>
            No upcoming fixture registered.
          </p>

          <Link
            href="/opposition"
            className={styles.primaryButton}
          >
            Register fixture →
          </Link>
        </div>
      )}
    </motion.div>
  )
}