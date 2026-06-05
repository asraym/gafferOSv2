# core/scenario/types.py — v2
# Extended with: ball_intent, callouts, slot_key, scenario metadata

from dataclasses import dataclass, field
from typing import Optional, Literal


# ─── Ball Intent ──────────────────────────────────────────────────────────────

BallIntentType = Literal[
    "carry", "pass", "switch", "cross",
    "through_ball", "clearance", "shot",
    "press_trigger", "hold", "long_ball"
]

LaneType = Literal[
    "short_pass", "diagonal_switch", "through_ball",
    "overlap_run", "cross_field", "vertical_carry",
    "long_ball", "cutback", "layoff"
]


@dataclass
class BallIntent:
    type: BallIntentType
    from_slot: Optional[str] = None   # e.g. "CB", "GK", "CDM"
    to_slot: Optional[str] = None     # e.g. "LW", "ST", "RB"
    lane: Optional[LaneType] = None

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "from": self.from_slot,
            "to": self.to_slot,
            "lane": self.lane,
        }


# ─── Callouts ─────────────────────────────────────────────────────────────────

CalloutType = Literal["player", "zone"]
CalloutSeverity = Literal["opportunity", "danger", "neutral"]

ZoneKey = Literal[
    "left_channel", "right_channel", "central_channel",
    "left_box", "right_box", "central_box",
    "defensive_third", "midfield_third", "attacking_third",
    "left_flank", "right_flank"
]


@dataclass
class Callout:
    type: CalloutType
    text: str
    severity: CalloutSeverity = "neutral"
    target: Optional[str] = None    # player name or opp slot key e.g. "Opp RB"
    zone: Optional[ZoneKey] = None  # only when type == "zone"

    def to_dict(self) -> dict:
        d = {
            "type": self.type,
            "text": self.text,
            "severity": self.severity,
        }
        if self.target:
            d["target"] = self.target
        if self.zone:
            d["zone"] = self.zone
        return d


# ─── Player Delta ─────────────────────────────────────────────────────────────

@dataclass
class PlayerDelta:
    name: str
    dx: float
    dy: float
    slot_key: Optional[str] = None       # e.g. "CB", "LB", "CAM"
    player_id: Optional[int] = None
    trait_label: Optional[str] = None
    is_ball_target: bool = False
    is_ball_carrier: bool = False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "player_id": self.player_id,
            "slot_key": self.slot_key,
            "dx": self.dx,
            "dy": self.dy,
            "trait_label": self.trait_label,
            "is_ball_target": self.is_ball_target,
            "is_ball_carrier": self.is_ball_carrier,
        }


# ─── Opp Delta ────────────────────────────────────────────────────────────────

OppReaction = Literal[
    "hold", "pressing", "tracking", "retreating",
    "marking", "attacking", "supporting", "probing",
    "dribbling", "counter", "isolated", "covering",
    "overloaded", "dragged_out", "screening", "pinning"
]


@dataclass
class OppDelta:
    slot_index: int
    dx: float
    dy: float
    slot_key: Optional[str] = None    # e.g. "RB", "CDM", "ST"
    reaction: OppReaction = "hold"

    def to_dict(self) -> dict:
        return {
            "slot_index": self.slot_index,
            "slot_key": self.slot_key,
            "dx": self.dx,
            "dy": self.dy,
            "reaction": self.reaction,
        }


# ─── Sim Frame ────────────────────────────────────────────────────────────────

@dataclass
class BallState:
    x: float
    y: float


@dataclass
class SimFrame:
    frame: int
    duration_ms: int
    ball: BallState
    ball_carrier: Optional[str]
    action: str
    players: list[PlayerDelta] = field(default_factory=list)
    opp_players: list[OppDelta] = field(default_factory=list)
    note: Optional[str] = None
    ball_intent: Optional[BallIntent] = None
    callouts: list[Callout] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "frame": self.frame,
            "duration_ms": self.duration_ms,
            "ball": {"x": self.ball.x, "y": self.ball.y},
            "ball_carrier": self.ball_carrier,
            "action": self.action,
            "note": self.note,
            "ball_intent": self.ball_intent.to_dict() if self.ball_intent else None,
            "callouts": [c.to_dict() for c in self.callouts],
            "players": [p.to_dict() for p in self.players],
            "opp_players": [o.to_dict() for o in self.opp_players],
        }


# ─── Scenario Metadata ────────────────────────────────────────────────────────

@dataclass
class ScenarioMeta:
    scenario: str
    title: str
    phase: Literal["In possession", "Out of possession"]
    purpose: str
    takeaway: str

    def to_dict(self) -> dict:
        return {
            "scenario": self.scenario,
            "title": self.title,
            "phase": self.phase,
            "purpose": self.purpose,
            "takeaway": self.takeaway,
        }