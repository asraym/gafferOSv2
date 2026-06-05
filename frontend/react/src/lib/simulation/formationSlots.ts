import type { PlayerXI } from './types'

export interface SlotPosition {
  slot_key: string
  label: string
  x: number
  y: number
}

const DEFAULT_SLOTS: SlotPosition[] = [
  { slot_key: 'GK', label: 'GK', x: 14, y: 65 },
  { slot_key: 'LB', label: 'LB', x: 42, y: 20 },
  { slot_key: 'LCB', label: 'CB', x: 46, y: 48 },
  { slot_key: 'RCB', label: 'CB', x: 46, y: 82 },
  { slot_key: 'RB', label: 'RB', x: 42, y: 110 },
  { slot_key: 'LDM', label: 'DM', x: 82, y: 48 },
  { slot_key: 'RDM', label: 'DM', x: 82, y: 82 },
  { slot_key: 'LW', label: 'LW', x: 126, y: 24 },
  { slot_key: 'CAM', label: 'AM', x: 120, y: 65 },
  { slot_key: 'RW', label: 'RW', x: 126, y: 106 },
  { slot_key: 'ST', label: 'ST', x: 166, y: 65 },
]

const SLOTS_433: SlotPosition[] = [
  { slot_key: 'GK', label: 'GK', x: 14, y: 65 },
  { slot_key: 'LB', label: 'LB', x: 42, y: 20 },
  { slot_key: 'LCB', label: 'CB', x: 46, y: 48 },
  { slot_key: 'RCB', label: 'CB', x: 46, y: 82 },
  { slot_key: 'RB', label: 'RB', x: 42, y: 110 },
  { slot_key: 'CDM', label: 'DM', x: 82, y: 65 },
  { slot_key: 'LCM', label: 'CM', x: 98, y: 42 },
  { slot_key: 'RCM', label: 'CM', x: 98, y: 88 },
  { slot_key: 'LW', label: 'LW', x: 136, y: 24 },
  { slot_key: 'ST', label: 'ST', x: 166, y: 65 },
  { slot_key: 'RW', label: 'RW', x: 136, y: 106 },
]

const SLOTS_352: SlotPosition[] = [
  { slot_key: 'GK', label: 'GK', x: 14, y: 65 },
  { slot_key: 'LCB', label: 'CB', x: 48, y: 34 },
  { slot_key: 'CB', label: 'CB', x: 42, y: 65 },
  { slot_key: 'RCB', label: 'CB', x: 48, y: 96 },
  { slot_key: 'LWB', label: 'WB', x: 88, y: 16 },
  { slot_key: 'LCM', label: 'CM', x: 92, y: 45 },
  { slot_key: 'CDM', label: 'DM', x: 90, y: 65 },
  { slot_key: 'RCM', label: 'CM', x: 92, y: 85 },
  { slot_key: 'RWB', label: 'WB', x: 88, y: 114 },
  { slot_key: 'LST', label: 'ST', x: 154, y: 48 },
  { slot_key: 'RST', label: 'ST', x: 154, y: 82 },
]

export const OPP_SLOTS: SlotPosition[] = [
  { slot_key: 'Opp GK', label: 'GK', x: 206, y: 65 },
  { slot_key: 'Opp RB', label: 'RB', x: 174, y: 22 },
  { slot_key: 'Opp RCB', label: 'CB', x: 170, y: 48 },
  { slot_key: 'Opp LCB', label: 'CB', x: 170, y: 82 },
  { slot_key: 'Opp LB', label: 'LB', x: 174, y: 108 },
  { slot_key: 'Opp RCM', label: 'CM', x: 136, y: 42 },
  { slot_key: 'Opp CDM', label: 'DM', x: 132, y: 65 },
  { slot_key: 'Opp LCM', label: 'CM', x: 136, y: 88 },
  { slot_key: 'Opp RW', label: 'RW', x: 96, y: 24 },
  { slot_key: 'Opp LW', label: 'LW', x: 96, y: 106 },
  { slot_key: 'Opp ST', label: 'ST', x: 66, y: 65 },
]

export function getFormationSlots(formation?: string): SlotPosition[] {
  const key = (formation || '').replace(/\s/g, '')
  if (key.includes('3-5-2')) return SLOTS_352
  if (key.includes('4-3-3')) return SLOTS_433
  return DEFAULT_SLOTS
}

export function normalizeSlotKey(slotKey?: string | null) {
  if (!slotKey) return null
  const key = slotKey.trim()
  const aliases: Record<string, string> = {
    LCB: 'LCB',
    RCB: 'RCB',
    CB: 'RCB',
    DM: 'CDM',
    LDM: 'LDM',
    RDM: 'RDM',
    AM: 'CAM',
    CF: 'ST',
    FW: 'ST',
  }
  return aliases[key] || key
}

export function findSlot(slots: SlotPosition[], slotKey?: string | null) {
  const normalized = normalizeSlotKey(slotKey)
  return slots.find((slot) => slot.slot_key === normalized)
}

export function findOppSlot(slotKey?: string | null, slotIndex?: number) {
  if (slotKey) {
    const direct = OPP_SLOTS.find((slot) => slot.slot_key === slotKey)
    if (direct) return direct
  }
  if (slotIndex != null) return OPP_SLOTS[slotIndex]
  return undefined
}

export function assignPlayersToSlots(players: PlayerXI[], slots: SlotPosition[]) {
  return slots.map((slot, index) => {
    const exact = players.find((player) => {
      return normalizeSlotKey(player.slot_key || player.specific_position || player.position) === slot.slot_key
    })

    if (exact) return exact
    return players[index] || null
  })
}

export function toScenePosition(point: { x: number; y: number }, height = 0): [number, number, number] {
  return [point.x - 110, height, point.y - 65]
}
