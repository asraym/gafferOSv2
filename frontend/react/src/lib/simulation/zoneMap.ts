import type { ZoneKey } from './types'

export interface ZoneRect {
  x: number
  y: number
  width: number
  height: number
}

export const ZONE_RECTS: Record<ZoneKey, ZoneRect> = {
  defensive_third: { x: 0, y: 0, width: 73, height: 130 },
  midfield_third: { x: 73, y: 0, width: 74, height: 130 },
  attacking_third: { x: 147, y: 0, width: 73, height: 130 },
  left_channel: { x: 0, y: 0, width: 220, height: 45 },
  right_channel: { x: 0, y: 85, width: 220, height: 45 },
  central_channel: { x: 0, y: 45, width: 220, height: 40 },
  left_flank: { x: 0, y: 0, width: 220, height: 32 },
  right_flank: { x: 0, y: 98, width: 220, height: 32 },
  left_box: { x: 147, y: 0, width: 63, height: 50 },
  right_box: { x: 147, y: 80, width: 63, height: 50 },
  central_box: { x: 147, y: 45, width: 63, height: 40 },
}

export function severityColor(severity?: string) {
  if (severity === 'danger') return '#dd6b52'
  if (severity === 'opportunity') return '#83b86f'
  return '#d4c3a6'
}