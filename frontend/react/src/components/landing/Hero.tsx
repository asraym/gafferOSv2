'use client'

import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import styles from './Hero.module.css'

const PLAYERS = [
  { id: 1, x: 50, y: 85, role: 'GK' },
  { id: 2, x: 20, y: 65, role: 'DEF' },
  { id: 3, x: 38, y: 68, role: 'DEF' },
  { id: 4, x: 62, y: 68, role: 'DEF' },
  { id: 5, x: 80, y: 65, role: 'DEF' },
  { id: 6, x: 28, y: 45, role: 'MID' },
  { id: 7, x: 50, y: 40, role: 'MID' },
  { id: 8, x: 72, y: 45, role: 'MID' },
  { id: 9, x: 25, y: 22, role: 'FWD' },
  { id: 10, x: 50, y: 18, role: 'FWD' },
  { id: 11, x: 75, y: 22, role: 'FWD' },
]

const PASS_LINES = [
  [1, 2], [1, 3], [1, 4], [1, 5],
  [2, 6], [3, 6], [3, 7], [4, 7], [4, 8], [5, 8],
  [6, 9], [7, 9], [7, 10], [7, 11], [8, 11],
]

const ROLE_COLORS: Record<string, string> = {
  GK: '#B86A3C',
  DEF: '#8C7A63',
  MID: '#5A8A6A',
  FWD: '#B86A3C',
}

export default function Hero() {
  const [phase, setPhase] = useState(0)
  const svgRef = useRef<SVGSVGElement>(null)
  const [mouse, setMouse] = useState({ x: 0, y: 0 })

  useEffect(() => {
    const timings = [600, 1400, 2400, 3400]
    const timers = timings.map((t, i) =>
      setTimeout(() => setPhase(i + 1), t)
    )
    return () => timers.forEach(clearTimeout)
  }, [])

  useEffect(() => {
    const handle = (e: MouseEvent) => {
      setMouse({
        x: (e.clientX / window.innerWidth - 0.5) * 10,
        y: (e.clientY / window.innerHeight - 0.5) * 10,
      })
    }
    window.addEventListener('mousemove', handle)
    return () => window.removeEventListener('mousemove', handle)
  }, [])

  const getPlayer = (id: number) => PLAYERS.find(p => p.id === id)!

  return (
    <section className={styles.hero}>

      <div className={styles.gridBg} style={{
        transform: `translate(${mouse.x * 0.3}px, ${mouse.y * 0.3}px)`
      }} />

      <div className={styles.board} style={{
        transform: `translate(${mouse.x * 0.6}px, ${mouse.y * 0.6}px)`
      }}>
        <svg
          ref={svgRef}
          viewBox="0 0 100 100"
          className={styles.pitch}
          preserveAspectRatio="xMidYMid meet"
        >
          {phase >= 1 && (
            <g opacity="0.18">
              <rect x="10" y="5" width="80" height="90" fill="none" stroke="#3D3530" strokeWidth="0.5" />
              <line x1="10" y1="50" x2="90" y2="50" stroke="#3D3530" strokeWidth="0.3" />
              <circle cx="50" cy="50" r="12" fill="none" stroke="#3D3530" strokeWidth="0.3" />
              <rect x="30" y="5" width="40" height="12" fill="none" stroke="#3D3530" strokeWidth="0.3" />
              <rect x="30" y="83" width="40" height="12" fill="none" stroke="#3D3530" strokeWidth="0.3" />
            </g>
          )}

          {phase >= 2 && PASS_LINES.map(([fromId, toId], i) => {
            const from = getPlayer(fromId)
            const to = getPlayer(toId)
            return (
              <motion.line
                key={`line-${i}`}
                x1={from.x} y1={from.y}
                x2={to.x} y2={to.y}
                stroke="#B86A3C"
                strokeWidth="0.3"
                strokeOpacity="0.35"
                strokeDasharray="2 2"
                initial={{ pathLength: 0, opacity: 0 }}
                animate={{ pathLength: 1, opacity: 1 }}
                transition={{ duration: 0.6, delay: i * 0.04 }}
              />
            )
          })}

          {phase >= 3 && PLAYERS.map((p, i) => (
            <motion.g
              key={p.id}
              initial={{ opacity: 0, scale: 0.3 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4, delay: i * 0.05 }}
            >
              <circle
                cx={p.x}
                cy={p.y}
                r="2.8"
                fill={ROLE_COLORS[p.role]}
                opacity="0.9"
              />
              <circle
                cx={p.x}
                cy={p.y}
                r="4"
                fill="none"
                stroke={ROLE_COLORS[p.role]}
                strokeWidth="0.4"
                opacity="0.4"
              />
            </motion.g>
          ))}
        </svg>
      </div>

      <div className={styles.content}>
        <AnimatePresence>
          {phase >= 3 && (
            <motion.div
              className={styles.badge}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <span className={styles.dot} />
              Live tactical analysis
            </motion.div>
          )}
        </AnimatePresence>

        {phase >= 4 && (
          <>
            <motion.h1
              className={styles.headline}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7 }}
            >
              Tactical intelligence
              <br />
              <span className={styles.accent}>for every club.</span>
            </motion.h1>

            <motion.p
              className={styles.sub}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.15 }}
            >
              GafferOS watches your matches, builds rich player profiles,
              and delivers context-aware recommendations before every game.
            </motion.p>

            <motion.div
              className={styles.actions}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.3 }}
            >
              <button className={styles.btnPrimary}>Get started</button>
              <button className={styles.btnGhost}>See how it works</button>
            </motion.div>
          </>
        )}
      </div>

    </section>
  )
}