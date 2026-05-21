'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import styles from './dashboard-components.module.css'

const LINKS = [
  {
    href: '/squad',
    title: 'Squad',
    desc: 'Manage players and attributes',
  },
  {
    href: '/opposition',
    title: 'Opposition',
    desc: 'Parse scouting intelligence',
  },
  {
    href: '/analysis',
    title: 'Analysis',
    desc: 'Generate tactical briefing',
  },
  {
    href: '/feedback',
    title: 'Feedback',
    desc: 'Submit match outcome',
  },
]

export default function QuickActions() {
  return (
    <motion.section
      className={styles.quickSection}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: 0.1 }}
    >
      <p className={styles.metaLabel}>
        Workflow
      </p>

      <div className={styles.quickGrid}>
        {LINKS.map((link) => (
          <motion.div
            key={link.href}
            whileHover={{ y: -1 }}
          >
            <Link
              href={link.href}
              className={styles.quickCard}
            >
              <span className={styles.quickTitle}>
                {link.title}
              </span>

              <span className={styles.quickDesc}>
                {link.desc}
              </span>
            </Link>
          </motion.div>
        ))}
      </div>
    </motion.section>
  )
}