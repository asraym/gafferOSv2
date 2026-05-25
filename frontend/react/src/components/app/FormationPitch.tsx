'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence, useAnimation } from 'framer-motion'
import styles from './FormationPitch.module.css'

// ─── Types ───────────────────────────────────────────────────────────────────

interface Player {
  name: string
  position?: string
  broad_position?: string
  specific_position?: string
  slot_broad?: string
  form_score?: number | null
  attributes?: Record<string, number | undefined>
  traits?: string[]
  tactical_profile?: Record<string, number>
}

interface LinkupPair {
  id: string
  player_a: string
  player_b: string
  description: string
}

interface DefensiveShape {
  block: string
  compactness: string
  press_trigger: string
  transition: string
  shape_label: string
}

interface OppositionProfile {
  likely_formation?: string
  press_style?: string
  defensive_line?: string
  playing_style?: string
  set_piece_threat?: string
  opponent_strength?: string
  attributes?: Record<string, string>
}

interface FormationPitchProps {
  formation: string
  defensiveFormation?: string
  xi: Player[]
  bench?: Player[]
  defensiveShape?: DefensiveShape
  linkupPairs?: LinkupPair[]
  opposition?: OppositionProfile
  tacticalFocus?: string
  pressIntensity?: string
  matchRiskLevel?: string
  matchupExploits?: string[]
  matchupVulnerabilities?: string[]
}

// ─── Pitch dimensions (viewBox 0 0 220 130) ──────────────────────────────────
// GK on LEFT, attack goes RIGHT

const PW = 220
const PH = 130

// ─── Formation slots ─────────────────────────────────────────────────────────

type Slot = { x: number; y: number; role: string }

const FORMATION_SLOTS: Record<string, Slot[]> = {
  '4-3-3': [
    { x: 14, y: 65, role: 'GK' },
    { x: 52, y: 20, role: 'DEF' }, { x: 52, y: 45, role: 'DEF' },
    { x: 52, y: 85, role: 'DEF' }, { x: 52, y: 110, role: 'DEF' },
    { x: 100, y: 32, role: 'MID' }, { x: 100, y: 65, role: 'MID' }, { x: 100, y: 98, role: 'MID' },
    { x: 175, y: 20, role: 'FWD' }, { x: 175, y: 65, role: 'FWD' }, { x: 175, y: 110, role: 'FWD' },
  ],
  '4-4-2': [
    { x: 14, y: 65, role: 'GK' },
    { x: 52, y: 20, role: 'DEF' }, { x: 52, y: 48, role: 'DEF' },
    { x: 52, y: 82, role: 'DEF' }, { x: 52, y: 110, role: 'DEF' },
    { x: 108, y: 20, role: 'MID' }, { x: 108, y: 48, role: 'MID' },
    { x: 108, y: 82, role: 'MID' }, { x: 108, y: 110, role: 'MID' },
    { x: 178, y: 42, role: 'FWD' }, { x: 178, y: 88, role: 'FWD' },
  ],
  '4-2-3-1': [
    { x: 14, y: 65, role: 'GK' },
    { x: 52, y: 20, role: 'DEF' }, { x: 52, y: 48, role: 'DEF' },
    { x: 52, y: 82, role: 'DEF' }, { x: 52, y: 110, role: 'DEF' },
    { x: 92, y: 44, role: 'MID' }, { x: 92, y: 86, role: 'MID' },
    { x: 138, y: 20, role: 'MID' }, { x: 138, y: 65, role: 'MID' }, { x: 138, y: 110, role: 'MID' },
    { x: 190, y: 65, role: 'FWD' },
  ],
  '4-4-1-1': [
    { x: 14, y: 65, role: 'GK' },
    { x: 52, y: 20, role: 'DEF' }, { x: 52, y: 48, role: 'DEF' },
    { x: 52, y: 82, role: 'DEF' }, { x: 52, y: 110, role: 'DEF' },
    { x: 108, y: 20, role: 'MID' }, { x: 108, y: 48, role: 'MID' },
    { x: 108, y: 82, role: 'MID' }, { x: 108, y: 110, role: 'MID' },
    { x: 158, y: 65, role: 'FWD' },
    { x: 190, y: 65, role: 'FWD' },
  ],
  '4-1-4-1': [
    { x: 14, y: 65, role: 'GK' },
    { x: 52, y: 20, role: 'DEF' }, { x: 52, y: 48, role: 'DEF' },
    { x: 52, y: 82, role: 'DEF' }, { x: 52, y: 110, role: 'DEF' },
    { x: 88, y: 65, role: 'MID' },
    { x: 130, y: 15, role: 'MID' }, { x: 130, y: 45, role: 'MID' },
    { x: 130, y: 85, role: 'MID' }, { x: 130, y: 115, role: 'MID' },
    { x: 190, y: 65, role: 'FWD' },
  ],
  '5-4-1': [
    { x: 14, y: 65, role: 'GK' },
    { x: 52, y: 12, role: 'DEF' }, { x: 52, y: 36, role: 'DEF' },
    { x: 52, y: 65, role: 'DEF' }, { x: 52, y: 94, role: 'DEF' }, { x: 52, y: 118, role: 'DEF' },
    { x: 110, y: 24, role: 'MID' }, { x: 110, y: 52, role: 'MID' },
    { x: 110, y: 78, role: 'MID' }, { x: 110, y: 106, role: 'MID' },
    { x: 190, y: 65, role: 'FWD' },
  ],
  '4-5-1': [
    { x: 14, y: 65, role: 'GK' },
    { x: 52, y: 20, role: 'DEF' }, { x: 52, y: 48, role: 'DEF' },
    { x: 52, y: 82, role: 'DEF' }, { x: 52, y: 110, role: 'DEF' },
    { x: 108, y: 12, role: 'MID' }, { x: 108, y: 36, role: 'MID' }, { x: 108, y: 65, role: 'MID' },
    { x: 108, y: 94, role: 'MID' }, { x: 108, y: 118, role: 'MID' },
    { x: 190, y: 65, role: 'FWD' },
  ],
  '3-5-2': [
    { x: 14, y: 65, role: 'GK' },
    { x: 52, y: 32, role: 'DEF' }, { x: 52, y: 65, role: 'DEF' }, { x: 52, y: 98, role: 'DEF' },
    { x: 100, y: 12, role: 'MID' }, { x: 100, y: 38, role: 'MID' }, { x: 100, y: 65, role: 'MID' },
    { x: 100, y: 92, role: 'MID' }, { x: 100, y: 118, role: 'MID' },
    { x: 178, y: 42, role: 'FWD' }, { x: 178, y: 88, role: 'FWD' },
  ],
  '4-3-1-2': [
    { x: 14, y: 65, role: 'GK' },
    { x: 52, y: 20, role: 'DEF' }, { x: 52, y: 48, role: 'DEF' },
    { x: 52, y: 82, role: 'DEF' }, { x: 52, y: 110, role: 'DEF' },
    { x: 95, y: 28, role: 'MID' }, { x: 95, y: 65, role: 'MID' }, { x: 95, y: 102, role: 'MID' },
    { x: 145, y: 65, role: 'MID' },
    { x: 185, y: 42, role: 'FWD' }, { x: 185, y: 88, role: 'FWD' },
  ],
}

// ─── Mirror for opposition (attacks right→left) ───────────────────────────────

function mirrorSlots(slots: Slot[]): Slot[] {
  return slots.map(s => ({ ...s, x: PW - s.x }))
}

// ─── Defensive drop ───────────────────────────────────────────────────────────

function getDefensiveSlots(slots: Slot[], block: string): Slot[] {
  const shift: Record<string, number> = { high: -6, mid: 22, low: 45, deep: 45 }
  const dx = shift[block] ?? 22
  return slots.map(s => s.role === 'GK' ? s : { ...s, x: Math.max(14, s.x - dx) })
}

// ─── Outlier detection ────────────────────────────────────────────────────────

type Highlight = 'inform' | 'weak' | null

function detectOutliers(xi: Player[]): Map<number, Highlight> {
  const map = new Map<number, Highlight>()
  if (!xi.length) return map
  const scores = xi.map(p => p.form_score).filter(s => s != null) as number[]
  if (!scores.length) return map
  const avg = scores.reduce((a, b) => a + b, 0) / scores.length
  const candidates: { i: number; type: Highlight; strength: number }[] = []
  xi.forEach((p, i) => {
    const f = p.form_score
    const rr = p.attributes?.role_rating
    if (f != null && f < avg - 0.2 && f < 0.4)
      candidates.push({ i, type: 'weak', strength: avg - f })
    else if (rr != null && rr < 11)
      candidates.push({ i, type: 'weak', strength: 11 - rr })
    else if (f != null && f > avg + 0.2 && f > 0.55)
      candidates.push({ i, type: 'inform', strength: f - avg })
  })
  candidates.sort((a, b) => b.strength - a.strength).slice(0, 3)
    .forEach(({ i, type }) => map.set(i, type))
  return map
}

// ─── Trait → movement + label ─────────────────────────────────────────────────

const TRAIT_MOVES: Record<string, Record<string, [number, number]>> = {
  goal_kick: {
    'Ball Playing Defender': [-8, 0],
    'Deep Playmaker': [-12, 0],
    'Sweeper Keeper': [10, 0],
    'Drops Deep': [-18, 0],
    'Overlapping Full-Back': [8, 0],
    'Stays Back': [-4, 0],
    'Progressive Passer': [6, 0],
    'Organises Defence': [0, 0],
  },
  counter: {
    'Runs In Behind': [28, 0],
    'Late Run Into Box': [25, -8],
    'Drifts Into Channels': [16, -14],
    'Drifts Central': [10, -12],
    'Counterattacking Runner': [24, 0],
    'Overlapping Full-Back': [26, 0],
    'Offensive Full-Back': [28, 0],
    'Box To Box': [20, 0],
    'Holds Width': [0, 0],
    'Deep Playmaker': [0, 0],
    'Stays Back': [-2, 0],
    'Target Man': [6, 0],
    'Presses High': [14, 0],
  },
  featured: {
    'Overlapping Full-Back': [22, -6],
    'Offensive Full-Back': [24, -6],
    'Holds Width': [0, -4],
    'Drifts Central': [6, 10],
    'Cuts Inside': [6, 14],
    'Late Run Into Box': [20, -10],
    'Runs In Behind': [18, -10],
    'Combination Play': [6, 0],
    'Progressive Passer': [8, 0],
    'Ball Playing Defender': [-6, 0],
  },
}

const TRAIT_LABELS: Record<string, string> = {
  'Ball Playing Defender': 'Builds from back',
  'Deep Playmaker': 'Drops between CBs',
  'Progressive Passer': 'Progresses play',
  'Overlapping Full-Back': 'Overlapping run',
  'Offensive Full-Back': 'Bombs forward',
  'Stays Back': 'Holds shape',
  'Drops Deep': 'Drops to receive',
  'Sweeper Keeper': 'Plays out wide',
  'Runs In Behind': 'Run in behind',
  'Late Run Into Box': 'Late run into box',
  'Drifts Into Channels': 'Drifts into channel',
  'Drifts Central': 'Drifts central',
  'Counterattacking Runner': 'Bursting forward',
  'Box To Box': 'Joins the attack',
  'Holds Width': 'Holds width',
  'Target Man': 'Holds up play',
  'Presses High': 'Pressing high',
  'Cuts Inside': 'Cuts inside',
  'Combination Play': 'Combination',
  'Organises Defence': 'Organising shape',
}

// ─── Role-based default movements (everyone moves, not just trait players) ────

type ScenarioId = 'goal_kick' | 'counter' | 'featured' | 'oop_defend' | 'oop_counter'

function getRoleMovement(role: string, slotIndex: number, scenario: ScenarioId, slotY: number): [number, number] {
  const isTopHalf = slotY < PH / 2
  const yMirror = isTopHalf ? 1 : -1

  if (scenario === 'goal_kick') {
    if (role === 'DEF') return [-4, slotIndex % 2 === 0 ? 4 * yMirror : -4 * yMirror]
    if (role === 'MID') return [8, slotIndex % 2 === 0 ? 3 * yMirror : -3 * yMirror]
    if (role === 'FWD') return [0, slotIndex % 2 === 0 ? 5 * yMirror : -5 * yMirror]
  }
  if (scenario === 'counter') {
    if (role === 'DEF') return [2, 0]
    if (role === 'MID') return [12, slotIndex % 2 === 0 ? 4 * yMirror : -4 * yMirror]
    if (role === 'FWD') return [10, 0]
  }
  if (scenario === 'featured') {
    if (role === 'DEF') return [-2, slotIndex % 2 === 0 ? 5 * yMirror : -5 * yMirror]
    if (role === 'MID') return [10, slotIndex % 2 === 0 ? 6 * yMirror : -6 * yMirror]
    if (role === 'FWD') return [5, 0]
  }
  return [0, 0]
}

// ─── Ball paths per scenario ──────────────────────────────────────────────────

// Returns SVG path string and keyframe positions [{x,y}]
function getBallPath(scenario: ScenarioId, slots: Slot[]): { path: string; points: {x:number;y:number}[] } {
  if (scenario === 'goal_kick') {
    const gk = slots[0]
    const cbL = slots[1] ?? { x: 52, y: 45 }
    const cdm = slots[5] ?? { x: 90, y: 65 }
    const cb2 = slots[2] ?? { x: 52, y: 85 }
    const points = [
      { x: gk.x, y: gk.y },
      { x: cbL.x - 5, y: cbL.y + 8 },
      { x: cdm.x, y: cdm.y },
      { x: cb2.x + 5, y: cb2.y - 8 },
      { x: cdm.x + 15, y: cdm.y - 10 },
    ]
    return {
      path: `M ${points[0].x} ${points[0].y} Q ${points[1].x} ${points[1].y} ${points[2].x} ${points[2].y} Q ${points[3].x} ${points[3].y} ${points[4].x} ${points[4].y}`,
      points,
    }
  }
  if (scenario === 'counter') {
    const cdm = slots[5] ?? { x: 90, y: 65 }
    const cam = slots[9] ?? { x: 158, y: 65 }
    const fwd = slots[10] ?? { x: 190, y: 65 }
    const points = [
      { x: cdm.x, y: cdm.y },
      { x: (cdm.x + cam.x) / 2, y: cdm.y - 15 },
      { x: cam.x, y: cam.y },
      { x: fwd.x - 10, y: fwd.y - 20 },
      { x: fwd.x, y: fwd.y },
    ]
    return {
      path: `M ${points[0].x} ${points[0].y} Q ${points[1].x} ${points[1].y} ${points[2].x} ${points[2].y} Q ${points[3].x} ${points[3].y} ${points[4].x} ${points[4].y}`,
      points,
    }
  }
  if (scenario === 'featured') {
    const cb = slots[2] ?? { x: 52, y: 48 }
    const fb = slots[1] ?? { x: 52, y: 20 }
    const mid = slots[6] ?? { x: 108, y: 48 }
    const cam = slots[9] ?? { x: 158, y: 65 }
    const points = [
      { x: cb.x, y: cb.y },
      { x: fb.x + 10, y: fb.y + 5 },
      { x: mid.x, y: mid.y },
      { x: cam.x - 15, y: cam.y - 20 },
      { x: cam.x, y: cam.y },
    ]
    return {
      path: `M ${points[0].x} ${points[0].y} Q ${points[1].x} ${points[1].y} ${points[2].x} ${points[2].y} Q ${points[3].x} ${points[3].y} ${points[4].x} ${points[4].y}`,
      points,
    }
  }
  return { path: '', points: [] }
}

// ─── Opposition reactions per scenario ────────────────────────────────────────

function getOppReaction(
  slot: Slot,
  index: number,
  scenario: ScenarioId,
  ballPos: { x: number; y: number },
  pressStyle: string
): { x: number; y: number } {
  const isHighPress = pressStyle === 'high'

  if (scenario === 'goal_kick') {
    // Opposition sits in shape, slight pressure based on press style
    if (slot.role === 'FWD') {
      return { x: slot.x - (isHighPress ? 20 : 8), y: slot.y }
    }
    if (slot.role === 'MID') {
      return { x: slot.x - (isHighPress ? 10 : 4), y: slot.y }
    }
    return slot
  }

  if (scenario === 'counter') {
    // Opposition scrambles back
    if (slot.role === 'FWD') return { x: slot.x - 10, y: slot.y + (slot.y > PH / 2 ? -8 : 8) }
    if (slot.role === 'MID') return { x: slot.x - 5, y: slot.y }
    if (slot.role === 'DEF') return { x: slot.x + 3, y: slot.y }
    return slot
  }

  if (scenario === 'featured') {
    // Opposition shifts to ball side
    const ballSideShift = ballPos.y < PH / 2 ? -6 : 6
    if (slot.role === 'MID') return { x: slot.x, y: slot.y + ballSideShift }
    if (slot.role === 'DEF') return { x: slot.x + 4, y: slot.y + ballSideShift * 0.5 }
    return slot
  }

  return slot
}

// ─── Passing lane targets ─────────────────────────────────────────────────────

function getPassingLanes(scenario: ScenarioId, slots: Slot[]): [number, number][] {
  if (scenario === 'goal_kick') {
    return [[0, 1], [1, 5], [2, 5], [5, 6]]
  }
  if (scenario === 'counter') {
    return [[5, 9], [9, 10], [6, 10], [8, 9]]
  }
  if (scenario === 'featured') {
    return [[2, 6], [6, 9], [1, 6], [9, 10]]
  }
  return []
}

// ─── Featured scenario label ──────────────────────────────────────────────────

function getFeaturedLabel(focus?: string): { label: string; desc: string } {
  const f = (focus ?? '').toLowerCase()
  if (f.includes('wide') || f.includes('wing')) return { label: 'Wing Play', desc: 'Width + overlaps stretch the defence' }
  if (f.includes('press')) return { label: 'High Press', desc: 'Collective press from the front line' }
  if (f.includes('counter')) return { label: 'Counter', desc: 'Rapid transition on winning possession' }
  return { label: 'Build-Up', desc: 'Patient build from deep positions' }
}

// ─── Colour palette ────────────────────────────────────────────────────────────

const JERSEY_COLORS = [
  '#B86A3C', '#c0392b', '#2d5fa0', '#3a8a5a',
  '#8a3a6a', '#5a3a8a', '#8a7a3a', '#2c7a7a',
]

// ─── Main component ───────────────────────────────────────────────────────────

export default function FormationPitch({
  formation,
  defensiveFormation,
  xi = [],
  defensiveShape,
  linkupPairs = [],
  opposition,
  tacticalFocus,
  pressIntensity,
  matchupExploits = [],
  matchupVulnerabilities = [],
}: FormationPitchProps) {

  const [scenario, setScenario] = useState<ScenarioId>('goal_kick')
  const [jerseyColor, setJerseyColor] = useState('#B86A3C')
  const [oppColor, setOppColor] = useState('#2d5fa0')
  const [colorPicker, setColorPicker] = useState<'own' | 'opp' | null>(null)
  const [traitLabels, setTraitLabels] = useState<Map<number, string>>(new Map())
  const [animating, setAnimating] = useState(false)
  const [ballPos, setBallPos] = useState<{ x: number; y: number }>({ x: 14, y: 65 })
  const [ballVisible, setBallVisible] = useState(true)
  const [laneOpacity, setLaneOpacity] = useState(0)
  const animTimer = useRef<ReturnType<typeof setTimeout>[]>([])

  const isDefenseScenario = scenario === 'oop_defend' || scenario === 'oop_counter'
  const attackSlots = FORMATION_SLOTS[formation] ?? FORMATION_SLOTS['4-4-1-1']
  const defFormSlots = defensiveFormation ? (FORMATION_SLOTS[defensiveFormation] ?? null) : null
  const defSlots = defFormSlots ?? getDefensiveSlots(attackSlots, defensiveShape?.block ?? 'mid')
  const oppFormation = opposition?.likely_formation
  const oppSlots = mirrorSlots(FORMATION_SLOTS[oppFormation ?? '4-3-3'] ?? FORMATION_SLOTS['4-3-3'])
  const highlights = detectOutliers(xi)
  const featured = getFeaturedLabel(tacticalFocus)
  const pressStyle = opposition?.press_style ?? 'medium'

  const activeSlots = isDefenseScenario ? defSlots : attackSlots

  const nameToIndex = new Map<string, number>()
  xi.forEach((p, i) => { if (p?.name) nameToIndex.set(p.name, i) })

  // Clear timers on unmount
  useEffect(() => {
    return () => animTimer.current.forEach(clearTimeout)
  }, [])

  function clearTimers() {
    animTimer.current.forEach(clearTimeout)
    animTimer.current = []
  }

  function handleScenario(s: ScenarioId) {
    clearTimers()
    setAnimating(false)
    setTraitLabels(new Map())
    setLaneOpacity(0)
    setScenario(s)

    if (s === 'oop_defend' || s === 'oop_counter') {
      setBallVisible(false)
      return
    }

    // Animate ball along path
    setBallVisible(true)
    const { points } = getBallPath(s, attackSlots)
    if (points.length > 0) {
      setBallPos(points[0])
      points.forEach((pt, i) => {
        const t = animTimer.current[animTimer.current.length] = setTimeout(() => {
          setBallPos(pt)
        }, i * 600)
        animTimer.current.push(t)
      })
    }

    // Trigger player movement + trait labels
    const t1 = setTimeout(() => {
      setAnimating(true)
      const labels = new Map<number, string>()
      xi.forEach((p, i) => {
        if (!p.traits) return
        const traitMap = TRAIT_MOVES[s] ?? {}
        for (const trait of p.traits) {
          if (traitMap[trait] && TRAIT_LABELS[trait]) {
            labels.set(i, TRAIT_LABELS[trait])
            break
          }
        }
      })
      setTraitLabels(labels)
      setLaneOpacity(1)
    }, 300)
    animTimer.current.push(t1)

    // Fade out trait labels after 3s
    const t2 = setTimeout(() => {
      setTraitLabels(new Map())
    }, 3400)
    animTimer.current.push(t2)
  }

  // Compute player animated position
  function getPlayerPos(player: Player, i: number): { x: number; y: number } {
    if (!animating || isDefenseScenario) return activeSlots[i] ?? { x: 100, y: 65 }
    const base = attackSlots[i] ?? { x: 100, y: 65 }

    // Check trait first
    const traitMap = TRAIT_MOVES[scenario] ?? {}
    let dx = 0, dy = 0
    if (player.traits) {
      for (const trait of player.traits) {
        if (traitMap[trait]) {
          ;[dx, dy] = traitMap[trait]
          // Mirror Y for bottom-half players
          if (base.y > PH / 2) dy = -dy
          break
        }
      }
    }

    // Apply role movement if no trait movement
    if (dx === 0 && dy === 0) {
      const [rdx, rdy] = getRoleMovement(base.role, i, scenario, base.y)
      dx = rdx; dy = rdy
    }

    return {
      x: Math.min(PW - 8, Math.max(8, base.x + dx)),
      y: Math.min(PH - 8, Math.max(8, base.y + dy)),
    }
  }

  // Get opposition position (reacts to scenario + ball)
  function getOppPos(slot: Slot, index: number): { x: number; y: number } {
    if (!animating) return slot
    return getOppReaction(slot, index, scenario, ballPos, pressStyle)
  }

  // Passing lane pairs
  const laneSlotPairs = getPassingLanes(scenario, attackSlots)

  const scenarios = [
    { id: 'goal_kick' as ScenarioId, label: 'Goal kick', icon: '▶', phase: 'attack' },
    { id: 'counter' as ScenarioId, label: 'Win ball', icon: '⚡', phase: 'attack' },
    { id: 'featured' as ScenarioId, label: featured.label, icon: '★', phase: 'attack' },
    { id: 'oop_defend' as ScenarioId, label: 'Defensive shape', icon: '⬛', phase: 'defense' },
    { id: 'oop_counter' as ScenarioId, label: 'Their break', icon: '↩', phase: 'defense' },
  ]

  return (
    <div className={styles.wrapper}>

      {/* Header */}
      <div className={styles.header}>
        <div className={styles.formationBadge}>
          <span className={styles.formationText}>{isDefenseScenario && defensiveFormation ? defensiveFormation : formation}</span>
          <span className={styles.formationPhase}>{isDefenseScenario ? 'out of possession' : 'in possession'}</span>
        </div>
        <div className={styles.colorPickers}>
          {(['own', 'opp'] as const).map(side => (
            <div key={side} className={styles.colorPickerGroup}>
              <span className={styles.colorLabel}>{side === 'own' ? 'Us' : 'Them'}</span>
              <div
                className={styles.colorSwatch}
                style={{ background: side === 'own' ? jerseyColor : oppColor }}
                onClick={() => setColorPicker(p => p === side ? null : side)}
              />
              {colorPicker === side && (
                <div className={styles.colorPalette}>
                  {JERSEY_COLORS.map(c => (
                    <div
                      key={c}
                      className={`${styles.paletteColor} ${(side === 'own' ? jerseyColor : oppColor) === c ? styles.paletteActive : ''}`}
                      style={{ background: c }}
                      onClick={() => {
                        side === 'own' ? setJerseyColor(c) : setOppColor(c)
                        setColorPicker(null)
                      }}
                    />
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Scenario tabs */}
      <div className={styles.scenarioTabs}>
        {scenarios.map(s => (
          <button
            key={s.id}
            className={`${styles.tab} ${scenario === s.id ? styles.tabActive : ''} ${s.phase === 'defense' ? styles.tabDefense : ''}`}
            onClick={() => handleScenario(s.id)}
          >
            <span>{s.icon}</span>
            <span>{s.label}</span>
          </button>
        ))}
      </div>

      {/* Scenario desc */}
      <div className={styles.scenarioDesc}>
        {scenarios.find(s => s.id === scenario)?.phase === 'attack'
          ? (scenario === 'featured' ? featured.desc : scenario === 'goal_kick' ? 'Building from goalkeeper — short passing from back' : 'Rapid transition — exploit space on turnover')
          : scenario === 'oop_defend' ? 'Organised defensive block — holding shape' : 'Opposition on the break — tracking runners'
        }
        {opposition?.likely_formation && isDefenseScenario && (
          <span className={styles.oppTag}> vs {opposition.likely_formation}</span>
        )}
      </div>

      {/* ══ PITCH ══ */}
      <div className={styles.pitchWrap}>
        <svg viewBox={`0 0 ${PW} ${PH}`} className={styles.pitch}>

          {/* Grass stripes */}
          {Array.from({ length: 8 }).map((_, i) => (
            <rect key={i} x={i * (PW / 8)} y={0} width={PW / 8} height={PH}
              fill={i % 2 === 0 ? 'rgba(255,255,255,0.025)' : 'rgba(0,0,0,0.04)'} />
          ))}

          {/* Pitch lines */}
          <g stroke="rgba(255,255,255,0.16)" fill="none" strokeWidth="0.5">
            <rect x="4" y="4" width={PW - 8} height={PH - 8} rx="1.5" />
            <line x1={PW / 2} y1="4" x2={PW / 2} y2={PH - 4} />
            <circle cx={PW / 2} cy={PH / 2} r="16" />
            <circle cx={PW / 2} cy={PH / 2} r="1" fill="rgba(255,255,255,0.3)" stroke="none" />
            {/* Left penalty area */}
            <rect x="4" y="36" width="26" height="58" />
            <rect x="4" y="50" width="10" height="30" />
            {/* Right penalty area */}
            <rect x={PW - 30} y="36" width="26" height="58" />
            <rect x={PW - 14} y="50" width="10" height="30" />
            {/* Goals */}
            <rect x="1" y="52" width="3" height="26" stroke="rgba(255,255,255,0.5)" />
            <rect x={PW - 4} y="52" width="3" height="26" stroke="rgba(255,255,255,0.5)" />
            {/* Penalty spots */}
            <circle cx="22" cy={PH / 2} r="0.8" fill="rgba(255,255,255,0.25)" stroke="none" />
            <circle cx={PW - 22} cy={PH / 2} r="0.8" fill="rgba(255,255,255,0.25)" stroke="none" />
            {/* Arcs */}
            <path d={`M 30 50 A 12 12 0 0 1 30 80`} />
            <path d={`M ${PW - 30} 50 A 12 12 0 0 0 ${PW - 30} 80`} />
          </g>

          {/* ── Passing lanes ── */}
          {!isDefenseScenario && laneSlotPairs.map(([ia, ib], li) => {
            const pa = animating ? getPlayerPos(xi[ia] ?? {}, ia) : (attackSlots[ia] ?? { x: 0, y: 0 })
            const pb = animating ? getPlayerPos(xi[ib] ?? {}, ib) : (attackSlots[ib] ?? { x: 0, y: 0 })
            return (
              <motion.line
                key={`lane-${li}`}
                x1={pa.x} y1={pa.y}
                x2={pb.x} y2={pb.y}
                stroke="rgba(255,255,255,0.12)"
                strokeWidth="0.6"
                strokeDasharray="3 2"
                animate={{ opacity: laneOpacity * 0.5 }}
                transition={{ duration: 0.5, delay: li * 0.1 }}
              />
            )
          })}

          {/* ── Linkup pair lines ── */}
          {!isDefenseScenario && linkupPairs.map((pair, pi) => {
            const ia = nameToIndex.get(pair.player_a)
            const ib = nameToIndex.get(pair.player_b)
            if (ia == null || ib == null) return null
            const pa = animating ? getPlayerPos(xi[ia], ia) : (attackSlots[ia] ?? { x: 0, y: 0 })
            const pb = animating ? getPlayerPos(xi[ib], ib) : (attackSlots[ib] ?? { x: 0, y: 0 })
            return (
              <motion.line
                key={pair.id}
                x1={pa.x} y1={pa.y} x2={pb.x} y2={pb.y}
                stroke="rgba(255,220,80,0.65)"
                strokeWidth="0.8"
                strokeLinecap="round"
                animate={{ opacity: laneOpacity * 0.9 }}
                transition={{ duration: 0.6, delay: 0.4 + pi * 0.15 }}
              />
            )
          })}

          {/* ── Ball ── */}
          <AnimatePresence>
            {ballVisible && !isDefenseScenario && (
              <motion.g
                key="ball"
                animate={{ cx: ballPos.x, cy: ballPos.y }}
                transition={{ duration: 0.55, ease: [0.25, 0.46, 0.45, 0.94] }}
              >
                <motion.circle
                  cx={ballPos.x} cy={ballPos.y} r="2.8"
                  fill="white"
                  animate={{ cx: ballPos.x, cy: ballPos.y }}
                  transition={{ duration: 0.55, ease: [0.25, 0.46, 0.45, 0.94] }}
                />
                <motion.circle
                  cx={ballPos.x} cy={ballPos.y} r="4.5"
                  fill="none"
                  stroke="rgba(255,255,255,0.2)"
                  strokeWidth="0.5"
                  animate={{ cx: ballPos.x, cy: ballPos.y }}
                  transition={{ duration: 0.55, ease: [0.25, 0.46, 0.45, 0.94] }}
                />
              </motion.g>
            )}
          </AnimatePresence>

          {/* ── Opposition players ── */}
          {oppSlots.map((slot, i) => {
            const pos = getOppPos(slot, i)
            const oppOpacity = isDefenseScenario ? 0.88 : 0.28
            return (
              <motion.g
                key={`opp-${i}`}
                animate={{ x: pos.x, y: pos.y }}
                initial={{ x: slot.x, y: slot.y }}
                transition={{ duration: 0.8, ease: [0.25, 0.46, 0.45, 0.94], delay: i * 0.02 }}
              >
                <circle cx={0} cy={0} r="5"
                  fill={oppColor}
                  opacity={oppOpacity}
                />
                <circle cx={0} cy={0} r="6.2"
                  fill="none"
                  stroke={oppColor}
                  strokeWidth="0.5"
                  opacity={oppOpacity * 0.4}
                />
                <text x={0} y={0.9}
                  textAnchor="middle" dominantBaseline="middle"
                  fontSize="2.8" fill="rgba(255,255,255,0.85)"
                  fontFamily="monospace" fontWeight="700"
                >
                  {i + 1}
                </text>
                <text x={0} y={9}
                  textAnchor="middle" fontSize="2.4"
                  fill={`rgba(255,255,255,${oppOpacity * 0.5})`}
                  fontFamily="monospace"
                >
                  {slot.role}
                </text>
              </motion.g>
            )
          })}

          {/* ── Your players ── */}
          {activeSlots.map((slot, i) => {
            const player = xi[i]
            if (!player) return null
            const highlight = highlights.get(i)
            const traitLabel = traitLabels.get(i)
            const pos = getPlayerPos(player, i)
            const hasTrait = traitLabels.has(i)
            const initials = player.name
              ? player.name.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase()
              : '?'

            return (
              <motion.g
                key={i}
                animate={{ x: pos.x, y: pos.y }}
                initial={{ x: attackSlots[i]?.x ?? slot.x, y: attackSlots[i]?.y ?? slot.y }}
                transition={{ duration: 0.85, ease: [0.25, 0.46, 0.45, 0.94], delay: i * 0.02 }}
              >
                {/* Weak glow */}
                {highlight === 'weak' && (
                  <motion.circle cx={0} cy={0} r={10}
                    fill="rgba(220,50,50,0.12)"
                    stroke="rgba(220,50,50,0.45)"
                    strokeWidth="0.6"
                    animate={{ r: [9, 11.5, 9], opacity: [0.5, 0.9, 0.5] }}
                    transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                  />
                )}

                {/* In-form ring */}
                {highlight === 'inform' && (
                  <motion.circle cx={0} cy={0} r={9}
                    fill="none"
                    stroke="rgba(80,200,120,0.75)"
                    strokeWidth="0.8"
                    animate={{ opacity: [0.5, 1, 0.5] }}
                    transition={{ duration: 2.2, repeat: Infinity }}
                  />
                )}

                {/* Trait-active ring */}
                {hasTrait && (
                  <motion.circle cx={0} cy={0} r={8.5}
                    fill="none"
                    stroke="rgba(255,200,80,0.55)"
                    strokeWidth="0.5"
                    strokeDasharray="2.5 1.5"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 2.5, repeat: Infinity, ease: 'linear' }}
                    style={{ originX: 0, originY: 0 }}
                  />
                )}

                {/* Jersey */}
                <motion.circle
                  cx={0} cy={0}
                  animate={{ r: hasTrait ? 6.8 : 6 }}
                  transition={{ duration: 0.3 }}
                  fill={jerseyColor}
                  style={{
                    filter: hasTrait ? `drop-shadow(0 0 4px ${jerseyColor}cc)` : 'none',
                  }}
                />
                {/* Shine */}
                <circle cx={-1.8} cy={-2.2} r={2.2} fill="rgba(255,255,255,0.14)" />

                {/* Initials */}
                <text x={0} y={0.9}
                  textAnchor="middle" dominantBaseline="middle"
                  fontSize="3" fill="rgba(255,255,255,0.95)"
                  fontFamily="monospace" fontWeight="700"
                >
                  {initials}
                </text>

                {/* Name */}
                <text x={0} y={10.5}
                  textAnchor="middle" fontSize="2.6"
                  fill="rgba(255,255,255,0.6)" fontFamily="monospace"
                >
                  {player.name?.split(' ')[0] ?? ''}
                </text>

                {/* Trait label */}
                <AnimatePresence>
                  {traitLabel && (
                    <motion.g
                      initial={{ opacity: 0, y: -2 }}
                      animate={{ opacity: 1, y: -5 }}
                      exit={{ opacity: 0, y: -9 }}
                      transition={{ duration: 0.35 }}
                    >
                      <rect x={-20} y={-26} width={40} height={9} rx={3.5}
                        fill="rgba(8,6,4,0.88)"
                        stroke="#B86A3C" strokeWidth="0.5"
                      />
                      <text x={0} y={-21.2}
                        textAnchor="middle" dominantBaseline="middle"
                        fontSize="2.7" fill="#e8a060"
                        fontFamily="monospace" fontWeight="600"
                      >
                        {traitLabel.length > 17 ? traitLabel.slice(0, 16) + '…' : traitLabel}
                      </text>
                    </motion.g>
                  )}
                </AnimatePresence>
              </motion.g>
            )
          })}

        </svg>
      </div>

      {/* Defensive shape strip */}
      {isDefenseScenario && defensiveShape && (
        <motion.div className={styles.shapeStrip}
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }}
        >
          <div className={styles.shapeItem}>
            <span className={styles.shapeKey}>Block</span>
            <span className={styles.shapeVal}>{defensiveShape.block}</span>
          </div>
          <div className={styles.shapeItem}>
            <span className={styles.shapeKey}>Press</span>
            <span className={styles.shapeVal}>{defensiveShape.press_trigger}</span>
          </div>
          <div className={styles.shapeItem}>
            <span className={styles.shapeKey}>Shape</span>
            <span className={styles.shapeVal}>{defensiveShape.compactness}</span>
          </div>
          {defensiveShape.shape_label && (
            <span className={styles.shapeLabel}>{defensiveShape.shape_label}</span>
          )}
        </motion.div>
      )}

      {/* Linkup pairs */}
      {!isDefenseScenario && linkupPairs.length > 0 && (
        <div className={styles.linkupSection}>
          <p className={styles.sectionTitle}><span className={styles.linkupDot} /> Linkup pairs</p>
          {linkupPairs.map(pair => (
            <div key={pair.id} className={styles.linkupRow}>
              <span className={styles.linkupNames}>
                {pair.player_a.split(' ')[0]} ↔ {pair.player_b.split(' ')[0]}
              </span>
              <span className={styles.linkupDesc}>{pair.description}</span>
            </div>
          ))}
        </div>
      )}

      {/* Highlights legend */}
      {highlights.size > 0 && (
        <div className={styles.legend}>
          {Array.from(highlights.entries()).map(([i, type]) => {
            if (!type || !xi[i]) return null
            const f = xi[i].form_score
            return (
              <div key={i} className={styles.legendItem}>
                <span className={styles.legendDot} style={{
                  background: type === 'inform' ? 'rgba(80,200,120,0.9)' : 'rgba(220,50,50,0.9)',
                  boxShadow: type === 'weak' ? '0 0 6px rgba(220,50,50,0.6)' : '0 0 6px rgba(80,200,120,0.5)',
                }} />
                <span className={styles.legendName}>{xi[i].name?.split(' ')[0]}</span>
                <span className={styles.legendType}>
                  {type === 'inform' ? `↑ In form${f != null ? ` (${(f * 100).toFixed(0)}%)` : ''}` : '⚠ Watch'}
                </span>
              </div>
            )
          })}
        </div>
      )}

      {/* Opposition intel */}
      {isDefenseScenario && opposition && (
        <motion.div className={styles.oppIntel}
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }}
        >
          <p className={styles.sectionTitle}>Opposition intel</p>
          <div className={styles.oppGrid}>
            {[
              { k: 'Press', v: opposition.press_style },
              { k: 'Style', v: opposition.playing_style },
              { k: 'Set pieces', v: opposition.set_piece_threat },
              { k: 'Strength', v: opposition.opponent_strength },
            ].filter(x => x.v).map(({ k, v }) => (
              <div key={k} className={styles.oppItem}>
                <span className={styles.oppKey}>{k}</span>
                <span className={`${styles.oppVal} ${v === 'high' ? styles.threatHigh : ''}`}>{v}</span>
              </div>
            ))}
          </div>
          {opposition.attributes && Object.keys(opposition.attributes).length > 0 && (
            <div className={styles.oppAttributes}>
              {Object.entries(opposition.attributes).slice(0, 4).map(([pos, desc]) => (
                <div key={pos} className={styles.oppAttr}>
                  <span className={styles.oppAttrPos}>{pos.replace(/_/g, ' ')}</span>
                  <span className={styles.oppAttrDesc}>{desc as string}</span>
                </div>
              ))}
            </div>
          )}
          {matchupVulnerabilities.length > 0 && (
            <div className={styles.vulnList}>
              {matchupVulnerabilities.slice(0, 2).map((v, i) => (
                <div key={i} className={styles.vulnItem}>⚠ {v}</div>
              ))}
            </div>
          )}
          {matchupExploits.length > 0 && (
            <div className={styles.exploitList}>
              {matchupExploits.slice(0, 2).map((e, i) => (
                <div key={i} className={styles.exploitItem}>↗ {e}</div>
              ))}
            </div>
          )}
        </motion.div>
      )}

    </div>
  )
}