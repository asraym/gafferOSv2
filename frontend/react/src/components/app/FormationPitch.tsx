// src/components/app/FormationPitch.tsx
'use client'

import { useEffect, useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import styles from './FormationPitch.module.css'

// ── Constants ────────────────────────────────────────────────────────────────

const ROLE_COLORS: Record<string, string> = {
  GK:  '#B86A3C',
  DEF: '#8C7A63',
  MID: '#5A8A6A',
  FWD: '#C8612A',
}

const HIGHLIGHT_COLORS = {
  inform:  '#22c55e',   // green ring — in form
  dip:     '#ef4444',   // red ring — form dip
  weak:    '#f59e0b',   // amber ring — weak link
}

// Horizontal pitch: viewBox 0 0 200 110
// GK on left (x~10), FWD on right (x~185)
const FORMATION_SLOTS: Record<string, { x: number; y: number; role: string }[]> = {
  '4-3-3': [
    { x: 12,  y: 55, role: 'GK'  },
    { x: 45,  y: 20, role: 'DEF' },
    { x: 45,  y: 42, role: 'DEF' },
    { x: 45,  y: 68, role: 'DEF' },
    { x: 45,  y: 90, role: 'DEF' },
    { x: 90,  y: 30, role: 'MID' },
    { x: 90,  y: 55, role: 'MID' },
    { x: 90,  y: 80, role: 'MID' },
    { x: 155, y: 20, role: 'FWD' },
    { x: 155, y: 55, role: 'FWD' },
    { x: 155, y: 90, role: 'FWD' },
  ],
  '4-4-2': [
    { x: 12,  y: 55, role: 'GK'  },
    { x: 45,  y: 20, role: 'DEF' },
    { x: 45,  y: 42, role: 'DEF' },
    { x: 45,  y: 68, role: 'DEF' },
    { x: 45,  y: 90, role: 'DEF' },
    { x: 95,  y: 20, role: 'MID' },
    { x: 95,  y: 42, role: 'MID' },
    { x: 95,  y: 68, role: 'MID' },
    { x: 95,  y: 90, role: 'MID' },
    { x: 165, y: 38, role: 'FWD' },
    { x: 165, y: 72, role: 'FWD' },
  ],
  '4-2-3-1': [
    { x: 12,  y: 55, role: 'GK'  },
    { x: 45,  y: 20, role: 'DEF' },
    { x: 45,  y: 42, role: 'DEF' },
    { x: 45,  y: 68, role: 'DEF' },
    { x: 45,  y: 90, role: 'DEF' },
    { x: 85,  y: 40, role: 'MID' },
    { x: 85,  y: 70, role: 'MID' },
    { x: 125, y: 20, role: 'MID' },
    { x: 125, y: 55, role: 'MID' },
    { x: 125, y: 90, role: 'MID' },
    { x: 170, y: 55, role: 'FWD' },
  ],
  '4-5-1': [
    { x: 12,  y: 55, role: 'GK'  },
    { x: 45,  y: 20, role: 'DEF' },
    { x: 45,  y: 42, role: 'DEF' },
    { x: 45,  y: 68, role: 'DEF' },
    { x: 45,  y: 90, role: 'DEF' },
    { x: 95,  y: 10, role: 'MID' },
    { x: 95,  y: 32, role: 'MID' },
    { x: 95,  y: 55, role: 'MID' },
    { x: 95,  y: 78, role: 'MID' },
    { x: 95,  y: 100,role: 'MID' },
    { x: 170, y: 55, role: 'FWD' },
  ],
  '5-4-1': [
    { x: 12,  y: 55, role: 'GK'  },
    { x: 45,  y: 10, role: 'DEF' },
    { x: 45,  y: 32, role: 'DEF' },
    { x: 45,  y: 55, role: 'DEF' },
    { x: 45,  y: 78, role: 'DEF' },
    { x: 45,  y: 100,role: 'DEF' },
    { x: 100, y: 20, role: 'MID' },
    { x: 100, y: 45, role: 'MID' },
    { x: 100, y: 70, role: 'MID' },
    { x: 100, y: 92, role: 'MID' },
    { x: 170, y: 55, role: 'FWD' },
  ],
  '4-1-4-1': [
    { x: 12,  y: 55, role: 'GK'  },
    { x: 45,  y: 20, role: 'DEF' },
    { x: 45,  y: 42, role: 'DEF' },
    { x: 45,  y: 68, role: 'DEF' },
    { x: 45,  y: 90, role: 'DEF' },
    { x: 80,  y: 55, role: 'MID' },
    { x: 115, y: 15, role: 'MID' },
    { x: 115, y: 38, role: 'MID' },
    { x: 115, y: 72, role: 'MID' },
    { x: 115, y: 95, role: 'MID' },
    { x: 170, y: 55, role: 'FWD' },
  ],
  '4-4-1-1': [
    { x: 12,  y: 55, role: 'GK'  },
    { x: 45,  y: 20, role: 'DEF' },
    { x: 45,  y: 42, role: 'DEF' },
    { x: 45,  y: 68, role: 'DEF' },
    { x: 45,  y: 90, role: 'DEF' },
    { x: 95,  y: 20, role: 'MID' },
    { x: 95,  y: 42, role: 'MID' },
    { x: 95,  y: 68, role: 'MID' },
    { x: 95,  y: 90, role: 'MID' },
    { x: 145, y: 55, role: 'FWD' },
    { x: 172, y: 55, role: 'FWD' },
  ],
  '3-5-2': [
    { x: 12,  y: 55, role: 'GK'  },
    { x: 45,  y: 30, role: 'DEF' },
    { x: 45,  y: 55, role: 'DEF' },
    { x: 45,  y: 80, role: 'DEF' },
    { x: 90,  y: 10, role: 'MID' },
    { x: 90,  y: 32, role: 'MID' },
    { x: 90,  y: 55, role: 'MID' },
    { x: 90,  y: 78, role: 'MID' },
    { x: 90,  y: 100,role: 'MID' },
    { x: 165, y: 38, role: 'FWD' },
    { x: 165, y: 72, role: 'FWD' },
  ],
  '4-3-1-2': [
    { x: 12,  y: 55, role: 'GK'  },
    { x: 45,  y: 20, role: 'DEF' },
    { x: 45,  y: 42, role: 'DEF' },
    { x: 45,  y: 68, role: 'DEF' },
    { x: 45,  y: 90, role: 'DEF' },
    { x: 88,  y: 25, role: 'MID' },
    { x: 88,  y: 55, role: 'MID' },
    { x: 88,  y: 85, role: 'MID' },
    { x: 130, y: 55, role: 'MID' },
    { x: 165, y: 38, role: 'FWD' },
    { x: 165, y: 72, role: 'FWD' },
  ],
}

// ── Defensive shape shift ────────────────────────────────────────────────────
// Shifts all outfield players toward own goal based on block height
function getDefensiveSlots(
  attackSlots: { x: number; y: number; role: string }[],
  block: string
): { x: number; y: number; role: string }[] {
  const shiftMap: Record<string, number> = {
    high: -5,   // push slightly forward
    mid:  15,   // pull back to mid
    low:  35,   // deep block — everyone drops
  }
  const shift = shiftMap[block] ?? 15

  return attackSlots.map((slot) => {
    if (slot.role === 'GK') return slot
    return { ...slot, x: Math.max(12, slot.x - shift) }
  })
}

// ── Outlier detection ────────────────────────────────────────────────────────
type HighlightType = 'inform' | 'dip' | 'weak' | null

function detectOutliers(xi: any[]): Map<number, HighlightType> {
  const highlights = new Map<number, HighlightType>()
  if (!xi.length) return highlights

  const formScores = xi
    .map((p) => p?.form_score)
    .filter((s) => s != null) as number[]

  if (formScores.length === 0) return highlights

  const avg = formScores.reduce((a, b) => a + b, 0) / formScores.length

  const candidates: { index: number; type: HighlightType; strength: number }[] = []

  xi.forEach((player, i) => {
    if (!player) return
    const form = player.form_score
    const roleRating = player.attributes?.role_rating

    // In form — significantly above average
    if (form != null && form > avg + 0.20 && form > 0.55) {
      candidates.push({ index: i, type: 'inform', strength: form - avg })
    }
    // Dip — significantly below average
    else if (form != null && form < avg - 0.20 && form < 0.45) {
      candidates.push({ index: i, type: 'dip', strength: avg - form })
    }
    // Weak link — low role rating regardless of form
    else if (roleRating != null && roleRating < 11) {
      candidates.push({ index: i, type: 'weak', strength: 11 - roleRating })
    }
  })

  // Sort by strength, cap at 3
  candidates
    .sort((a, b) => b.strength - a.strength)
    .slice(0, 3)
    .forEach(({ index, type }) => highlights.set(index, type))

  return highlights
}

// ── Props ────────────────────────────────────────────────────────────────────
interface FormationPitchProps {
  formation: string
  defensiveFormation?: string
  xi: any[]
  defensiveShape?: {
    block: string
    compactness: string
    press_trigger: string
    transition: string
    shape_label: string
  }
  linkupPairs?: {
    id: string
    player_a: string
    player_b: string
    description: string
  }[]
}

// ── Component ────────────────────────────────────────────────────────────────
export default function FormationPitch({
  formation,
  defensiveFormation,
  xi,
  defensiveShape,
  linkupPairs = [],
}: FormationPitchProps) {
  const attackSlots  = FORMATION_SLOTS[formation] || FORMATION_SLOTS['4-3-3']
    const defFormationSlots = defensiveFormation
        ? (FORMATION_SLOTS[defensiveFormation] || null)
        : null
    const defSlots = defFormationSlots
        ? defFormationSlots
        : getDefensiveSlots(attackSlots, defensiveShape?.block ?? 'mid')
  const highlights   = detectOutliers(xi)

  const [mode, setMode] = useState<'attack' | 'defense'>('attack')
  const [locked, setLocked] = useState<'attack' | 'defense' | null>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Auto-cycle attack → defense → attack every 4s unless locked
  useEffect(() => {
    if (locked) return
    timerRef.current = setTimeout(() => {
      setMode((m) => (m === 'attack' ? 'defense' : 'attack'))
    }, mode === 'attack' ? 3000 : 4000)
    return () => { if (timerRef.current) clearTimeout(timerRef.current) }
  }, [mode, locked])

  function handleToggle(next: 'attack' | 'defense') {
    if (timerRef.current) clearTimeout(timerRef.current)
    setMode(next)
    setLocked(next)
  }

  const activeSlots = mode === 'attack' ? attackSlots : defSlots

  // Build name → slot index map for linkup lines
  const nameToIndex = new Map<string, number>()
  xi.forEach((p, i) => { if (p?.name) nameToIndex.set(p.name, i) })

 return (
    <div className={styles.wrapper}>

      {/* Toggle */}
      <div className={styles.toggle}>
        <button
          className={`${styles.toggleBtn} ${mode === 'attack' ? styles.active : ''}`}
          onClick={() => handleToggle('attack')}
        >
          In possession
        </button>
        <button
          className={`${styles.toggleBtn} ${mode === 'defense' ? styles.active : ''}`}
          onClick={() => handleToggle('defense')}
        >
          Out of possession
        </button>
        {locked && (
          <button className={styles.autoBtn} onClick={() => setLocked(null)}>
            Auto
          </button>
        )}
      </div>

      {/* Shape label */}
      {defensiveShape?.shape_label && (
        <p className={styles.shapeLabel}>
          {mode === 'defense' ? defensiveShape.shape_label : `${formation} — attacking shape`}
        </p>
      )}

      <svg viewBox="0 0 200 110" className={styles.pitch}>

        {/* Pitch markings */}
        <g opacity="0.15">
          <rect x="4" y="4" width="192" height="102" fill="none" stroke="#3D3530" strokeWidth="0.6" rx="2" />
          <line x1="100" y1="4" x2="100" y2="106" stroke="#3D3530" strokeWidth="0.4" />
          <circle cx="100" cy="55" r="12" fill="none" stroke="#3D3530" strokeWidth="0.4" />
          <rect x="4"   y="33" width="18" height="44" fill="none" stroke="#3D3530" strokeWidth="0.4" />
          <rect x="178" y="33" width="18" height="44" fill="none" stroke="#3D3530" strokeWidth="0.4" />
          <rect x="4"   y="42" width="8"  height="26" fill="none" stroke="#3D3530" strokeWidth="0.3" />
          <rect x="188" y="42" width="8"  height="26" fill="none" stroke="#3D3530" strokeWidth="0.3" />
          <circle cx="100" cy="55" r="1.2" fill="#3D3530" opacity="0.4" />
        </g>

        {/* Linkup lines — attack mode only */}
        {mode === 'attack' && linkupPairs.map((pair, pi) => {
          const idxA = nameToIndex.get(pair.player_a)
          const idxB = nameToIndex.get(pair.player_b)
          if (idxA == null || idxB == null) return null
          const slotA = attackSlots[idxA]
          const slotB = attackSlots[idxB]
          if (!slotA || !slotB) return null
          return (
            <motion.line
              key={pair.id}
              x1={slotA.x} y1={slotA.y}
              x2={slotB.x} y2={slotB.y}
              stroke="#B86A3C"
              strokeWidth="0.6"
              strokeDasharray="2 2"
              initial={{ opacity: 0, pathLength: 0 }}
              animate={{ opacity: 0.5, pathLength: 1 }}
              transition={{ duration: 0.8, delay: pi * 0.2 }}
            />
          )
        })}

        {/* Players */}
        {activeSlots.map((slot, i) => {
          const player   = xi[i]
          const initials = player?.name
            ? player.name.split(' ').map((n: string) => n[0]).join('').slice(0, 2)
            : '?'
          const highlight = highlights.get(i)
          const ringColor = highlight ? HIGHLIGHT_COLORS[highlight] : null

          return (
            <g
              key={i}
              style={{
                transform: `translate(${slot.x}px, ${slot.y}px)`,
                transition: 'transform 1.2s ease-in-out',
              }}
            >
              {ringColor && (
                <circle cx={0} cy={0} r="9"
                  fill="none"
                  stroke={ringColor}
                  strokeWidth="0.8"
                  opacity="0.7"
                />
              )}
              <circle cx={0} cy={0} r="6"
                fill={ROLE_COLORS[slot.role]}
                opacity="0.92"
              />
              <circle cx={0} cy={0} r="7.5"
                fill="none"
                stroke={ROLE_COLORS[slot.role]}
                strokeWidth="0.4"
                opacity="0.3"
              />
              <text
                x={0} y={1.2}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize="3.2"
                fill="#F7F3EE"
                fontFamily="monospace"
                fontWeight="600"
              >
                {initials}
              </text>
              {player?.name && (
                <text
                  x={0} y={10}
                  textAnchor="middle"
                  fontSize="3"
                  fill="#3D3530"
                  fontFamily="monospace"
                  opacity="0.75"
                >
                  {player.name.split(' ')[0]}
                </text>
              )}
            </g>
          )
        })}

      </svg>

      {/* Highlight legend — outside svg */}
      {highlights.size > 0 && (
        <div className={styles.legend}>
          {Array.from(highlights.entries()).map(([i, type]) => {
            if (!type || !xi[i]) return null
            const labels = {
              inform: '↑ In form',
              dip:    '↓ Form dip',
              weak:   '⚠ Weak link',
            }
            return (
              <div key={i} className={styles.legendItem}>
                <span
                  className={styles.legendDot}
                  style={{ background: HIGHLIGHT_COLORS[type] }}
                />
                <span className={styles.legendName}>{xi[i].name?.split(' ')[0]}</span>
                <span className={styles.legendType}>{labels[type]}</span>
              </div>
            )
          })}
        </div>
      )}

    </div>
  )
}