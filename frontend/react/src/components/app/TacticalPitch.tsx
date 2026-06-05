'use client'

import { useRef, useMemo, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

// ─── Constants ────────────────────────────────────────────────────────────────

const VW = 220
const VH = 130
const R = 3.8
const R_CARRIER = 7

const lerp = (a: number, b: number, t: number) => a + (b - a) * t
const clamp = (x: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, x))
const dist = (a: {x:number;y:number}, b: {x:number;y:number}) =>
  Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)

// ─── Formation slots ──────────────────────────────────────────────────────────

const FORMATION_SLOTS: Record<string, {x:number;y:number;role:string;slot_key:string}[]> = {
  '4-3-3': [
    {x:14,y:65,role:'GK',slot_key:'GK'},
    {x:52,y:20,role:'DEF',slot_key:'RB'},{x:52,y:45,role:'DEF',slot_key:'RCB'},
    {x:52,y:85,role:'DEF',slot_key:'LCB'},{x:52,y:110,role:'DEF',slot_key:'LB'},
    {x:100,y:32,role:'MID',slot_key:'RCM'},{x:100,y:65,role:'MID',slot_key:'CM'},{x:100,y:98,role:'MID',slot_key:'LCM'},
    {x:175,y:20,role:'FWD',slot_key:'RW'},{x:175,y:65,role:'FWD',slot_key:'ST'},{x:175,y:110,role:'FWD',slot_key:'LW'},
  ],
  '4-4-2': [
    {x:14,y:65,role:'GK',slot_key:'GK'},
    {x:52,y:20,role:'DEF',slot_key:'RB'},{x:52,y:48,role:'DEF',slot_key:'RCB'},
    {x:52,y:82,role:'DEF',slot_key:'LCB'},{x:52,y:110,role:'DEF',slot_key:'LB'},
    {x:108,y:20,role:'MID',slot_key:'RM'},{x:108,y:48,role:'MID',slot_key:'RCM'},
    {x:108,y:82,role:'MID',slot_key:'LCM'},{x:108,y:110,role:'MID',slot_key:'LM'},
    {x:178,y:42,role:'FWD',slot_key:'RST'},{x:178,y:88,role:'FWD',slot_key:'LST'},
  ],
  '4-2-3-1': [
    {x:14,y:65,role:'GK',slot_key:'GK'},
    {x:52,y:20,role:'DEF',slot_key:'RB'},{x:52,y:48,role:'DEF',slot_key:'RCB'},
    {x:52,y:82,role:'DEF',slot_key:'LCB'},{x:52,y:110,role:'DEF',slot_key:'LB'},
    {x:92,y:44,role:'MID',slot_key:'RDM'},{x:92,y:86,role:'MID',slot_key:'LDM'},
    {x:138,y:20,role:'MID',slot_key:'RAM'},{x:138,y:65,role:'MID',slot_key:'CAM'},{x:138,y:110,role:'MID',slot_key:'LAM'},
    {x:190,y:65,role:'FWD',slot_key:'ST'},
  ],
  '4-4-1-1': [
    {x:14,y:65,role:'GK',slot_key:'GK'},
    {x:52,y:20,role:'DEF',slot_key:'RB'},{x:52,y:48,role:'DEF',slot_key:'RCB'},
    {x:52,y:82,role:'DEF',slot_key:'LCB'},{x:52,y:110,role:'DEF',slot_key:'LB'},
    {x:108,y:20,role:'MID',slot_key:'RM'},{x:108,y:48,role:'MID',slot_key:'RCM'},
    {x:108,y:82,role:'MID',slot_key:'LCM'},{x:108,y:110,role:'MID',slot_key:'LM'},
    {x:158,y:65,role:'FWD',slot_key:'SS'},{x:190,y:65,role:'FWD',slot_key:'ST'},
  ],
  '4-1-4-1': [
    {x:14,y:65,role:'GK',slot_key:'GK'},
    {x:52,y:20,role:'DEF',slot_key:'RB'},{x:52,y:48,role:'DEF',slot_key:'RCB'},
    {x:52,y:82,role:'DEF',slot_key:'LCB'},{x:52,y:110,role:'DEF',slot_key:'LB'},
    {x:88,y:65,role:'MID',slot_key:'CDM'},
    {x:130,y:15,role:'MID',slot_key:'RM'},{x:130,y:45,role:'MID',slot_key:'RCM'},
    {x:130,y:85,role:'MID',slot_key:'LCM'},{x:130,y:115,role:'MID',slot_key:'LM'},
    {x:190,y:65,role:'FWD',slot_key:'ST'},
  ],
  '5-4-1': [
    {x:14,y:65,role:'GK',slot_key:'GK'},
    {x:52,y:12,role:'DEF',slot_key:'RWB'},{x:52,y:36,role:'DEF',slot_key:'RCB'},
    {x:52,y:65,role:'DEF',slot_key:'CB'},{x:52,y:94,role:'DEF',slot_key:'LCB'},{x:52,y:118,role:'DEF',slot_key:'LWB'},
    {x:110,y:24,role:'MID',slot_key:'RM'},{x:110,y:52,role:'MID',slot_key:'RCM'},
    {x:110,y:78,role:'MID',slot_key:'LCM'},{x:110,y:106,role:'MID',slot_key:'LM'},
    {x:190,y:65,role:'FWD',slot_key:'ST'},
  ],
  '4-5-1': [
    {x:14,y:65,role:'GK',slot_key:'GK'},
    {x:52,y:20,role:'DEF',slot_key:'RB'},{x:52,y:48,role:'DEF',slot_key:'RCB'},
    {x:52,y:82,role:'DEF',slot_key:'LCB'},{x:52,y:110,role:'DEF',slot_key:'LB'},
    {x:108,y:12,role:'MID',slot_key:'RM'},{x:108,y:36,role:'MID',slot_key:'RCM'},{x:108,y:65,role:'MID',slot_key:'CM'},
    {x:108,y:94,role:'MID',slot_key:'LCM'},{x:108,y:118,role:'MID',slot_key:'LM'},
    {x:190,y:65,role:'FWD',slot_key:'ST'},
  ],
  '3-5-2': [
    {x:14,y:65,role:'GK',slot_key:'GK'},
    {x:52,y:32,role:'DEF',slot_key:'RCB'},{x:52,y:65,role:'DEF',slot_key:'CB'},{x:52,y:98,role:'DEF',slot_key:'LCB'},
    {x:100,y:12,role:'MID',slot_key:'RWB'},{x:100,y:38,role:'MID',slot_key:'RCM'},{x:100,y:65,role:'MID',slot_key:'CM'},
    {x:100,y:92,role:'MID',slot_key:'LCM'},{x:100,y:118,role:'MID',slot_key:'LWB'},
    {x:178,y:42,role:'FWD',slot_key:'RST'},{x:178,y:88,role:'FWD',slot_key:'LST'},
  ],
}

function mirrorFormation(slots: {x:number;y:number;role:string;slot_key:string}[]) {
  return slots.map(s => ({
    ...s,
    x: VW - s.x,
    slot_key: 'Opp ' + s.slot_key,
  }))
}

const ZONE_RECTS: Record<string, {x:number;y:number;w:number;h:number}> = {
  defensive_third:  {x:0,   y:0,  w:73,  h:130},
  midfield_third:   {x:73,  y:0,  w:74,  h:130},
  attacking_third:  {x:147, y:0,  w:73,  h:130},
  left_channel:     {x:0,   y:0,  w:220, h:45 },
  right_channel:    {x:0,   y:85, w:220, h:45 },
  central_channel:  {x:0,   y:45, w:220, h:40 },
  left_box:         {x:147, y:0,  w:63,  h:50 },
  right_box:        {x:147, y:80, w:63,  h:50 },
  central_box:      {x:147, y:45, w:63,  h:40 },
  left_flank:       {x:0,   y:0,  w:110, h:45 },
  right_flank:      {x:0,   y:85, w:110, h:45 },
}

const SEVERITY_COLOR: Record<string, string> = {
  opportunity: '#5A8A6A',
  danger:      '#C8612A',
  neutral:     '#8C7A63',
}

// ─── Ambient movement ─────────────────────────────────────────────────────────

function getAmbientDelta(
  slot: {x:number;y:number;role:string;slot_key:string},
  ball: {x:number;y:number},
  scenario: string,
  playerTraits: string[],
  traitLabel?: string,
): {dx:number; dy:number} {
  const isDefense = scenario === 'defensive_shape' || scenario === 'opponent_threat'
  const ballSideY = ball.y < VH * 0.4 ? -1 : ball.y > VH * 0.6 ? 1 : 0
  const ballAdvance = (ball.x - 100) / 100

  const xDist = Math.abs(slot.x - ball.x)
  const reactivity = Math.max(0, 1 - xDist / 120)

  // ── "Short option" trait: player drops deeper toward ball ──
  // If this player has been labelled as a short option, they should drop
  // toward the ball carrier rather than push forward
  const isShortOption = traitLabel?.toLowerCase().includes('short option') ||
    playerTraits.some(t => t.toLowerCase().includes('short option') || t.toLowerCase().includes('drops deep'))

  if (isShortOption) {
    // Drop 10–16 units back toward ball and tighten toward ball's y
    return {
      dx: clamp((ball.x - slot.x) * 0.55, -18, 0),
      dy: (ball.y - slot.y) * 0.35,
    }
  }

  if (isDefense) {
    const dropFactor = slot.role === 'GK' ? 0 : slot.role === 'DEF' ? 0.05 : slot.role === 'MID' ? 0.12 : 0.18
    return {
      dx: -(ball.x - slot.x) * dropFactor,
      dy: (ball.y - slot.y) * 0.08 * reactivity,
    }
  }

  switch (slot.role) {
    case 'GK':
      return { dx: ballAdvance > 0.3 ? 6 : 0, dy: (ball.y - slot.y) * 0.04 }

    case 'DEF': {
      const isCB = slot.slot_key.includes('CB')
      if (isCB) {
        const spread = slot.y < VH / 2 ? -6 : 6
        return {
          dx: clamp(ballAdvance * 8 + 4, -4, 16),
          dy: spread * (1 + ballAdvance * 0.3),
        }
      }
      const onBallSide = (slot.y < VH / 2 && ball.y < VH / 2) || (slot.y > VH / 2 && ball.y > VH / 2)
      const hasOverlap = playerTraits.includes('Overlapping Full-Back') || playerTraits.includes('Offensive Full-Back')
      return {
        dx: onBallSide ? (hasOverlap ? 22 : 14) : 4,
        dy: onBallSide ? (slot.y < VH / 2 ? -8 : 8) * (hasOverlap ? 1.3 : 1) : 2,
      }
    }

    case 'MID': {
      const isWide = slot.slot_key.includes('M') && !slot.slot_key.includes('CM') && !slot.slot_key.includes('DM')
      const isCDM = slot.slot_key === 'CDM' || slot.slot_key === 'RDM' || slot.slot_key === 'LDM'
      const onBallSide = (slot.y < VH / 2 && ball.y < VH / 2) || (slot.y > VH / 2 && ball.y > VH / 2)

      if (isCDM) {
        const hasDeepPlay = playerTraits.includes('Deep Playmaker')
        return {
          dx: hasDeepPlay && ball.x < 80 ? -16 : clamp(ballAdvance * 6, -4, 10),
          dy: (ball.y - slot.y) * 0.06,
        }
      }
      if (isWide) {
        return {
          dx: onBallSide ? 14 : 2,
          dy: onBallSide ? (slot.y < VH/2 ? -6 : 6) : 0,
        }
      }
      return {
        dx: clamp(ballAdvance * 10 + 6, 0, 18),
        dy: ballSideY * 5 * reactivity,
      }
    }

    case 'FWD': {
      const hasDrift = playerTraits.includes('Drifts Central') || playerTraits.includes('Cuts Inside')
      const hasRun   = playerTraits.includes('Runs In Behind') || playerTraits.includes('Counterattacking Runner')
      const isWide   = slot.slot_key.includes('W') || slot.slot_key.includes('LW') || slot.slot_key.includes('RW')
      const isST     = slot.slot_key === 'ST' || slot.slot_key.includes('ST')

      if (isST) {
        return {
          dx: hasRun ? 15 : 5,
          dy: (ball.y - slot.y) * 0.1,
        }
      }
      if (isWide && hasDrift) {
        return {
          dx: 8,
          dy: slot.y < VH / 2 ? 12 : -12,
        }
      }
      if (isWide) {
        return {
          dx: 10,
          dy: slot.y < VH / 2 ? -4 : 4,
        }
      }
      return { dx: 8, dy: 0 }
    }

    default:
      return { dx: 0, dy: 0 }
  }
}

// ─── Opposition ambient — improved FWD behaviour ─────────────────────────────
// Forwards now track toward and slightly ahead of the ball rather than just
// pushing blindly in one direction. This makes them wrap around the ball carrier.

function getOppAmbientDelta(
  slot: {x:number;y:number;role:string},
  ball: {x:number;y:number},
  scenario: string,
  pressStyle: string,
  slotIndex: number,
  totalFwds: number,
): {dx:number; dy:number} {
  const isAttacking = scenario === 'goal_kick' || scenario === 'transition' || scenario === 'special'
  const isHighPress = pressStyle === 'high'

  const toBallX = ball.x - slot.x
  const toBallY = ball.y - slot.y
  const distToBall = Math.max(1, Math.sqrt(toBallX ** 2 + toBallY ** 2))
  const normX = toBallX / distToBall
  const normY = toBallY / distToBall

  if (isAttacking) {
    switch (slot.role) {
      case 'GK':
        return { dx: 0, dy: 0 }

      case 'DEF':
        return {
          dx: toBallX * 0.04,
          dy: toBallY * 0.06,
        }

      case 'MID':
        return {
          dx: normX * (isHighPress ? 18 : 8),
          dy: normY * (isHighPress ? 18 : 8),
        }

      case 'FWD': {
        // Spread forwards around the ball carrier realistically:
        // - One forward presses the ball directly (closest to ball)
        // - Others position to either side and slightly behind the ball
        //   to cut passing lanes and support the press
        const spreadAngle = (slotIndex / Math.max(1, totalFwds - 1) - 0.5) * 1.2 // -0.6 to +0.6 radians
        const pressIntensity = isHighPress ? 26 : 14

        // Rotate the toward-ball vector by spreadAngle so each fwd takes a different approach vector
        const rotX = normX * Math.cos(spreadAngle) - normY * Math.sin(spreadAngle)
        const rotY = normX * Math.sin(spreadAngle) + normY * Math.cos(spreadAngle)

        // Also add a "get in front of ball" nudge — push past the ball slightly on x
        // so they're blocking forward passes, not just chasing
        const aheadOfBall = clamp((ball.x - slot.x - 8) * 0.35, -20, 20)

        return {
          dx: rotX * pressIntensity + aheadOfBall,
          dy: rotY * pressIntensity,
        }
      }

      default:
        return { dx: 0, dy: 0 }
    }
  } else {
    // Opp is in possession — push forward toward our goal
    switch (slot.role) {
      case 'GK':
        return { dx: -4, dy: 0 }
      case 'DEF':
        return { dx: -12, dy: toBallY * 0.05 }
      case 'MID':
        return { dx: -18, dy: normY * 10 }
      case 'FWD': {
        // Forwards spread wide and deep to stretch the defence
        const spreadY = (slotIndex % 2 === 0 ? -1 : 1) * 14
        return {
          dx: -28,
          dy: normY * 10 + spreadY,
        }
      }
      default:
        return { dx: 0, dy: 0 }
    }
  }
}

// ─── Spread nodes ─────────────────────────────────────────────────────────────

function spreadNodes(
  nodes: {x:number;y:number;key:string}[],
  minDist: number = R * 3.2,
  passes: number = 4,
): Record<string, {x:number;y:number}> {
  const positions = nodes.map(n => ({ x: n.x, y: n.y, key: n.key }))
  for (let p = 0; p < passes; p++) {
    for (let i = 0; i < positions.length; i++) {
      for (let j = i + 1; j < positions.length; j++) {
        const dx = positions[j].x - positions[i].x
        const dy = positions[j].y - positions[i].y
        const d = Math.max(0.1, Math.sqrt(dx * dx + dy * dy))
        if (d >= minDist) continue
        const push = (minDist - d) / 2 * 0.5
        const ux = dx / d
        const uy = dy / d
        positions[i].x = clamp(positions[i].x - ux * push, 8, VW - 8)
        positions[i].y = clamp(positions[i].y - uy * push, 8, VH - 8)
        positions[j].x = clamp(positions[j].x + ux * push, 8, VW - 8)
        positions[j].y = clamp(positions[j].y + uy * push, 8, VH - 8)
      }
    }
  }
  return Object.fromEntries(positions.map(p => [p.key, { x: p.x, y: p.y }]))
}

// ─── Props ────────────────────────────────────────────────────────────────────

interface TacticalPitchProps {
  report: any
  scenario: any | null
  progress: number
  onScrub: (p: number) => void
  oppFormation?: string
  oppPressStyle?: string
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function TacticalPitch({
  report,
  scenario,
  progress,
  onScrub,
  oppFormation = '4-3-3',
  oppPressStyle = 'medium',
}: TacticalPitchProps) {
  const scrubRef = useRef<HTMLDivElement>(null)

  const formation = report?.recommended_formation || '4-3-3'
  const ownSlots  = FORMATION_SLOTS[formation] || FORMATION_SLOTS['4-3-3']
  const oppSlots  = mirrorFormation(FORMATION_SLOTS[oppFormation] || FORMATION_SLOTS['4-3-3'])
  const scenarioId = scenario?.scenario || 'goal_kick'

  // Count opp forwards for spread logic
  const oppFwdCount = oppSlots.filter(s => s.role === 'FWD').length

  const totalDuration = useMemo(() => {
    if (!scenario?.frames?.length) return 1
    return scenario.frames.reduce((s: number, f: any) => s + f.duration_ms, 0)
  }, [scenario])

  // ── Interpolated state ──────────────────────────────────────────────────────
  const state = useMemo(() => {
    const xi = report?.starting_xi || []
    if (!scenario?.frames?.length) {
      const ball = { x: 100, y: 65 }
      const ownNodes = ownSlots.map((slot, i) => {
        const amb = getAmbientDelta(slot, ball, scenarioId, xi[i]?.traits || [])
        return {
          x: clamp(slot.x + amb.dx, 8, VW - 8),
          y: clamp(slot.y + amb.dy, 8, VH - 8),
          key: `own-${i}`,
        }
      })
      const oppNodes = oppSlots.map((slot, i) => ({
        x: clamp(slot.x, 8, VW - 8),
        y: clamp(slot.y, 8, VH - 8),
        key: `opp-${i}`,
      }))
      return {
        ownPos: spreadNodes(ownNodes),
        oppPos: spreadNodes(oppNodes),
        ball,
        frame: null,
        traitLabels: {} as Record<number, string>,
        carriers: new Set<number>(),
        targets: new Set<number>(),
      }
    }

    const targetMs = (progress / 100) * totalDuration
    let accTime = 0
    let fi = 0
    for (let i = 0; i < scenario.frames.length; i++) {
      if (targetMs >= accTime && targetMs <= accTime + scenario.frames[i].duration_ms) {
        fi = i; break
      }
      accTime += scenario.frames[i].duration_ms
      fi = i
    }
    fi = Math.min(fi, scenario.frames.length - 1)

    const cur = scenario.frames[fi]
    const nxt = scenario.frames[Math.min(fi + 1, scenario.frames.length - 1)]
    const localT = cur.duration_ms > 0
      ? clamp((targetMs - accTime) / cur.duration_ms, 0, 1)
      : 0

    const ball = {
      x: lerp(cur.ball.x, nxt.ball.x, localT),
      y: lerp(cur.ball.y, nxt.ball.y, localT),
    }

    const carriers = new Set<number>()
    const targets  = new Set<number>()
    const traitLabels: Record<number, string> = {}

    const ownNodes = ownSlots.map((slot, i) => {
      const player       = xi[i]
      const playerTraits = player?.traits || []

      const curD = cur.players?.find((p: any) =>
        (player?.player_id && p.player_id === player.player_id) ||
        p.slot_key === slot.slot_key
      )
      const nxtD = nxt.players?.find((p: any) =>
        (player?.player_id && p.player_id === player.player_id) ||
        p.slot_key === slot.slot_key
      )

      let dx: number, dy: number

      if (curD) {
        dx = lerp(curD.dx || 0, nxtD?.dx || curD.dx || 0, localT)
        dy = lerp(curD.dy || 0, nxtD?.dy || curD.dy || 0, localT)
        if (curD.is_ball_carrier) carriers.add(i)
        if (curD.is_ball_target)  targets.add(i)
        if (curD.trait_label)     traitLabels[i] = curD.trait_label
      } else {
        // Pass traitLabel so short-option players drop correctly even without explicit delta
        const amb = getAmbientDelta(slot, ball, scenarioId, playerTraits, undefined)
        dx = lerp(0, amb.dx, Math.min(localT * 2, 1))
        dy = lerp(0, amb.dy, Math.min(localT * 2, 1))
      }

      return {
        x: clamp(slot.x + dx, 8, VW - 8),
        y: clamp(slot.y + dy, 8, VH - 8),
        key: `own-${i}`,
      }
    })

    // ── After building ownNodes, resolve trait labels so short-option players ──
    // can influence their ambient in the *next* frame cycle if needed
    // (Here we apply it retroactively for the explicit-delta path)
    let fwdSlotIndex = 0
    const oppNodes = oppSlots.map((slot, i) => {
      const curD = cur.opp_players?.find((p: any) =>
        p.slot_index === i || p.slot_key === slot.slot_key
      )
      const nxtD = nxt.opp_players?.find((p: any) =>
        p.slot_index === i || p.slot_key === slot.slot_key
      )

      let dx: number, dy: number

      if (curD) {
        dx = lerp(curD.dx || 0, nxtD?.dx || curD.dx || 0, localT)
        dy = lerp(curD.dy || 0, nxtD?.dy || curD.dy || 0, localT)
      } else {
        const fwdIdx = slot.role === 'FWD' ? fwdSlotIndex : 0
        const amb = getOppAmbientDelta(slot, ball, scenarioId, oppPressStyle, fwdIdx, oppFwdCount)
        dx = lerp(0, amb.dx, Math.min(localT * 1.5, 1))
        dy = lerp(0, amb.dy, Math.min(localT * 1.5, 1))
      }

      if (slot.role === 'FWD') fwdSlotIndex++

      return {
        x: clamp(slot.x + dx, 8, VW - 8),
        y: clamp(slot.y + dy, 8, VH - 8),
        key: `opp-${i}`,
      }
    })

    return {
      ownPos:      spreadNodes(ownNodes),
      oppPos:      spreadNodes(oppNodes),
      ball,
      frame:       cur,
      traitLabels,
      carriers,
      targets,
    }
  }, [scenario, progress, totalDuration, ownSlots, oppSlots, scenarioId, report, oppPressStyle, oppFwdCount])

  // ── Scrubber ──────────────────────────────────────────────────────────────
  const handleScrub = useCallback((e: React.MouseEvent) => {
    if (!scrubRef.current) return
    const rect = scrubRef.current.getBoundingClientRect()
    onScrub(clamp(((e.clientX - rect.left) / rect.width) * 100, 0, 100))
  }, [onScrub])

  const handleDrag = useCallback((e: React.MouseEvent) => {
    const move = (ev: MouseEvent) => {
      if (!scrubRef.current) return
      const rect = scrubRef.current.getBoundingClientRect()
      onScrub(clamp(((ev.clientX - rect.left) / rect.width) * 100, 0, 100))
    }
    const up = () => { window.removeEventListener('mousemove', move); window.removeEventListener('mouseup', up) }
    window.addEventListener('mousemove', move)
    window.addEventListener('mouseup', up)
    handleScrub(e)
  }, [handleScrub, onScrub])

  const xi = report?.starting_xi || []
  const duration = state.frame?.duration_ms || 800

  return (
    <div className="relative w-full flex flex-col gap-3">

      {/* ── Pitch ── */}
      <div
        className="relative w-full rounded-xl overflow-hidden shadow-2xl"
        style={{ aspectRatio: '220/130', background: 'linear-gradient(160deg, #1c4028 0%, #163318 50%, #1c4028 100%)' }}
      >
        {/* Grass stripes */}
        <svg className="absolute inset-0 w-full h-full" viewBox="0 0 220 130" preserveAspectRatio="none">
          {Array.from({length: 11}).map((_,i) => (
            <rect key={i} x={i*20} y={0} width={20} height={130}
              fill={i%2===0 ? 'rgba(255,255,255,0.022)' : 'rgba(0,0,0,0.035)'} />
          ))}
        </svg>

        {/* Pitch markings */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 220 130">
          <g stroke="rgba(255,255,255,0.22)" fill="none" strokeWidth="0.45">
            <rect x="4" y="4" width="212" height="122" rx="1.5" />
            <line x1="110" y1="4" x2="110" y2="126" />
            <circle cx="110" cy="65" r="16" />
            <circle cx="110" cy="65" r="0.7" fill="rgba(255,255,255,0.3)" stroke="none" />
            <rect x="4" y="31" width="24" height="68" />
            <rect x="4" y="48" width="9" height="34" />
            <rect x="192" y="31" width="24" height="68" />
            <rect x="211" y="48" width="9" height="34" />
            <rect x="1"   y="54" width="3" height="22" stroke="rgba(255,255,255,0.5)" />
            <rect x="216" y="54" width="3" height="22" stroke="rgba(255,255,255,0.5)" />
            <circle cx="20"  cy="65" r="0.7" fill="rgba(255,255,255,0.25)" stroke="none" />
            <circle cx="200" cy="65" r="0.7" fill="rgba(255,255,255,0.25)" stroke="none" />
            <path d="M 28 51 A 11 11 0 0 1 28 79" />
            <path d="M 192 51 A 11 11 0 0 0 192 79" />
          </g>
        </svg>

        {/* Simulation layer */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 220 130">
          <defs>
            <marker id="arr" markerWidth="4" markerHeight="4" refX="3.5" refY="2" orient="auto">
              <polygon points="0 0, 4 2, 0 4" fill="rgba(250,204,21,0.55)" />
            </marker>
            <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="1.5" result="b"/>
              <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
            </filter>
            <filter id="soft" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="0.8"/>
            </filter>
          </defs>

          {/* Zone callouts */}
          {state.frame?.callouts?.filter((c:any) => c.type === 'zone' && c.zone && ZONE_RECTS[c.zone]).map((c:any, i:number) => {
            const z = ZONE_RECTS[c.zone]
            const col = SEVERITY_COLOR[c.severity] || SEVERITY_COLOR.neutral
            return (
              <g key={i}>
                <rect x={z.x} y={z.y} width={z.w} height={z.h}
                  fill={col} fillOpacity="0.1" stroke={col} strokeWidth="0.5" strokeDasharray="3 2" />
                <text x={z.x+z.w/2} y={z.y+z.h/2} textAnchor="middle" dominantBaseline="middle"
                  fontSize="3.8" fontFamily="monospace" fontWeight="800" fill={col} fillOpacity="0.85">
                  {c.text}
                </text>
              </g>
            )
          })}

          {/* Ball intent path — toned down */}
          {(() => {
            const intent = state.frame?.ball_intent
            if (!intent?.from || !intent?.to) return null
            const fromSlot = ownSlots.find(s => s.slot_key === intent.from) || oppSlots.find(s => s.slot_key === intent.from)
            const toSlot   = ownSlots.find(s => s.slot_key === intent.to)   || oppSlots.find(s => s.slot_key === intent.to)
            if (!fromSlot || !toSlot) return null

            const fromKey = fromSlot.slot_key.startsWith('Opp') ? `opp-${oppSlots.indexOf(fromSlot)}` : `own-${ownSlots.indexOf(fromSlot)}`
            const toKey   = toSlot.slot_key.startsWith('Opp')   ? `opp-${oppSlots.indexOf(toSlot)}`   : `own-${ownSlots.indexOf(toSlot)}`
            const fp = (fromSlot.slot_key.startsWith('Opp') ? state.oppPos : state.ownPos)[fromKey] || fromSlot
            const tp = (toSlot.slot_key.startsWith('Opp')   ? state.oppPos : state.ownPos)[toKey]   || toSlot

            const curved = ['diagonal_switch','cross_field','cross','through_ball','overlap_run'].includes(intent.lane||'')
            const mx = (fp.x + tp.x) / 2
            const my = (fp.y + tp.y) / 2 - (curved ? 16 : 0)
            const d = curved
              ? `M ${fp.x} ${fp.y} Q ${mx} ${my} ${tp.x} ${tp.y}`
              : `M ${fp.x} ${fp.y} L ${tp.x} ${tp.y}`

            return (
              <path d={d} stroke="rgba(250,204,21,0.45)" strokeWidth="0.7"
                strokeDasharray="3.5 2.5" fill="none" strokeLinecap="round"
                markerEnd="url(#arr)" />
            )
          })()}

          {/* Linkup lines — subtle */}
          {(report?.linkup_pairs || []).map((pair:any, i:number) => {
            const ia = xi.findIndex((p:any) => p.name === pair.player_a)
            const ib = xi.findIndex((p:any) => p.name === pair.player_b)
            if (ia < 0 || ib < 0) return null
            const pa = state.ownPos[`own-${ia}`]
            const pb = state.ownPos[`own-${ib}`]
            if (!pa || !pb) return null
            return (
              <line key={i} x1={pa.x} y1={pa.y} x2={pb.x} y2={pb.y}
                stroke="rgba(250,204,21,0.10)" strokeWidth="0.7" strokeLinecap="round" />
            )
          })}

          {/* ── Opposition nodes ── */}
          {oppSlots.map((slot, i) => {
            const pos = state.oppPos[`opp-${i}`]
            if (!pos) return null
            const curD     = state.frame?.opp_players?.find((p:any) => p.slot_index === i || p.slot_key === slot.slot_key)
            const reaction  = curD?.reaction || 'hold'
            const isDanger  = ['isolated','overloaded','dragged_out'].includes(reaction)
            const isPressing= ['pressing','counter','attacking'].includes(reaction)

            return (
              <g key={`opp-${i}`}
                style={{
                  transform: `translate(${pos.x}px, ${pos.y}px)`,
                  transition: `transform ${duration}ms cubic-bezier(.25,.46,.45,.94)`,
                }}
              >
                {/* Shadow */}
                <circle r={R + 0.5} fill="rgba(0,0,0,0.3)" cy={0.8} filter="url(#soft)" />
                {/* Body — stroke changes colour to signal state, no outer ring */}
                <circle r={R}
                  fill="#263f5c"
                  stroke={isDanger ? '#C8612A' : isPressing ? '#e8a060' : '#4a7aaa'}
                  strokeWidth={isDanger || isPressing ? 1.1 : 0.6}
                />
                {/* Shine */}
                <circle cx={-1} cy={-1.2} r={1.4} fill="rgba(255,255,255,0.12)" />
                {/* Number */}
                <text textAnchor="middle" dominantBaseline="central"
                  fontSize="2.5" fontFamily="monospace" fontWeight="900" fill="rgba(255,255,255,0.9)">
                  {i + 1}
                </text>
                {/* Role label */}
                <text y={R + 4} textAnchor="middle" fontSize="2.2" fontFamily="monospace"
                  fill="rgba(255,255,255,0.4)">
                  {slot.role}
                </text>
              </g>
            )
          })}

          {/* ── Own player nodes ── */}
          {ownSlots.map((slot, i) => {
            const pos      = state.ownPos[`own-${i}`]
            if (!pos) return null
            const player   = xi[i]
            const isCarrier = state.carriers.has(i)
            const isTarget  = state.targets.has(i)
            const traitLbl  = state.traitLabels[i]
            const isWeak    = player?.attributes?.role_rating && player.attributes.role_rating < 11
            const isForm    = player?.form_score && player.form_score > 0.65
            const initials  = player?.name
              ? player.name.split(' ').map((n:string) => n[0]).join('').slice(0,2).toUpperCase()
              : slot.slot_key.slice(0,2)

            return (
              <g key={`own-${i}`}
                style={{
                  transform: `translate(${pos.x}px, ${pos.y}px)`,
                  transition: `transform ${duration}ms cubic-bezier(.25,.46,.45,.94)`,
                }}
              >
                {/* Carrier ring */}
                {isCarrier && (
                  <circle r={R_CARRIER} fill="none"
                    stroke="rgba(250,204,21,0.85)" strokeWidth="0.8" />
                )}
                {/* Target dashed ring */}
                {isTarget && (
                  <circle r={R + 2.8} fill="none"
                    stroke="rgba(255,255,255,0.5)" strokeWidth="0.5" strokeDasharray="1.8 1.8" />
                )}
                {/* Shadow */}
                <circle r={R + 0.5} fill="rgba(0,0,0,0.3)" cy={0.8} filter="url(#soft)" />
                {/* Body — stroke carries state signal, no separate glow ring */}
                <circle r={R}
                  fill="#B86A3C"
                  stroke={isWeak ? 'rgba(200,60,60,0.9)' : isForm ? 'rgba(90,200,120,0.85)' : '#f0c090'}
                  strokeWidth={isWeak || isForm ? 1.1 : 0.5}
                  filter={isCarrier ? 'url(#glow)' : ''}
                />
                {/* Shine */}
                <circle cx={-1.2} cy={-1.5} r={1.6} fill="rgba(255,255,255,0.16)" />
                {/* Initials */}
                <text textAnchor="middle" dominantBaseline="central"
                  fontSize="2.6" fontFamily="monospace" fontWeight="900"
                  fill="rgba(255,255,255,0.96)">
                  {initials}
                </text>
                {/* Name */}
                <text y={R + 4} textAnchor="middle" fontSize="2.2" fontFamily="monospace"
                  fill="rgba(255,255,255,0.55)">
                  {player?.name?.split(' ')[0] || slot.slot_key}
                </text>

                {/* ── Trait label — small tooltip popping from node ── */}
                {traitLbl && (
                  <g>
                    {/* Connector stem */}
                    <line x1={0} y1={-(R+1)} x2={0} y2={-17}
                      stroke="rgba(160,150,140,0.35)" strokeWidth="0.4" />
                    {/* Pill background */}
                    <rect
                      x={-(Math.min(traitLbl.length, 16) * 1.55 + 4) / 2}
                      y={-25}
                      width={Math.min(traitLbl.length, 16) * 1.55 + 4}
                      height={7}
                      rx={2}
                      fill="rgba(38,34,30,0.88)"
                      stroke="rgba(130,120,110,0.35)"
                      strokeWidth="0.3"
                    />
                    {/* Text */}
                    <text y={-21} textAnchor="middle" dominantBaseline="central"
                      fontSize="2.1" fontFamily="monospace" fontWeight="600"
                      fill="rgba(230,225,215,0.92)">
                      {traitLbl.length > 16 ? traitLbl.slice(0,15)+'…' : traitLbl}
                    </text>
                  </g>
                )}
              </g>
            )
          })}

          {/* ── Player callout labels — small tooltip close to node ── */}
          {state.frame?.callouts?.filter((c:any) => c.type === 'player').map((c:any, idx:number) => {
            const oppIdx = oppSlots.findIndex(s => s.slot_key === c.target)
            const pos = oppIdx >= 0 ? state.oppPos[`opp-${oppIdx}`] : null
            if (!pos) return null
            const col = SEVERITY_COLOR[c.severity] || SEVERITY_COLOR.neutral
            const textLen = Math.min(c.text.length, 18)
            const w = textLen * 1.55 + 6
            return (
              <g key={`lbl-${idx}`}
                style={{ transform: `translate(${pos.x}px, ${pos.y}px)` }}>
                {/* Stem */}
                <line x1={0} y1={-(R+1)} x2={0} y2={-16}
                  stroke="rgba(160,150,140,0.35)" strokeWidth="0.4" />
                {/* Pill */}
                <rect x={-w/2} y={-23} width={w} height={7} rx={2}
                  fill="rgba(38,34,30,0.88)"
                  stroke={col} strokeWidth="0.35" />
                {/* Text */}
                <text y={-19.5} textAnchor="middle" dominantBaseline="central"
                  fontSize="2.1" fontFamily="monospace" fontWeight="600"
                  fill="rgba(230,225,215,0.92)">
                  {c.text.length > 18 ? c.text.slice(0,17)+'…' : c.text}
                </text>
              </g>
            )
          })}

          {/* Ball */}
          <g style={{
            transform: `translate(${state.ball.x}px, ${state.ball.y}px)`,
            transition: `transform ${Math.max(400, duration * 0.75)}ms cubic-bezier(.25,.46,.45,.94)`,
          }}>
            <circle r={3.8} fill="rgba(255,255,255,0.12)" />
            <circle r={2.2} fill="white" stroke="rgba(40,20,5,0.45)" strokeWidth="0.4"
              filter="url(#soft)" />
            <circle r={1} fill="none" stroke="rgba(150,120,80,0.4)" strokeWidth="0.3" />
          </g>
        </svg>

        {/* Frame action text */}
        <AnimatePresence mode="wait">
          {state.frame?.action && (
            <motion.div
              key={state.frame.frame}
              initial={{ opacity: 0, y: 3 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.25 }}
              className="absolute bottom-3 left-3 right-3 pointer-events-none"
            >
              <div style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                background: 'rgba(0,0,0,0.62)',
                backdropFilter: 'blur(4px)',
                borderRadius: '8px',
                padding: '5px 10px',
              }}>
                <span style={{ fontSize: '10px', fontFamily: 'monospace', fontWeight: 600, color: 'rgba(255,255,255,0.82)' }}>
                  {state.frame.action}
                </span>
                {state.frame.note && (
                  <span style={{ fontSize: '9px', fontFamily: 'monospace', color: '#e8a060' }}>
                    — {state.frame.note}
                  </span>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Scrubber */}
      <div
        ref={scrubRef}
        onMouseDown={handleDrag}
        onClick={handleScrub}
        style={{
          height: '6px',
          background: 'rgba(200,184,154,0.25)',
          borderRadius: '999px',
          cursor: 'ew-resize',
          position: 'relative',
        }}
      >
        <div style={{
          position: 'absolute', inset: '0', right: `${100 - progress}%`,
          background: '#B86A3C', borderRadius: '999px',
        }} />
        <div style={{
          position: 'absolute', top: '50%', left: `${progress}%`,
          transform: 'translate(-50%, -50%)',
          width: '14px', height: '14px',
          background: 'white', border: '2px solid #B86A3C',
          borderRadius: '50%', pointerEvents: 'none',
        }} />
      </div>
    </div>
  )
}