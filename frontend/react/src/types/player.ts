export interface Player {
  id?: number
  player_id?: number
  name?: string
  broad_position?: string
  position?: string
  specific_position?: string
  jersey_number?: number | null
  is_active?: boolean
  overall_rating?: number | null
  role_rating?: number | null
  traits?: string[]
  key_attributes?: Record<string, number | null>
}