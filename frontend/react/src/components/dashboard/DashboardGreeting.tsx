'use client'

import { motion } from 'framer-motion'
import styles from './dashboard-components.module.css'

interface Props {
  teamName: string
}

export default function DashboardGreeting({ teamName }: Props) {
  return (
    <motion.div
      className={styles.greeting}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <p className={styles.greetLabel}>Operations overview</p>

      <h1 className={styles.greetTitle}>
        {teamName}
      </h1>
    </motion.div>
  )
}