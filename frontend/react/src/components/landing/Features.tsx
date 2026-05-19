'use client'

import { motion } from 'framer-motion'
import styles from './Features.module.css'

const FEATURES = [
  {
    icon: '⬡',
    title: 'Footage-driven profiles',
    desc: 'Your CV pipeline watches every match and builds rich player profiles automatically. No manual data entry after setup.',
    tag: 'CV Pipeline',
  },
  {
    icon: '◎',
    title: 'Tactical engine',
    desc: 'XGBoost model trained on StatsBomb data cross-referenced with your squad traits, attributes, and form curves.',
    tag: 'ML Model',
  },
  {
    icon: '↗',
    title: 'Matchup intelligence',
    desc: 'Opposition scouting notes parsed into structured data. Your players cross-referenced against their weaknesses.',
    tag: 'Matchup Layer',
  },
  {
    icon: '◈',
    title: 'Formation resolver',
    desc: 'Recommends the right shape based on squad depth, opponent strength, player traits, and fatigue risk.',
    tag: 'Rule Engine',
  },
  {
    icon: '▲',
    title: 'Form curves',
    desc: 'Every player has a trajectory. The engine knows who is rising, who is falling, and picks the XI accordingly.',
    tag: 'Player Ranking',
  },
  {
    icon: '◐',
    title: 'Feedback loop',
    desc: 'Coach submits actual results after each match. The system learns which recommendations translate to wins.',
    tag: 'Learning',
  },
]

const cardVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, delay: i * 0.08 },
  }),
}

export default function Features() {
  return (
    <section className={styles.section} id="features">
      <div className={styles.header}>
        <motion.p
          className={styles.label}
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          What GafferOS does
        </motion.p>
        <motion.h2
          className={styles.title}
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          Every layer of the game,
          <br />
          <span className={styles.accent}>covered.</span>
        </motion.h2>
        <motion.p
          className={styles.sub}
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          Built for semi-professional clubs who have footage but no analytics team.
          GafferOS turns raw match data into actionable tactical intelligence.
        </motion.p>
      </div>

      <div className={styles.grid}>
        {FEATURES.map((f, i) => (
          <motion.div
            key={f.title}
            className={styles.card}
            custom={i}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-40px' }}
            variants={cardVariants}
            whileHover={{ y: -4, transition: { duration: 0.2 } }}
          >
            <div className={styles.cardTop}>
              <span className={styles.icon}>{f.icon}</span>
              <span className={styles.tag}>{f.tag}</span>
            </div>
            <h3 className={styles.cardTitle}>{f.title}</h3>
            <p className={styles.cardDesc}>{f.desc}</p>
          </motion.div>
        ))}
      </div>
    </section>
  )
}