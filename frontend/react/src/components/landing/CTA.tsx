'use client'

import { motion } from 'framer-motion'
import styles from './CTA.module.css'

export default function CTA() {
  return (
    <section className={styles.section}>
      <div className={styles.inner}>

        <motion.div
          className={styles.card}
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <div className={styles.topRow}>
            <span className={styles.badge}>
              <span className={styles.dot} />
              Now in early access
            </span>
          </div>

          <h2 className={styles.title}>
            Your next match starts
            <br />
            <span className={styles.accent}>with better data.</span>
          </h2>

          <p className={styles.desc}>
            GafferOS is built for clubs who are serious about winning
            but don't have an analytics team. Set up takes one session.
            The engine does the rest.
          </p>

          <div className={styles.actions}>
            <button className={styles.btnPrimary}>Get started free</button>
            <button className={styles.btnGhost}>Book a demo</button>
          </div>

          <div className={styles.statsRow}>
            {[
              { value: '75%', label: 'Model accuracy' },
              { value: '35+', label: 'Features tracked' },
              { value: '< 1s', label: 'Analysis time' },
            ].map((s) => (
              <div key={s.label} className={styles.stat}>
                <span className={styles.statValue}>{s.value}</span>
                <span className={styles.statLabel}>{s.label}</span>
              </div>
            ))}
          </div>

          {/* Background pitch mark */}
          <svg
            className={styles.bgPitch}
            viewBox="0 0 200 200"
            fill="none"
            aria-hidden
          >
            <circle cx="100" cy="100" r="60" stroke="#B86A3C" strokeWidth="0.5" strokeOpacity="0.15" />
            <circle cx="100" cy="100" r="2" fill="#B86A3C" fillOpacity="0.2" />
            <line x1="20" y1="100" x2="180" y2="100" stroke="#B86A3C" strokeWidth="0.5" strokeOpacity="0.1" />
            <rect x="60" y="20" width="80" height="30" stroke="#B86A3C" strokeWidth="0.5" strokeOpacity="0.1" />
            <rect x="60" y="150" width="80" height="30" stroke="#B86A3C" strokeWidth="0.5" strokeOpacity="0.1" />
          </svg>
        </motion.div>

      </div>

      <footer className={styles.footer}>
        <div className={styles.footerInner}>
          <div className={styles.footerLogo}>
            <span className={styles.logoMark}>G</span>
            <span className={styles.logoText}>GafferOS</span>
          </div>
          <p className={styles.footerDesc}>
            AI-assisted tactical intelligence for semi-professional football clubs.
          </p>
          <p className={styles.footerCopy}>
            © 2025 GafferOS. Built for the game.
          </p>
        </div>
      </footer>
    </section>
  )
}