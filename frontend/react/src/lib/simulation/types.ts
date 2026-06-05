export type ScenarioKey =
  | 'goal_kick'
  | 'transition'
  | 'special'
  | 'defensive_shape'
  | 'opponent_threat'

export type BallIntentType =
  | 'carry'
  | 'pass'
  | 'switch'
  | 'cross'
  | 'through_ball'
  | 'clearance'
  | 'shot'
  | 'press_trigger'
  | 'hold'
  | 'long_ball'

export type BallLane =
  | 'short_pass'
  | 'diagonal_switch'
  | 'through_ball'
  | 'overlap_run'
  | 'cross_field'
  | 'vertical_carry'
  | 'long_ball'
  | 'cutback'
  | 'layoff'

export type CalloutSeverity = 'opportunity' | 'danger' | 'neutral'

export type ZoneKey =
  | 'left_channel'
  | 'right_channel'
  | 'central_channel'
  | 'left_box'
  | 'right_box'
  | 'central_box'
  | 'defensive_third'
  | 'midfield_third'
  | 'attacking_third'
  | 'left_flank'
  | 'right_flank'

export type OppReaction =
  | 'hold'
  | 'pressing'
  | 'tracking'
  | 'retreating'
  | 'marking'
  | 'attacking'
  | 'supporting'
  | 'probing'
  | 'dribbling'
  | 'counter'
  | 'isolated'
  | 'covering'
  | 'overloaded'
  | 'dragged_out'
  | 'screening'
  | 'pinning'

export interface ScenarioMeta {
  scenario: ScenarioKey
  title: string
  phase: string
  purpose: string
  takeaway: string
}

export interface BallPosition {
  x: number
  y: number
}

export interface BallIntent {
  type: BallIntentType
  from: string | null
  to: string | null
  lane: BallLane | null
}

export interface Callout {
  type: 'player' | 'zone'
  text: string
  severity: CalloutSeverity
  target?: string
  zone?: ZoneKey
}

export interface PlayerDelta {
  name: string
  player_id: number | null
  slot_key: string | null
  dx: number
  dy: number
  trait_label: string | null
  is_ball_carrier: boolean
  is_ball_target: boolean
}

export interface OppDelta {
  slot_index: number
  slot_key: string | null
  dx: number
  dy: number
  reaction: OppReaction
}

export interface SimFrame {
  frame: number
  duration_ms: number
  ball: BallPosition
  ball_carrier: string | null
  action: string
  note: string | null
  ball_intent: BallIntent | null
  callouts: Callout[]
  players: PlayerDelta[]
  opp_players: OppDelta[]
}

export interface ScenarioSimulation {
  scenario: ScenarioKey
  meta: ScenarioMeta
  frame_count: number
  frames: SimFrame[]
}

export interface SimulationPackage {
  match_id: number
  team_id: number
  playlist: ScenarioSimulation[]
  errors: string[] | null
}

export interface PlayerXI {
  name: string
  player_id?: number | null
  id?: number
  position?: string
  specific_position?: string
  slot_key?: string
  jersey_number?: number
}

export interface TacticalFilmProps {
  matchId: number
  teamId: number
  formation?: string
  xi?: PlayerXI[]
  summary?: {
    formation?: string
    press?: string
    risk?: string
    focus?: string
  }
}
