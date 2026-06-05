'use client'
import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import styles from './FormationPitch.module.css'

// ─── Formation slots — vertical pitch ────────────────────────────────────────
// viewBox 0 0 185 300 — GK bottom (y≈278), FWD top (y≈22)

const FORMATION_SLOTS: Record<string, Record<string, [number, number]>> = {
  '4-3-3': {
    GK:  [92,278], RB:  [152,232], RCB: [115,232], LCB: [70,232],  LB:  [33,232],
    RCM: [140,168], CM: [92,158],  LCM: [44,168],
    RW:  [160,80],  ST: [92,65],   LW:  [25,80],
  },
  '4-4-2': {
    GK:  [92,278], RB:  [152,232], RCB: [115,232], LCB: [70,232],  LB:  [33,232],
    RM:  [160,175], RCM:[115,168], LCM: [70,168],  LM:  [25,175],
    RST: [125,72],  LST:[60,72],
  },
  '4-2-3-1': {
    GK:   [92,278], RB:  [152,232], RCB: [115,232], LCB: [70,232],  LB:  [33,232],
    RCDM: [125,195], LCDM:[60,195],
    RAM:  [155,138], CAM:[92,128],  LAM: [30,138],
    ST:   [92,62],
  },
  '4-1-4-1': {
    GK:  [92,278], RB:  [152,232], RCB: [115,232], LCB: [70,232],  LB:  [33,232],
    CDM: [92,198],
    RM:  [160,155], RCM:[118,148], LCM: [66,148],  LM:  [25,155],
    ST:  [92,62],
  },
  '4-4-1-1': {
    GK:  [92,278], RB:  [152,232], RCB: [115,232], LCB: [70,232],  LB:  [33,232],
    RM:  [160,178], RCM:[115,170], LCM: [70,170],  LM:  [25,178],
    SS:  [92,118],  ST: [92,65],
  },
  '5-4-1': {
    GK:  [92,278], RWB:[168,228], RCB:[130,235], CB:[92,238], LCB:[54,235], LWB:[16,228],
    RM:  [155,168], RCM:[112,162], LCM:[72,162],  LM: [30,168],
    ST:  [92,62],
  },
  '3-5-2': {
    GK:  [92,278], RCB:[138,238], CB: [92,242],  LCB:[46,238],
    RWM: [168,175], RCM:[128,165], CM: [92,158],  LCM:[56,165], LWM:[16,175],
    RST: [125,72],  LST:[60,72],
  },
}

const DEFAULT_SLOTS = FORMATION_SLOTS['4-3-3']

function normaliseFormation(f?: string): string {
  const raw = f
    ?.replace(/[‐‑‒–—]/g, '-')
    .replace(/\s/g, '')
    .trim() ?? ''

  const compactMap: Record<string, string> = {
    '433': '4-3-3',
    '442': '4-4-2',
    '4231': '4-2-3-1',
    '4141': '4-1-4-1',
    '4411': '4-4-1-1',
    '541': '5-4-1',
    '352': '3-5-2',
    '451': '4-5-1',
  }

  return compactMap[raw] ?? raw
}

function getSlots(f?: string): Record<string, [number, number]> {
  return FORMATION_SLOTS[normaliseFormation(f)] ?? DEFAULT_SLOTS
}

// ─── Opposition slots — mirrored (GK top y≈22, FWD bottom y≈238) ─────────────

const OPP_FORMATION_SLOTS: Record<string, Record<string, [number, number]>> = {
  '4-4-2': {
    GK:  [92,22],  RB:  [33,68],   RCB: [70,68],   LCB: [115,68],  LB:  [152,68],
    RM:  [25,125], RCM: [70,132],  LCM: [115,132],  LM:  [160,125],
    RST: [60,228], LST: [125,228],
  },
  '4-3-3': {
    GK:  [92,22],  RB:  [33,68],   RCB: [70,68],   LCB: [115,68],  LB:  [152,68],
    RCM: [44,132], CM:  [92,142],  LCM: [140,132],
    RW:  [25,220], ST:  [92,235],  LW:  [160,220],
  },
  '4-2-3-1': {
    GK:   [92,22],  RB:  [33,68],  RCB: [70,68],   LCB: [115,68],  LB:  [152,68],
    RCDM: [60,105], LCDM:[125,105],
    RAM:  [30,162], CAM: [92,172], LAM: [155,162],
    ST:   [92,238],
  },
  '4-1-4-1': {
    GK:  [92,22],  RB:  [33,68],   RCB: [70,68],   LCB: [115,68],  LB:  [152,68],
    CDM: [92,102],
    RM:  [25,145], RCM: [66,152],  LCM: [118,152],  LM:  [160,145],
    ST:  [92,238],
  },
  '4-4-1-1': {
    GK:  [92,22],  RB:  [33,68],   RCB: [70,68],   LCB: [115,68],  LB:  [152,68],
    RM:  [25,125], RCM: [70,132],  LCM: [115,132],  LM:  [160,125],
    SS:  [92,182], ST:  [92,238],
  },
  '5-4-1': {
    GK:  [92,22],  RWB: [16,72],   RCB: [54,65],   CB:  [92,62],   LCB: [130,65], LWB:[168,72],
    RM:  [30,132], RCM: [72,138],  LCM: [112,138],  LM:  [155,132],
    ST:  [92,238],
  },
  '3-5-2': {
    GK:  [92,22],  RCB: [46,62],   CB:  [92,58],   LCB: [138,62],
    RWM: [16,125], RCM: [56,135],  CM:  [92,142],  LCM: [128,135], LWM:[168,125],
    RST: [60,228], LST: [125,228],
  },
  '4-5-1': {
    GK:  [92,22],  RB:  [33,68],   RCB: [70,68],   LCB: [115,68],  LB:  [152,68],
    RM:  [25,128], RCM: [62,138],  CM:  [92,142],  LCM: [122,138], LM:  [160,128],
    ST:  [92,238],
  },
}

function getOppSlots(f?: string): Record<string, [number, number]> {
  if (!f) return OPP_FORMATION_SLOTS['4-4-2']
  const key = normaliseFormation(f)
  return OPP_FORMATION_SLOTS[key] ?? OPP_FORMATION_SLOTS['4-4-2']
}

function getResolvedOppFormation(f?: string) {
  const key = normaliseFormation(f)
  return OPP_FORMATION_SLOTS[key] ? key : '4-4-2'
}

// ─── Defensive shape ──────────────────────────────────────────────────────────

const DEFENDER_KEYS = new Set(['RB','LB','RCB','LCB','CB','RWB','LWB'])
const FWD_KEYS      = new Set(['RST','LST','ST','CF','SS','RW','LW','RM','LM'])

function getDefensiveSlots(
  formation: string, block: string, defensiveLine: string
): Record<string, [number, number]> {
  const base = getSlots(formation)
  const result: Record<string, [number, number]> = {}

  const fwdPull: Record<string, number>    = { high:18, mid:40, low:70  }
  const midPull: Record<string, number>    = { high:18, mid:38, low:62  }
  const defPull: Record<string, number>    = { high:5,  mid:22, low:45  }
  const lineExtra: Record<string, number>  = { High:-14, Medium:0, Deep:16 }

  const b     = (block ?? 'mid').toLowerCase()
  const extra = lineExtra[defensiveLine] ?? 0

  for (const [key, [x, y]] of Object.entries(base)) {
    if (key === 'GK') { result[key] = [x, y]; continue }
    const isDef = DEFENDER_KEYS.has(key)
    const isFwd = FWD_KEYS.has(key)
    const pull  = isDef ? defPull[b] + extra : isFwd ? fwdPull[b] : midPull[b]
    const xC    = 92.5
    const xComp = xC + (x - xC) * (b === 'low' ? 0.72 : b === 'mid' ? 0.82 : 0.92)
    result[key] = [xComp, Math.min(y + pull, 268)]
  }
  return result
}

// ─── Defensive line y-coordinate ─────────────────────────────────────────────

function getDefLineY(slots: Record<string, [number, number]>): number {
  const defYs = Object.entries(slots)
    .filter(([k]) => DEFENDER_KEYS.has(k))
    .map(([, [, y]]) => y)
  if (!defYs.length) return 232
  return defYs.reduce((a, b) => a + b, 0) / defYs.length
}

// ─── Trait movement map ───────────────────────────────────────────────────────

type MoveCategory =
  | 'hold_position' | 'step_up'      | 'carry_forward'  | 'push_forward'
  | 'overlap_wide'  | 'drop_deep'    | 'drop_to_receive' | 'stay_wide'
  | 'cut_inside'    | 'burst_forward'| 'run_behind'      | 'roam'
  | 'late_run'      | 'push_to_box'  | 'far_post_run'    | 'find_pocket'
  | 'press_high'    | 'push_up'      | 'slight_step_up'  | 'invert_inside'

const TRAIT_TO_MOVE: Record<string, MoveCategory> = {
  // CB
  'Ball Playing Defender':      'step_up',
  'Progressive Passer':         'step_up',
  'Brings Ball Out Of Defence': 'carry_forward',
  'Steps Into Midfield':        'step_up',
  'Calm Under Pressure':        'hold_position',
  'Holds Defensive Line':       'hold_position',
  'Physical Defender':          'hold_position',
  'Aggressive Tackler':         'hold_position',
  'Strong In Air':              'hold_position',
  'Organises Defence':          'hold_position',
  'Clears Danger Early':        'hold_position',
  'Tight Marker':               'hold_position',
  'Fast Recovery Runner':       'hold_position',
  // GK
  'Sweeper Keeper':             'push_up',
  'Comfortable With Feet':      'push_up',
  'Commands Area':              'hold_position',
  // FB / WB
  'Gets Forward Often':         'overlap_wide',
  'Overlaps Winger':            'overlap_wide',
  'Overlap':                    'overlap_wide',
  'Overlapping Fullback':       'overlap_wide',
  'Underlaps Winger':           'invert_inside',
  'Inverted Fullback':          'invert_inside',
  'Inverted Wing Back':         'invert_inside',
  'Inverts Into Midfield':      'invert_inside',
  'Progressive Carrier':        'push_forward',
  'Supports Build-Up':          'slight_step_up',
  'Aggressive Presser':         'press_high',
  'Stays Back At All Times':    'drop_deep',
  'Conservative Defender':      'drop_deep',
  'Marks Tightly':              'hold_position',
  'Plays Short Simple Passes':  'hold_position',
  'Holds Width':                'stay_wide',
  // CDM
  'Deep Playmaker':             'drop_to_receive',
  'Shields Defence':            'hold_position',
  'Dictates Tempo':             'slight_step_up',
  'Recycles Possession':        'drop_to_receive',
  'Breaks Up Play':             'hold_position',
  'Screens Passing Lanes':      'hold_position',
  // CM
  'Box To Box Runner':          'push_forward',
  'Late Runs Into Box':         'late_run',
  'High Workrate':              'push_forward',
  'Counterpresses Aggressively':'press_high',
  'Vertical Runner':            'push_forward',
  'Combination Play Specialist':'slight_step_up',
  'Creative Playmaker':         'find_pocket',
  'Keeps Possession':           'hold_position',
  'Roams From Position':        'roam',
  // CAM
  'Tries Killer Balls Often':   'hold_position',
  'Through Ball Specialist':    'hold_position',
  'Finds Space Between Lines':  'find_pocket',
  'Chance Creator':             'find_pocket',
  'Arrives In Box':             'push_forward',
  'Quick Decision Maker':       'hold_position',
  // Winger
  'Cuts Inside':                'cut_inside',
  'Inverted Winger':            'cut_inside',
  'Shoots Frequently':          'cut_inside',
  'Counterattacking Runner':    'burst_forward',
  'Runs In Behind':             'run_behind',
  'Direct Dribbler':            'stay_wide',
  // ST
  'Target Man Play':            'hold_position',
  'Aerial Threat':              'push_to_box',
  'Holds Up Ball':              'drop_deep',
  'Physical Forward':           'hold_position',
  'Attacks Far Post':           'far_post_run',
  'Presses Defenders Aggressively': 'press_high',
}

// Left-side slot keys — dx sign flips for wide moves
const LEFT_SLOTS  = new Set(['LB','LWB','LCB','LCM','LCDM','LAM','LM','LW','LST','LWM'])
const RIGHT_SLOTS = new Set(['RB','RWB','RCB','RCM','RCDM','RAM','RM','RW','RST','RWM'])

function getMoveDelta(
  category: MoveCategory, slotKey: string, playerId: number
): [number, number] {
  const isLeft  = LEFT_SLOTS.has(slotKey)
  const isRight = RIGHT_SLOTS.has(slotKey)
  const side    = isLeft ? -1 : isRight ? 1 : 0

  switch (category) {
    case 'hold_position':    return [0, 0]
    case 'step_up':          return [0, -12]
    case 'carry_forward':    return [0, -18]
    case 'push_forward':     return [0, -20]
    case 'overlap_wide':     return [side * 20, -15]
    case 'drop_deep':        return [0, 12]
    case 'drop_to_receive':  return [0, 8]
    case 'stay_wide':        return [side * 15, 0]
    case 'cut_inside':       return [-side * 18, -8]
    case 'burst_forward':    return [0, -25]
    case 'run_behind':       return [side * 10, -30]
    case 'late_run':         return [0, -22]
    case 'push_to_box':      return [0, -15]
    case 'far_post_run':     return [side * 20, -12]
    case 'find_pocket':      return [side * 10, -8]
    case 'press_high':       return [0, -20]
    case 'push_up':          return [0, -10]
    case 'slight_step_up':   return [0, -8]
    case 'invert_inside':    return [-side * 20, -8]
    case 'roam': {
      const seed = playerId % 4
      const dx = seed < 2 ? 8 : -8
      const dy = seed % 2 === 0 ? 8 : -8
      return [dx, dy]
    }
    default: return [0, 0]
  }
}

function getPlayerMoveDelta(player: any, slotKey: string): [number, number] {
  const traits: string[] = player?.traits ?? []
  for (const trait of traits) {
    const cat = TRAIT_TO_MOVE[trait] ?? getTraitMoveByText(trait)
    if (cat && cat !== 'hold_position') {
      return getMoveDelta(cat, slotKey, player?.player_id ?? 0)
    }
  }
  return [0, 0]
}

function getTraitMoveByText(trait: string): MoveCategory | null {
  const t = trait.toLowerCase()
  if (t.includes('invert') || t.includes('underlap')) return 'invert_inside'
  if (t.includes('overlap')) return 'overlap_wide'
  if (t.includes('cut') && t.includes('inside')) return 'cut_inside'
  if (t.includes('behind')) return 'run_behind'
  if (t.includes('drop')) return 'drop_to_receive'
  if (t.includes('late run') || t.includes('box to box')) return 'late_run'
  if (t.includes('wide')) return 'stay_wide'
  if (t.includes('press')) return 'press_high'
  if (t.includes('roam')) return 'roam'
  return null
}

// ─── Possession sequence ──────────────────────────────────────────────────────

interface PassEvent {
  fromSlot: string; toSlot: string
  fromX: number; fromY: number; toX: number; toY: number
}

// Fallback sequences by playing style when no linkup pairs
const STYLE_SEQUENCES: Record<string, string[][]> = {
  direct:     [['GK','RCB'],['RCB','ST'],['ST','RCB']],
  possession: [['GK','LCDM'],['LCDM','CM'],['CM','CAM'],['CAM','LCDM']],
  counter:    [['GK','RCB'],['RCB','RW'],['RW','ST']],
  pressing:   [['GK','CDM'],['CDM','RCM'],['RCM','ST']],
  hybrid:     [['GK','RCDM'],['RCDM','CAM'],['CAM','ST']],
  default:    [['GK','CM'],['CM','ST'],['ST','CM']],
}

function firstExistingSlot(slots: Record<string, [number, number]>, keys: string[]) {
  return keys.find(k => slots[k])
}

function pushPass(
  events: PassEvent[],
  slots: Record<string, [number, number]>,
  fromKey?: string,
  toKey?: string
) {
  if (!fromKey || !toKey || fromKey === toKey) return
  const posA = slots[fromKey]
  const posB = slots[toKey]
  if (!posA || !posB) return
  if (events.some(e => e.fromSlot === fromKey && e.toSlot === toKey)) return
  events.push({
    fromSlot: fromKey, toSlot: toKey,
    fromX: posA[0], fromY: posA[1],
    toX: posB[0], toY: posB[1],
  })
}

function buildPossessionSequence(
  xi: any[],
  linkupPairs: { id: string; player_a: string; player_b: string }[],
  attackSlots: Record<string, [number, number]>,
  squadStyle: string
): PassEvent[] {
  const nameToSlot = new Map<string, string>()
  for (const p of xi) {
    const key = p.slot_key ?? p.specific_position
    if (key) nameToSlot.set(p.name, key)
  }

  const events: PassEvent[] = []

  if (linkupPairs?.length > 0) {
    // Always start from GK → deepest mid
    const deepMid = ['CDM','RCDM','LCDM','CM','RCM','LCM']
      .find(k => attackSlots[k]) ?? 'CM'
    const ballSideDef = firstExistingSlot(attackSlots, ['RCB','LCB','CB','RB','LB'])
    pushPass(events, attackSlots, 'GK', ballSideDef)
    pushPass(events, attackSlots, ballSideDef, deepMid)
    // Follow linkup pairs
    for (const pair of linkupPairs) {
      const slotA = nameToSlot.get(pair.player_a)
      const slotB = nameToSlot.get(pair.player_b)
      pushPass(events, attackSlots, slotA, slotB)
    }
    const creator = firstExistingSlot(attackSlots, ['CAM','RCM','LCM','CM','RAM','LAM'])
    const wideOutlet = firstExistingSlot(attackSlots, ['RW','LW','RM','LM','RWM','LWM'])
    const striker = firstExistingSlot(attackSlots, ['ST','RST','LST','CF','SS'])
    pushPass(events, attackSlots, deepMid, creator)
    pushPass(events, attackSlots, creator, wideOutlet)
    pushPass(events, attackSlots, wideOutlet, striker)
  } else {
    // Fallback: style-based sequence
    const style = (squadStyle ?? 'default').toLowerCase()
    const seq   = STYLE_SEQUENCES[style] ?? STYLE_SEQUENCES.default
    for (const [fromKey, toKey] of seq) {
      const posA = attackSlots[fromKey]
      const posB = attackSlots[toKey]
      if (!posA || !posB) continue
      events.push({
        fromSlot: fromKey, toSlot: toKey,
        fromX: posA[0], fromY: posA[1],
        toX: posB[0], toY: posB[1],
      })
    }
  }

  return events
}

// ─── Insights ─────────────────────────────────────────────────────────────────

type InsightType = 'inform' | 'formdip' | 'weaklink'

const INSIGHT_COLORS: Record<InsightType, { ring: string; glow: string }> = {
  inform:   { ring: '#5A8A6A', glow: 'rgba(90,138,106,0.28)'  },
  formdip:  { ring: '#C8612A', glow: 'rgba(200,97,42,0.28)'   },
  weaklink: { ring: '#B86A3C', glow: 'rgba(184,106,60,0.28)'  },
}

interface Insight { type: InsightType; label: string }

function computeInsights(xi: any[]): Map<string, Insight> {
  const map = new Map<string, Insight>()
  if (!xi?.length) return map
  const players = xi.filter(p => (p.slot_key ?? p.specific_position) && p.broad_position !== 'GK')
  const avgOverall = players.reduce((s, p) => s + (p.attributes?.overall_rating ?? 0), 0) / Math.max(1, players.length)
  const avgRole = players.reduce((s, p) => s + (p.attributes?.role_rating ?? 0), 0) / Math.max(1, players.length)
  const withForm = players.filter(p => p.form_score != null)
  const avgForm = withForm.length
    ? withForm.reduce((s, p) => s + p.form_score, 0) / withForm.length : 0.5

  const scored = players.map(p => {
    const key  = p.slot_key ?? p.specific_position ?? ''
    const overall = p.attributes?.overall_rating ?? avgOverall
    const role = p.attributes?.role_rating ?? avgRole
    const form = p.form_score ?? avgForm
    const score = (overall - avgOverall) + (role - avgRole) * 0.8 + (form - avgForm) * 8
    return { key, score, form, role }
  })

  scored
    .filter(p => p.score > 1.2 || p.form > avgForm + 0.18)
    .sort((a, b) => b.score - a.score)
    .slice(0, 2)
    .forEach(p => map.set(p.key, { type: 'inform', label: 'Strong' }))

  scored
    .filter(p => p.score < -1.2 || p.form < avgForm - 0.18 || p.role < avgRole - 2)
    .sort((a, b) => a.score - b.score)
    .slice(0, 2)
    .forEach(p => {
      if (!map.has(p.key)) map.set(p.key, { type: p.role < avgRole - 2 ? 'weaklink' : 'formdip', label: 'Concern' })
    })

  return map
}

// ─── Pitch markings ───────────────────────────────────────────────────────────

function PitchMarkings() {
  return (
    <g>
      <rect x="4" y="4" width="177" height="292" rx="2"
        fill="none" stroke="rgba(255,255,255,0.13)" strokeWidth="0.6"/>
      <line x1="4" y1="150" x2="181" y2="150"
        stroke="rgba(255,255,255,0.10)" strokeWidth="0.6"/>
      <circle cx="92.5" cy="150" r="18"
        fill="none" stroke="rgba(255,255,255,0.09)" strokeWidth="0.6"/>
      <circle cx="92.5" cy="150" r="1.2" fill="rgba(255,255,255,0.18)"/>
      <rect x="42" y="258" width="101" height="38"
        fill="none" stroke="rgba(255,255,255,0.09)" strokeWidth="0.6"/>
      <rect x="62" y="278" width="61" height="18"
        fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="0.6"/>
      <rect x="42" y="4" width="101" height="38"
        fill="none" stroke="rgba(255,255,255,0.09)" strokeWidth="0.6"/>
      <rect x="62" y="4" width="61" height="18"
        fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="0.6"/>
      <rect x="72" y="0"   width="41" height="5"
        fill="none" stroke="rgba(255,255,255,0.22)" strokeWidth="1"/>
      <rect x="72" y="295" width="41" height="5"
        fill="none" stroke="rgba(255,255,255,0.22)" strokeWidth="1"/>
    </g>
  )
}

// ─── Player node ─────────────────────────────────────────────────────────────

interface NodeProps {
  x: number; y: number; label: string
  insight?: Insight; dim?: boolean; isGK?: boolean
  isPossession?: boolean; isDefensive?: boolean
  hasBall?: boolean
}

function Node({ x, y, label, insight, dim, isGK, isPossession, isDefensive, hasBall }: NodeProps) {
  const r  = isGK ? 8 : 9
  const ic = insight ? INSIGHT_COLORS[insight.type] : null
  const fill = hasBall   ? '#B86A3C'
    : isPossession       ? '#1a4a5a'
    : isDefensive        ? '#2a1a1a'
    : isGK               ? '#1e3a5f'
    : '#1a3a6b'
  const strokeColor = hasBall ? '#f6c90e'
    : ic             ? ic.ring
    : isPossession   ? 'rgba(90,200,200,0.45)'
    : isDefensive    ? 'rgba(200,90,90,0.45)'
    : 'rgba(255,255,255,0.22)'

  return (
    <motion.g
      animate={{ x, y, opacity: dim ? 0.22 : 1 }}
      transition={{ type: 'spring', stiffness: 75, damping: 15 }}
    >
      {ic && (
        <motion.circle cx={0} cy={0} r={r + 5} fill={ic.glow}
          animate={{ opacity: [0.9, 0.3, 0.9], scale: [1, 1.2, 1] }}
          transition={{ repeat: Infinity, duration: 2.4 }}
        />
      )}
      {hasBall && (
        <motion.circle cx={0} cy={0} r={r + 4}
          fill="none" stroke="rgba(246,201,14,0.4)" strokeWidth="1"
          animate={{ scale: [1, 1.3, 1], opacity: [0.8, 0.2, 0.8] }}
          transition={{ repeat: Infinity, duration: 1.2 }}
        />
      )}
      <circle cx={0} cy={0} r={r}
        fill={fill} stroke={strokeColor}
        strokeWidth={ic || hasBall ? 1.5 : 0.8}
      />
      <text x={0} y={0} textAnchor="middle" dominantBaseline="central"
        fontSize={label.length > 2 ? '4.8' : '5.5'}
        fontFamily="'Barlow Condensed', sans-serif"
        fontWeight="700" fill="white" letterSpacing="0.3">
        {label}
      </text>
    </motion.g>
  )
}

function OppNode({ x, y, label }: { x: number; y: number; label: string }) {
  return (
    <motion.g
      initial={{ opacity: 0, scale: 0.4 }}
      animate={{ x, y, opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.4 }}
      transition={{ type: 'spring', stiffness: 85, damping: 15 }}
    >
      <circle cx={0} cy={0} r={8}
        fill="rgba(180,50,50,0.12)"
        stroke="rgba(200,97,42,0.55)"
        strokeWidth="1" strokeDasharray="3 2"/>
      <text x={0} y={0} textAnchor="middle" dominantBaseline="central"
        fontSize="4.5" fontFamily="'Barlow Condensed', sans-serif"
        fontWeight="600" fill="rgba(200,97,42,0.85)" letterSpacing="0.3">
        {label}
      </text>
    </motion.g>
  )
}

// ─── Ball ─────────────────────────────────────────────────────────────────────

function Ball({ x, y }: { x: number; y: number }) {
  return (
    <motion.g animate={{ x, y }} transition={{ type: 'spring', stiffness: 120, damping: 18 }}>
      <circle cx={0} cy={0} r={3.5} fill="#f6c90e"/>
      <motion.circle cx={0} cy={0} r={3.5}
        fill="none" stroke="rgba(246,201,14,0.5)" strokeWidth="1.5"
        animate={{ scale: [1, 2, 1], opacity: [0.7, 0, 0.7] }}
        transition={{ repeat: Infinity, duration: 1.0 }}
      />
    </motion.g>
  )
}

function MovementIntent({ from, to }: { from: [number, number]; to: [number, number] }) {
  const [x1, y1] = from
  const [x2, y2] = to
  if (Math.abs(x1 - x2) + Math.abs(y1 - y2) < 5) return null

  return (
    <motion.line
      x1={x1} y1={y1} x2={x2} y2={y2}
      stroke="rgba(246,201,14,0.38)"
      strokeWidth="0.8"
      strokeDasharray="3 3"
      strokeLinecap="round"
      markerEnd="url(#intentArrow)"
      initial={{ pathLength: 0, opacity: 0 }}
      animate={{ pathLength: 1, opacity: [0.25, 0.75, 0.25] }}
      transition={{ duration: 1.8, repeat: Infinity, ease: 'easeInOut' }}
    />
  )
}

const PRESS_LINE_KEYS: Record<string, string[]> = {
  '4-4-2': ['LM','LST','RST','RM'],
  '4-3-3': ['LW','ST','RW'],
  '4-2-3-1': ['LAM','CAM','RAM','ST'],
  '4-1-4-1': ['LM','LCM','RCM','RM'],
  '4-4-1-1': ['LM','SS','ST','RM'],
  '5-4-1': ['LM','LCM','RCM','RM'],
  '3-5-2': ['LWM','LST','RST','RWM'],
}

function getPressLinePoints(formation: string, slots: Record<string, [number, number]>) {
  const keys = PRESS_LINE_KEYS[normaliseFormation(formation)] ?? []
  const keyedPoints = keys
    .map(key => slots[key] ? { key, point: slots[key] } : null)
    .filter((p): p is { key: string; point: [number, number] } => Boolean(p))

  if (keyedPoints.length >= 2) return keyedPoints.map(p => p.point)

  return Object.entries(slots)
    .filter(([key]) => key !== 'GK' && !DEFENDER_KEYS.has(key))
    .sort((a, b) => a[1][1] - b[1][1])
    .slice(0, 4)
    .sort((a, b) => a[1][0] - b[1][0])
    .map(([, point]) => point)
}

function compactnessLevel(raw?: string) {
  const v = raw?.toLowerCase() ?? 'medium'
  if (v.includes('high') || v.includes('tight') || v.includes('compact')) return 'High'
  if (v.includes('low') || v.includes('loose') || v.includes('wide')) return 'Low'
  return 'Medium'
}

function PressCoverLine({
  points,
  pressIntensity,
  compactness,
}: {
  points: [number, number][]
  pressIntensity: string
  compactness?: string
}) {
  if (points.length < 2) return null

  const compact = compactnessLevel(compactness)
  const intensity = pressIntensity || 'Medium'
  const color = intensity === 'High' ? '#C8612A' : intensity === 'Low' ? '#5A8A6A' : '#B86A3C'
  const path = points.map(([x, y], i) => `${i === 0 ? 'M' : 'L'} ${x} ${y}`).join(' ')
  const labelPoint = points[Math.floor(points.length / 2)]
  const arrowLength = intensity === 'High' ? 16 : intensity === 'Low' ? 6 : 10

  return (
    <motion.g initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.45 }}>
      <motion.path
        d={path}
        fill="none"
        stroke={color}
        strokeWidth={compact === 'High' ? 1.6 : compact === 'Low' ? 0.8 : 1.2}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray={compact === 'Low' ? '5 4' : '2 2'}
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 0.9 }}
      />
      {points.map(([x, y], i) => (
        <motion.line
          key={`${x}-${y}-${i}`}
          x1={x} y1={y - 2}
          x2={x} y2={y - arrowLength}
          stroke={color}
          strokeWidth="0.7"
          markerEnd="url(#pressArrow)"
          initial={{ opacity: 0.2, pathLength: 0 }}
          animate={{ opacity: [0.25, 0.8, 0.25], pathLength: 1 }}
          transition={{ duration: 1.4, repeat: Infinity, delay: i * 0.12 }}
        />
      ))}
      <rect x={labelPoint[0] - 37} y={labelPoint[1] + 8} width="74" height="20"
        rx="3" fill="rgba(0,0,0,0.52)"/>
      <text x={labelPoint[0]} y={labelPoint[1] + 15}
        textAnchor="middle" dominantBaseline="central"
        fontSize="4.8" fontFamily="'JetBrains Mono', monospace"
        fontWeight="600" fill={color} letterSpacing="0.3">
        {intensity.toUpperCase()} PRESS
      </text>
      <text x={labelPoint[0]} y={labelPoint[1] + 22}
        textAnchor="middle" dominantBaseline="central"
        fontSize="4.2" fontFamily="'JetBrains Mono', monospace"
        fontWeight="500" fill="rgba(255,255,255,0.72)" letterSpacing="0.2">
        {compact.toUpperCase()} COMPACT
      </text>
    </motion.g>
  )
}

// ─── Props ────────────────────────────────────────────────────────────────────

export type PitchState = 'xi' | 'opposition' | 'possession' | 'defensive'

export interface FormationPitchProps {
  pitchState: PitchState
  formation: string
  defensiveFormation?: string
  xi: any[]
  defensiveShape?: { block: string; compactness: string; press_trigger: string; transition: string; shape_label: string }
  defensiveLine?: string
  pressIntensity?: string
  linkupPairs?: { id: string; player_a: string; player_b: string; description: string }[]
  oppFormation?: string
  squadStyle?: string
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function FormationPitch({
  pitchState, formation, defensiveFormation,
  xi = [], defensiveShape, defensiveLine = 'Medium', pressIntensity = 'Medium',
  linkupPairs = [], oppFormation, squadStyle = 'default',
}: FormationPitchProps) {

  const slotToPlayer = new Map<string, any>()
  for (const p of xi) {
    const key = p.slot_key ?? p.specific_position ?? null
    if (key) slotToPlayer.set(key, p)
  }

  const attackSlots = getSlots(formation)
  const slotKeys    = Object.keys(attackSlots)

  // ── Possession animation state ──────────────────────────────────────────────

  const [passIdx, setPassIdx]           = useState(0)
  const [ballPos, setBallPos]           = useState<[number,number]>([92, 278])
  const [ballCarrierSlot, setBallCarrierSlot] = useState<string>('GK')
  const [showPassLine, setShowPassLine] = useState(false)
  const [passLine, setPassLine]         = useState<[number,number,number,number] | null>(null)
  const sequence = buildPossessionSequence(xi, linkupPairs, attackSlots, squadStyle)

  // Run possession loop
  useEffect(() => {
    if (pitchState !== 'possession' || sequence.length === 0) {
      // Reset when leaving possession
      setBallPos([92, 278])
      setBallCarrierSlot('GK')
      setShowPassLine(false)
      return
    }

    const event = sequence[passIdx % sequence.length]
    // Show pass line
    setPassLine([event.fromX, event.fromY, event.toX, event.toY])
    setShowPassLine(true)
    setBallCarrierSlot(event.fromSlot)

    // After 600ms ball travels
    const t1 = setTimeout(() => {
      setBallPos([event.toX, event.toY])
      setBallCarrierSlot(event.toSlot)
    }, 600)

    // After 1800ms hide line and advance
    const t2 = setTimeout(() => {
      setShowPassLine(false)
      setPassIdx(i => (i + 1) % sequence.length)
    }, 1800)

    return () => { clearTimeout(t1); clearTimeout(t2) }
  }, [pitchState, passIdx, sequence.length])

  // Reset passIdx when entering possession
  useEffect(() => {
    if (pitchState === 'possession') {
      setPassIdx(0)
      const gkPos = attackSlots['GK']
      if (gkPos) setBallPos([gkPos[0], gkPos[1]])
      setBallCarrierSlot('GK')
    }
  }, [pitchState])

  // ── Position resolution ─────────────────────────────────────────────────────

  function getPositions(): Record<string, [number, number]> {
    if (pitchState === 'defensive') {
      const block = defensiveShape?.block ?? 'mid'
      return getDefensiveSlots(defensiveFormation ?? formation, block, defensiveLine)
    }
    return attackSlots
  }

  const activePositions = getPositions()
  const insights        = computeInsights(xi)
  const defensiveFormationKey = defensiveFormation ?? formation
  const pressLinePoints = pitchState === 'defensive'
    ? getPressLinePoints(defensiveFormationKey, activePositions)
    : []

  // Possession offsets — applied to non-ball-carrier players
  function getPossessionPos(slotKey: string, baseX: number, baseY: number): [number, number] {
    if (pitchState !== 'possession') return [baseX, baseY]
    if (slotKey === ballCarrierSlot)  return [baseX, baseY]
    const player = slotToPlayer.get(slotKey)
    const [dx, dy] = getPlayerMoveDelta(player, slotKey)
    return [baseX + dx, baseY + dy]
  }

  // ── Defensive line ──────────────────────────────────────────────────────────

  const defLineY = pitchState === 'defensive' ? getDefLineY(activePositions) : null

  const defLineColors: Record<string, string> = {
    High: '#C8612A', Medium: '#B86A3C', Deep: '#5A8A6A'
  }
  const defLineLabels: Record<string, string> = {
    High: 'HIGH LINE', Medium: 'MED LINE', Deep: 'DEEP LINE'
  }
  const defLineColor = defLineColors[defensiveLine] ?? '#B86A3C'
  const defLineLabel = defLineLabels[defensiveLine] ?? 'MED LINE'

  // ── Opposition ─────────────────────────────────────────────────────────────

  const resolvedOppFormation = getResolvedOppFormation(oppFormation)
  const oppSlots  = getOppSlots(oppFormation)
  const showOpp   = pitchState === 'opposition'

  // ── State label ─────────────────────────────────────────────────────────────

  const stateLabels: Record<PitchState, string> = {
    xi:          normaliseFormation(formation),
    opposition:  oppFormation ? `vs ${resolvedOppFormation}` : 'Opposition estimate',
    possession:  'In Possession',
    defensive:   defensiveShape?.shape_label ?? 'Defensive Shape',
  }

  return (
    <div className={styles.wrap}>
      <div className={styles.stateLabel}>{stateLabels[pitchState]}</div>
      <div className={styles.pitchContainer}>
        <svg viewBox="0 0 185 300" className={styles.pitch}
          preserveAspectRatio="xMidYMid meet">
          <defs>
            <linearGradient id="vg" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%"   stopColor="#1a4731"/>
              <stop offset="50%"  stopColor="#1e5236"/>
              <stop offset="100%" stopColor="#1a4731"/>
            </linearGradient>
            <pattern id="vsp" x="0" y="0" width="185" height="30"
              patternUnits="userSpaceOnUse">
              <rect x="0" y="0" width="185" height="15" fill="rgba(0,0,0,0.03)"/>
            </pattern>
            <marker id="intentArrow" markerWidth="5" markerHeight="5" refX="4" refY="2.5"
              orient="auto" markerUnits="strokeWidth">
              <path d="M0,0 L5,2.5 L0,5 Z" fill="rgba(246,201,14,0.55)" />
            </marker>
            <marker id="pressArrow" markerWidth="5" markerHeight="5" refX="4" refY="2.5"
              orient="auto" markerUnits="strokeWidth">
              <path d="M0,0 L5,2.5 L0,5 Z" fill="#B86A3C" />
            </marker>
          </defs>
          <rect width="185" height="300" fill="url(#vg)"/>
          <rect width="185" height="300" fill="url(#vsp)"/>
          <PitchMarkings/>

          {/* Defensive line */}
          {pitchState === 'defensive' && defLineY != null && (
            <motion.g
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5 }}
            >
              <motion.line
                x1="6" y1={defLineY} x2="179" y2={defLineY}
                stroke={defLineColor} strokeWidth="0.8"
                strokeDasharray="4 3"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 0.8 }}
              />
              <rect x="120" y={defLineY - 7} width="54" height="11"
                rx="2" fill="rgba(0,0,0,0.55)"/>
              <text x="147" y={defLineY + 0.5}
                textAnchor="middle" dominantBaseline="central"
                fontSize="5" fontFamily="'JetBrains Mono', monospace"
                fontWeight="500" fill={defLineColor} letterSpacing="0.3">
                {defLineLabel}
              </text>
            </motion.g>
          )}

          {pitchState === 'defensive' && (
            <PressCoverLine
              points={pressLinePoints}
              pressIntensity={pressIntensity}
              compactness={defensiveShape?.compactness}
            />
          )}

          {/* Pass line */}
          <AnimatePresence>
            {pitchState === 'possession' && showPassLine && passLine && (
              <motion.line
                key={`pass-${passIdx}`}
                x1={passLine[0]} y1={passLine[1]}
                x2={passLine[2]} y2={passLine[3]}
                stroke="rgba(246,201,14,0.7)" strokeWidth="1"
                strokeDasharray="4 3" strokeLinecap="round"
                initial={{ pathLength: 0, opacity: 0.9 }}
                animate={{ pathLength: 1, opacity: 0.9 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.5 }}
              />
            )}
          </AnimatePresence>

          {pitchState === 'possession' && slotKeys.map(key => {
            const player = slotToPlayer.get(key)
            if (!player || key === ballCarrierSlot) return null
            const base = attackSlots[key]
            if (!base) return null
            const [dx, dy] = getPlayerMoveDelta(player, key)
            const target: [number, number] = [base[0] + dx, base[1] + dy]
            return <MovementIntent key={`intent-${key}`} from={base} to={target} />
          })}

          {/* Opposition nodes */}
          <AnimatePresence>
            {showOpp && Object.entries(oppSlots).map(([key, [x, y]]) => {
              const label = key.replace(/^[RL](?=[A-Z])/, '').slice(0, 3).toUpperCase()
              return <OppNode key={`opp-${key}`} x={x} y={y} label={label}/>
            })}
          </AnimatePresence>

          {/* Your players */}
          {slotKeys.map(key => {
            const [bx, by]  = activePositions[key] ?? attackSlots[key]
            const [px, py]  = getPossessionPos(key, bx, by)
            const player    = slotToPlayer.get(key)
            const name      = player?.name ?? key
            const initials  = name.split(' ').map((w: string) => w[0]).join('').toUpperCase().slice(0, 3)
            const insight   = insights.get(key)
            const hasBall   = pitchState === 'possession' && key === ballCarrierSlot

            return (
              <Node key={key} x={px} y={py}
                label={initials}
                insight={insight}
                dim={showOpp}
                isGK={key === 'GK'}
                isPossession={pitchState === 'possession'}
                isDefensive={pitchState === 'defensive'}
                hasBall={hasBall}
              />
            )
          })}

          {/* Ball */}
          {pitchState === 'possession' && (
            <Ball x={ballPos[0]} y={ballPos[1]}/>
          )}
        </svg>
      </div>

      {/* Legend */}
      {(pitchState === 'xi' || pitchState === 'possession') && insights.size > 0 && (
        <div className={styles.legend}>
          {Array.from(insights.entries()).map(([key, insight]) => {
            const player = slotToPlayer.get(key)
            const ic     = INSIGHT_COLORS[insight.type]
            return (
              <div key={key} className={styles.legendItem}>
                <span className={styles.legendDot} style={{ background: ic.ring }}/>
                <span className={styles.legendName}>{player?.name ?? key}</span>
                <span className={styles.legendTag}
                  style={{ color: ic.ring, borderColor: `${ic.ring}55` }}>
                  {insight.label}
                </span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
