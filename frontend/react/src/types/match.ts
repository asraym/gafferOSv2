export interface Match {
  id?: number
  match_id?: number
  opponent_name: string
  match_date: string
  venue: 'home' | 'away' | 'neutral'
}