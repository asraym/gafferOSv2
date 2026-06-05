import type { BallIntent } from './types'

export function isCurvedLane(intent?: BallIntent | null) {
  return ['diagonal_switch', 'cross_field', 'long_ball', 'cross'].includes(intent?.lane || '')
}

export function isDashedLane(intent?: BallIntent | null) {
  return ['through_ball', 'overlap_run', 'vertical_carry'].includes(intent?.lane || '')
}

export function pathColor(intent?: BallIntent | null) {
  if (intent?.type === 'shot') return '#f0c65a'
  if (intent?.type === 'cross' || intent?.lane === 'cross_field') return '#8fc8ff'
  if (intent?.type === 'through_ball') return '#e8a060'
  return '#f7ead2'
}