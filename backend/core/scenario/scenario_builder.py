# core/scenario/scenario_builder.py
#
# Orchestrator — given a match_id, team_id and scenario name,
# pulls all required data from DB and delegates to the correct module.
#
# Called by: POST /api/matches/simulate
#
# Returns: List[dict] — array of SimFrame dicts ready for JSON serialisation

from sqlalchemy.orm import Session

from db.models import (
    Match, Player, PlayerSeasonStats, PlayerMatchSnapshot,
    PlayerPositionalAnswers, PlayerAttributeProfile, OppositionProfile,
)
from core.scenario.in_possession import goal_kick, transition, special
from core.scenario.out_of_possession import defensive_shape, opponent_threat


VALID_SCENARIOS = {
    "goal_kick",
    "transition",
    "special",
    "defensive_shape",
    "opponent_threat",
}

TRAIT_ALIASES = {
    # Fullback
    "Gets Forward Often":              "Overlapping Full-Back",
    "Overlaps Winger":                 "Overlapping Full-Back",
    "Stays Back At All Times":         "Stays Back",
    "Conservative Defender":           "Stays Back",

    # CB
    "Brings Ball Out Of Defence":      "Ball Playing Defender",
    "Supports Build-Up":               "Ball Playing Defender",
    "Holds Defensive Line":            "Organises Defence",
    "Clears Danger Early":             "Organises Defence",
    "Physical Defender":               "Aggressive Tackler",
    "Fast Recovery Runner":            "Sweeper CB",
    "Steps Into Midfield":             "Steps Into Midfield",

    # CDM
    "Shields Defence":                 "Deep Playmaker",
    "Breaks Up Play":                  "Ball Winner",
    "Recycles Possession":             "Deep Playmaker",
    "Screens Passing Lanes":           "Sits Between Lines",
    "Dictates Tempo":                  "Deep Playmaker",

    # CM
    "Box To Box Runner":               "Box To Box",
    "Late Runs Into Box":              "Late Run Into Box",
    "Counterpresses Aggressively":     "Counterpressing",
    "High Workrate":                   "Box To Box",
    "Vertical Runner":                 "Runs In Behind",
    "Creative Playmaker":              "Combination Play",
    "Progressive Carrier":             "Progressive Passer",
    "Combination Play Specialist":     "Combination Play",
    "Keeps Possession":                "Deep Playmaker",
    "Roams From Position":             "Drifts Into Channels",

    # CAM
    "Tries Killer Balls Often":        "Through Ball",
    "Through Ball Specialist":         "Through Ball",
    "Finds Space Between Lines":       "Drifts Into Channels",
    "Chance Creator":                  "Combination Play",
    "Arrives In Box":                  "Late Run Into Box",
    "Quick Decision Maker":            "Through Ball",

    # Winger
    "Counterattacking Runner":         "Counterattacking Runner",
    "Runs In Behind":                  "Runs In Behind",
    "Cuts Inside":                     "Cuts Inside",
    "Direct Dribbler":                 "Drifts Central",
    "Shoots Frequently":               "Cuts Inside",

    # ST
    "Target Man Play":                 "Target Man",
    "Aerial Threat":                   "Target Man",
    "Holds Up Ball":                   "Holds Up Play",
    "Physical Forward":                "Target Man",
    "Attacks Far Post":                "Runs In Behind",
    "Presses Defenders Aggressively":  "Presses High",

    # GK
    "Commands Area":                   "Command Of Area",
    "Comfortable With Feet":           "Calm On Ball",
    "Sweeper Keeper":                  "Sweeper Keeper",
    "Organises Defence":               "Organises Defence",

    # Generic
    "Aggressive Presser":              "Presses High",
    "Marks Tightly":                   "Tight Marker",
    "Holds Width":                     "Holds Width",
    "Calm Under Pressure":             "Calm On Ball",
}


def run(
    db,
    match_id: int,
    team_id: int,
    scenario: str,
) -> tuple[list[dict], dict]:
    """Returns (frames, meta) tuple."""
 
    if scenario not in VALID_SCENARIOS:
        raise ValueError(f"Unknown scenario '{scenario}'. Valid: {sorted(VALID_SCENARIOS)}")
 
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise ValueError(f"Match {match_id} not found")
 
    opp_row = (
        db.query(OppositionProfile)
        .filter(OppositionProfile.match_id == match_id)
        .order_by(OppositionProfile.created_at.desc())
        .first()
    )
    opposition = _build_opposition_dict(opp_row)
 
    season_stats = (
        db.query(PlayerSeasonStats)
        .filter(PlayerSeasonStats.team_id == team_id)
        .all()
    )
    player_ids = [s.player_id for s in season_stats]
 
    players_raw = (
        db.query(Player)
        .filter(Player.id.in_(player_ids), Player.is_active == True)
        .all()
    )
    player_map = {p.id: p for p in players_raw}
 
    formation        = match.recommended_formation or "4-3-3"
    defensive_form   = getattr(match, "defensive_formation", None) or formation
 
    xi: list[dict] = []
    for stats in season_stats:
        p = player_map.get(stats.player_id)
        if not p:
            continue
 
        trait_row = (
            db.query(PlayerPositionalAnswers)
            .filter(
                PlayerPositionalAnswers.player_id == p.id,
                PlayerPositionalAnswers.season_id == stats.season_id,
            )
            .first()
        )
 
        if trait_row and trait_row.answers:
            raw    = trait_row.answers
            traits = raw.get("traits", []) if isinstance(raw, dict) else raw
        else:
            traits = []
 
        traits = [TRAIT_ALIASES.get(t, t) for t in traits]
 
        attr_row = (
            db.query(PlayerAttributeProfile)
            .filter(PlayerAttributeProfile.player_id == p.id)
            .first()
        )
        attributes = {}
        if attr_row:
            attributes = {
                k: getattr(attr_row, k, None)
                for k in ["pace","acceleration","stamina","strength","jumping",
                           "heading","passing","finishing","tackling","positioning",
                           "creativity","work_rate","aggression","role_rating","overall_rating"]
            }
            attributes = {k: v for k, v in attributes.items() if v is not None}
 
        snapshots = (
            db.query(PlayerMatchSnapshot)
            .filter(PlayerMatchSnapshot.player_id == p.id)
            .order_by(PlayerMatchSnapshot.id.desc())
            .limit(5)
            .all()
        )
        form_score = _calculate_form(snapshots, p.broad_position)
 
        xi.append({
            "name":              p.name,
            "player_id":         p.id,
            "broad_position":    p.broad_position,
            "specific_position": p.specific_position,
            "jersey_number":     p.jersey_number,
            "traits":            traits,
            "attributes":        attributes,
            "form_score":        form_score,
        })
 
    ROLE_ORDER = {"GK": 0, "DEF": 1, "MID": 2, "FWD": 3}
    xi.sort(key=lambda p: ROLE_ORDER.get(p.get("broad_position", "MID"), 2))
    xi = xi[:11]
 
    def _parse_list(val):
        if isinstance(val, list): return val
        if isinstance(val, str):
            import json
            try: return json.loads(val)
            except: return []
        return []
 
    linkup_pairs     = _parse_list(getattr(match, "linkup_pairs", None) or [])
    tactical_focus   = match.recommended_focus or ""
    matchup_exploits = _parse_list(getattr(match, "matchup_exploits", None) or [])
    matchup_vulns    = _parse_list(getattr(match, "matchup_vulnerabilities", None) or [])
    matchup_notes    = _parse_list(getattr(match, "matchup_general_notes", None) or [])
 
    def _parse_dict(val):
        if isinstance(val, dict): return val
        if isinstance(val, str):
            import json
            try: return json.loads(val)
            except: return {}
        return {}
 
    defensive_shape_dict = _parse_dict(getattr(match, "defensive_shape", None) or {})
 
    # Dispatch — each module now returns frames list directly
    # Meta is built separately via build_metadata()
    if scenario == "goal_kick":
        frames = goal_kick.build(
            xi=xi, formation=formation, linkup_pairs=linkup_pairs,
            opposition=opposition, defensive_shape=defensive_shape_dict,
            matchup_exploits=matchup_exploits,
        )
        meta = goal_kick.metadata(opposition, matchup_exploits)
 
    elif scenario == "transition":
        frames = transition.build(
            xi=xi, formation=formation, linkup_pairs=linkup_pairs,
            opposition=opposition, tactical_focus=tactical_focus,
            matchup_exploits=matchup_exploits,
        )
        meta = transition.metadata(opposition, tactical_focus, matchup_exploits)
 
    elif scenario == "special":
        frames = special.build(
            xi=xi, formation=formation, linkup_pairs=linkup_pairs,
            opposition=opposition, tactical_focus=tactical_focus,
            matchup_exploits=matchup_exploits,
            matchup_vulnerabilities=matchup_vulns,
        )
        meta = special.metadata(tactical_focus, matchup_exploits, matchup_vulns, opposition)
 
    elif scenario == "defensive_shape":
        frames = defensive_shape.build(
            xi=xi, formation=formation, defensive_formation=defensive_form,
            defensive_shape=defensive_shape_dict, opposition=opposition,
        )
        meta = defensive_shape.metadata(defensive_shape_dict, opposition)
 
    elif scenario == "opponent_threat":
        frames = opponent_threat.build(
            xi=xi, formation=formation, defensive_formation=defensive_form,
            defensive_shape=defensive_shape_dict, opposition=opposition,
            matchup_vulnerabilities=matchup_vulns,
            matchup_general_notes=matchup_notes,
        )
        meta = opponent_threat.metadata(opposition, matchup_vulns)
 
    else:
        frames = []
        meta   = {}
 
    return frames, meta


# ── Helpers ───────────────────────────────────────────────────────────────────

def build_metadata(scenario: str, **kwargs) -> dict:
    """Build just the metadata for a scenario without running the full simulation."""
    from core.scenario.in_possession import goal_kick, transition, special
    from core.scenario.out_of_possession import defensive_shape, opponent_threat
    dispatch = {
        "goal_kick":       lambda: goal_kick.metadata(kwargs.get("opposition",{}), kwargs.get("matchup_exploits",[])),
        "transition":      lambda: transition.metadata(kwargs.get("opposition",{}), kwargs.get("tactical_focus",""), kwargs.get("matchup_exploits",[])),
        "special":         lambda: special.metadata(kwargs.get("tactical_focus",""), kwargs.get("matchup_exploits",[]), kwargs.get("matchup_vulnerabilities",[]), kwargs.get("opposition",{})),
        "defensive_shape": lambda: defensive_shape.metadata(kwargs.get("defensive_shape_dict",{}), kwargs.get("opposition",{})),
        "opponent_threat": lambda: opponent_threat.metadata(kwargs.get("opposition",{}), kwargs.get("matchup_vulnerabilities",[])),
    }
    fn = dispatch.get(scenario)
    return fn() if fn else {}

def _build_opposition_dict(opp_row) -> dict:
    if not opp_row:
        return {}
    return {
        "likely_formation":  getattr(opp_row, "likely_formation", None),
        "press_style":       getattr(opp_row, "press_style", None),
        "defensive_line":    getattr(opp_row, "defensive_line", None),
        "playing_style":     getattr(opp_row, "playing_style", None),
        "set_piece_threat":  getattr(opp_row, "set_piece_threat", None),
        "opponent_strength": getattr(opp_row, "opponent_strength", None),
        "attributes":        getattr(opp_row, "attributes", {}) or {},
    }


def _calculate_form(snapshots: list, position: str) -> float:
    """
    Compute a 0–1 form score from the last N match snapshots.
    Position-aware — weights different stats per role.
    """
    if not snapshots:
        return 0.5

    WEIGHTS = {
        "GK":  {"saves": 0.50, "defensive_errors": -0.30, "minutes_played": 0.20},
        "DEF": {"tackles": 0.35, "interceptions": 0.35, "defensive_errors": -0.30},
        "MID": {"key_passes": 0.35, "assists": 0.25, "tackles": 0.20, "goals": 0.20},
        "FWD": {"goals": 0.50, "assists": 0.30, "shots": 0.20},
    }
    pos_weights = WEIGHTS.get(position, WEIGHTS["MID"])

    scores = []
    for snap in snapshots:
        score = 0.5   # base
        for stat, weight in pos_weights.items():
            val = getattr(snap, stat, 0) or 0
            if stat == "defensive_errors":
                score += weight * min(val / 3.0, 1.0)   # negative weight
            elif stat == "minutes_played":
                score += weight * min(val / 90.0, 1.0)
            elif stat == "saves":
                score += weight * min(val / 5.0, 1.0)
            elif stat in ("goals", "assists"):
                score += weight * min(val / 2.0, 1.0)
            elif stat in ("tackles", "interceptions", "key_passes"):
                score += weight * min(val / 5.0, 1.0)
            elif stat == "shots":
                score += weight * min(val / 4.0, 1.0)
        scores.append(max(0.0, min(1.0, score)))

    # Recency weighted — most recent snapshot matters more
    if len(scores) == 1:
        return round(scores[0], 3)
    weights = [0.40, 0.25, 0.18, 0.10, 0.07]
    total = sum(s * w for s, w in zip(scores, weights[:len(scores)]))
    weight_sum = sum(weights[:len(scores)])
    return round(total / weight_sum, 3)