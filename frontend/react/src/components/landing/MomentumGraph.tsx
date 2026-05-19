'use client'

import { useRef } from 'react'
import { motion, useScroll, useTransform, useInView } from 'framer-motion'
import styles from './MomentumGraph.module.css'

const MATCHES = [
  { label: 'MD1', result: 'W', value: 72 },
  { label: 'MD2', result: 'L', value: 38 },
  { label: 'MD3', result: 'W', value: 65 },
  { label: 'MD4', result: 'D', value: 51 },
  { label: 'MD5', result: 'W', value: 78 },
  { label: 'MD6', result: 'L', value: 42 },
  { label: 'MD7', result: 'W', value: 69 },
  { label: 'MD8', result: 'W', value: 81 },
  { label: 'MD9', result: 'D', value: 55 },
  { label: 'MD10', result: 'W', value: 88 },
]

const RESULT_COLORS: Record<string, string> = {
  W: '#5A8A6A',
  D: '#8C7A63',
  L: '#C8612A',
}

const W = 700
const H = 200
const PAD = { top: 24, right: 40, bottom: 40, left: 48 }
const INNER_W = W - PAD.left - PAD.right
const INNER_H = H - PAD.top - PAD.bottom

function toSvgX(i: number) {
  return PAD.left + (i / (MATCHES.length - 1)) * INNER_W
}

function toSvgY(v: number) {
  return PAD.top + INNER_H - ((v - 20) / 80) * INNER_H
}

const points = MATCHES.map((m, i) => ({
  ...m,
  sx: toSvgX(i),
  sy: toSvgY(m.value),
}))

function buildPath(pts: typeof points) {
  return pts.reduce((acc, p, i) => {
    if (i === 0) return `M ${p.sx} ${p.sy}`
    const prev = pts[i - 1]
    const cpx = (prev.sx + p.sx) / 2
    return `${acc} C ${cpx} ${prev.sy} ${cpx} ${p.sy} ${p.sx} ${p.sy}`
  }, '')
}

const linePath = buildPath(points)

const areaPath =
  linePath +
  ` L ${points[points.length - 1].sx} ${PAD.top + INNER_H}` +
  ` L ${points[0].sx} ${PAD.top + INNER_H} Z`

const STATS = [
  { label: 'Avg momentum', value: '65.9', unit: 'pts' },
  { label: 'Peak', value: '88', unit: 'MD10' },
  { label: 'Wins', value: '6', unit: '/ 10' },
  { label: 'Trend', value: '↑', unit: 'Rising' },
]

export default function MomentumGraph() {
  const ref = useRef<HTMLDivElement>(null)
  const isInView = useInView(ref, { once: true, margin: '-100px' })

  return (
    <section className={styles.section} id="analysis" ref={ref}>
      <div className={styles.inner}>

        <div className={styles.header}>
          <motion.p
            className={styles.label}
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
          >
            Match momentum engine
          </motion.p>
          <motion.h2
            className={styles.title}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            Form tracked across
            <br />
            <span className={styles.accent}>every match.</span>
          </motion.h2>
        </div>

        <motion.div
          className={styles.statsRow}
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          {STATS.map((s) => (
            <div key={s.label} className={styles.statCard}>
              <p className={styles.statLabel}>{s.label}</p>
              <p className={styles.statValue}>
                {s.value}
                <span className={styles.statUnit}>{s.unit}</span>
              </p>
            </div>
          ))}
        </motion.div>

        <motion.div
          className={styles.graphWrap}
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.3 }}
        >
          <svg
            viewBox={`0 0 ${W} ${H}`}
            className={styles.graph}
            preserveAspectRatio="xMidYMid meet"
          >
            <defs>
              <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#B86A3C" stopOpacity="0.18" />
                <stop offset="100%" stopColor="#B86A3C" stopOpacity="0" />
              </linearGradient>
              <clipPath id="lineClip">
                <motion.rect
                  x="0" y="0"
                  width={W} height={H}
                  animate={{ scaleX: isInView ? 1 : 0 }}
                  initial={{ scaleX: 0 }}
                  transition={{ duration: 1.8, ease: 'easeInOut', delay: 0.3 }}
                  style={{ transformOrigin: 'left center' }}
                />
              </clipPath>
            </defs>

            {/* Grid lines */}
            {[20, 40, 60, 80, 100].map((v) => (
              <g key={v}>
                <line
                  x1={PAD.left} y1={toSvgY(v)}
                  x2={W - PAD.right} y2={toSvgY(v)}
                  stroke="#C8B89A" strokeWidth="0.5" strokeOpacity="0.4"
                />
                <text
                  x={PAD.left - 6} y={toSvgY(v) + 4}
                  textAnchor="end"
                  fontSize="10"
                  fill="#8C7A63"
                  fontFamily="monospace"
                >
                  {v}
                </text>
              </g>
            ))}

            {/* Area fill */}
            <path
              d={areaPath}
              fill="url(#areaGrad)"
              clipPath="url(#lineClip)"
            />

            {/* Main line */}
            <path
              d={linePath}
              fill="none"
              stroke="#B86A3C"
              strokeWidth="1.5"
              clipPath="url(#lineClip)"
            />

            {/* Match day labels + dots */}
            {points.map((p, i) => (
              <motion.g
                key={p.label}
                initial={{ opacity: 0 }}
                animate={{ opacity: isInView ? 1 : 0 }}
                transition={{ duration: 0.3, delay: 0.3 + (i / MATCHES.length) * 1.5 }}
              >
                <circle
                  cx={p.sx} cy={p.sy}
                  r="3.5"
                  fill={RESULT_COLORS[p.result]}
                  stroke="#F7F3EE"
                  strokeWidth="1.5"
                />
                <text
                  x={p.sx} y={PAD.top + INNER_H + 16}
                  textAnchor="middle"
                  fontSize="10"
                  fill="#8C7A63"
                  fontFamily="monospace"
                >
                  {p.label}
                </text>
                <text
                  x={p.sx} y={PAD.top + INNER_H + 26}
                  textAnchor="middle"
                  fontSize="9"
                  fill={RESULT_COLORS[p.result]}
                  fontFamily="monospace"
                  fontWeight="500"
                >
                  {p.result}
                </text>
              </motion.g>
            ))}

            {/* Live dot at end */}
            <motion.circle
              cx={points[points.length - 1].sx}
              cy={points[points.length - 1].sy}
              r="5"
              fill="#B86A3C"
              animate={{ opacity: isInView ? [1, 0.3, 1] : 0 }}
              transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }}
            />
            <motion.circle
              cx={points[points.length - 1].sx}
              cy={points[points.length - 1].sy}
              r="9"
              fill="none"
              stroke="#B86A3C"
              strokeWidth="0.8"
              animate={{ opacity: isInView ? [0.5, 0, 0.5] : 0, r: isInView ? [6, 12, 6] : 6 }}
              transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }}
            />

            {/* Live label */}
            <motion.g
              initial={{ opacity: 0 }}
              animate={{ opacity: isInView ? 1 : 0 }}
              transition={{ duration: 0.5, delay: 2 }}
            >
              <rect
                x={points[points.length - 1].sx - 18}
                y={points[points.length - 1].sy - 18}
                width="36" height="12"
                rx="3"
                fill="#B86A3C"
              />
              <text
                x={points[points.length - 1].sx}
                y={points[points.length - 1].sy - 9}
                textAnchor="middle"
                fontSize="9"
                fill="#F7F3EE"
                fontFamily="monospace"
                fontWeight="500"
              >
                LIVE
              </text>
            </motion.g>

          </svg>
        </motion.div>

      </div>
    </section>
  )
}