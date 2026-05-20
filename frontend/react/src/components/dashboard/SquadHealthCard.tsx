'use client'

import { motion } from 'framer-motion'
import Link from 'next/link'
import styles from './dashboard-components.module.css'

interface Props {
  totalPlayers: number
  availablePlayers: number
  avgRating: string
}

export default function SquadHealthCard({
  totalPlayers,
  availablePlayers,
  avgRating,
}: Props) {
  return (
    <motion.div
      className={`${styles.surfaceCard} ${styles.healthCard}`}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: 0.05 }}
    >
      <div className={styles.cardHeader}>
        <p className={styles.metaLabel}>Squad readiness</p>
      </div>

      <div className={styles.healthGrid}>
        <div className={styles.healthItem}>
          <span className={styles.healthValue}>
            {totalPlayers}
          </span>

          <span className={styles.healthLabel}>
            Squad depth
          </span>
        </div>

        <div className={styles.healthDivider} />

        <div className={styles.healthItem}>
          <span className={styles.healthValue}>
            {availablePlayers}
          </span>

          <span className={styles.healthLabel}>
            Match ready
          </span>
        </div>

        <div className={styles.healthDivider} />

        <div className={styles.healthItem}>
          <span className={styles.healthValue}>
            {avgRating}
          </span>

          <span className={styles.healthLabel}>
            Avg rating
          </span>
        </div>
      </div>

      <Link
        href="/squad"
        className={styles.inlineLink}
      >
        View full squad →
      </Link>
    </motion.div>
  )
}