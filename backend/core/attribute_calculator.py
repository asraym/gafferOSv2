"""
Attribute Calculator for GafferOS v2.
Converts physical test data + CV season stats into FM-style 1-20 attribute ratings.

Physical attributes → from beep test, sprint, jump, height, weight
Technical attributes → from player_season_stats (CV pipeline data)
All ratings: 1-20 scale.
"""


def _clamp(value: float, min_val: float = 1.0, max_val: float = 20.0) -> float:
    return round(max(min_val, min(max_val, value)), 1)


def _per90(stat: float, minutes: float) -> float:
    if minutes <= 0:
        return 0.0
    return stat / (minutes / 90.0)


# ─────────────────────────────────────────────
# PHYSICAL ATTRIBUTE CALCULATORS
# ─────────────────────────────────────────────

def calc_pace(sprint_time_20m: float) -> float:
    """Lower sprint time = higher pace. Benchmarks for semi-pro level."""
    if sprint_time_20m is None:
        return None
    if sprint_time_20m <= 2.8:  return 20.0
    if sprint_time_20m <= 2.9:  return 18.5
    if sprint_time_20m <= 3.0:  return 17.0
    if sprint_time_20m <= 3.1:  return 15.5
    if sprint_time_20m <= 3.2:  return 14.0
    if sprint_time_20m <= 3.3:  return 12.5
    if sprint_time_20m <= 3.4:  return 11.0
    if sprint_time_20m <= 3.5:  return 9.5
    if sprint_time_20m <= 3.6:  return 8.0
    if sprint_time_20m <= 3.7:  return 6.5
    if sprint_time_20m <= 3.8:  return 5.0
    return 3.0


def calc_acceleration(sprint_time_20m: float) -> float:
    """
    Acceleration uses same input as pace but different curve.
    Short burst speed matters more than top end — slightly harsher thresholds.
    """
    if sprint_time_20m is None:
        return None
    if sprint_time_20m <= 2.8:  return 19.0
    if sprint_time_20m <= 2.9:  return 17.5
    if sprint_time_20m <= 3.0:  return 16.0
    if sprint_time_20m <= 3.1:  return 14.0
    if sprint_time_20m <= 3.2:  return 13.0
    if sprint_time_20m <= 3.3:  return 11.0
    if sprint_time_20m <= 3.4:  return 10.0
    if sprint_time_20m <= 3.5:  return 8.0
    if sprint_time_20m <= 3.6:  return 7.0
    if sprint_time_20m <= 3.7:  return 5.5
    if sprint_time_20m <= 3.8:  return 4.0
    return 3.0


def calc_stamina(beep_test_level: float) -> float:
    """Beep test level → stamina. Standard 20m shuttle run scale."""
    if beep_test_level is None:
        return None
    if beep_test_level >= 13.0: return 20.0
    if beep_test_level >= 12.5: return 18.5
    if beep_test_level >= 12.0: return 17.0
    if beep_test_level >= 11.5: return 15.5
    if beep_test_level >= 11.0: return 14.0
    if beep_test_level >= 10.5: return 12.5
    if beep_test_level >= 10.0: return 11.0
    if beep_test_level >= 9.5:  return 9.5
    if beep_test_level >= 9.0:  return 8.0
    if beep_test_level >= 8.5:  return 6.5
    if beep_test_level >= 8.0:  return 5.0
    return 3.0


def calc_jumping(vertical_jump_cm: float) -> float:
    """Vertical jump height → jumping attribute."""
    if vertical_jump_cm is None:
        return None
    if vertical_jump_cm >= 70:  return 20.0
    if vertical_jump_cm >= 67:  return 18.5
    if vertical_jump_cm >= 65:  return 17.0
    if vertical_jump_cm >= 62:  return 15.5
    if vertical_jump_cm >= 60:  return 14.0
    if vertical_jump_cm >= 57:  return 12.5
    if vertical_jump_cm >= 55:  return 11.0
    if vertical_jump_cm >= 52:  return 9.5
    if vertical_jump_cm >= 50:  return 8.0
    if vertical_jump_cm >= 47:  return 6.5
    if vertical_jump_cm >= 45:  return 5.0
    return 3.0


def calc_strength(weight_kg: float, beep_test_level: float) -> float:
    """
    Strength = mass + fitness combined.
    Heavier + higher beep = physically dominant.
    Weight normalised to 90kg (heavy semi-pro), beep to 13.
    """
    if weight_kg is None or beep_test_level is None:
        return None
    weight_score = min(weight_kg / 90.0, 1.0)
    beep_score   = min(beep_test_level / 13.0, 1.0)
    raw          = (weight_score * 0.5 + beep_score * 0.5) * 20.0
    return _clamp(raw)


def calc_heading(vertical_jump_cm: float, height_cm: float) -> float:
    """
    Heading = jump reach + height combined.
    A tall player who jumps well dominates aerially.
    """
    if vertical_jump_cm is None or height_cm is None:
        return None
    jump_score   = min(vertical_jump_cm / 70.0, 1.0)
    height_score = min(height_cm / 195.0, 1.0)
    raw          = (jump_score * 0.6 + height_score * 0.4) * 20.0
    return _clamp(raw)


# ─────────────────────────────────────────────
# TECHNICAL ATTRIBUTE CALCULATORS (CV data)
# ─────────────────────────────────────────────

def calc_finishing(goals: float, shots: float, minutes: float) -> float:
    """
    Finishing = goals per 90 + shot accuracy combined.
    1 goal/90 = excellent. Shot accuracy 33%+ = good.
    """
    if minutes <= 0:
        return None
    goals_p90    = _per90(goals, minutes)
    shot_acc     = (goals / max(shots, 1))
    goals_norm   = min(goals_p90 / 1.0, 1.0)
    acc_norm     = min(shot_acc / 0.33, 1.0)
    raw          = (goals_norm * 0.6 + acc_norm * 0.4) * 20.0
    return _clamp(raw)


def calc_passing(passes_completed: float, passes_attempted: float) -> float:
    """Pass completion rate → passing attribute."""
    if passes_attempted <= 0:
        return None
    completion = passes_completed / passes_attempted
    raw        = min(completion / 0.90, 1.0) * 20.0   # 90% completion = 20
    return _clamp(raw)


def calc_creativity(key_passes: float, assists: float, minutes: float) -> float:
    """
    Creativity = key passes per 90 + assists per 90.
    3 key passes/90 = excellent creator.
    """
    if minutes <= 0:
        return None
    kp_p90   = _per90(key_passes, minutes)
    ast_p90  = _per90(assists, minutes)
    kp_norm  = min(kp_p90 / 3.0, 1.0)
    ast_norm = min(ast_p90 / 0.5, 1.0)
    raw      = (kp_norm * 0.65 + ast_norm * 0.35) * 20.0
    return _clamp(raw)


def calc_tackling(tackles: float, interceptions: float, minutes: float) -> float:
    """
    Tackling = tackles + interceptions per 90.
    6 defensive actions/90 = excellent.
    """
    if minutes <= 0:
        return None
    def_p90 = _per90(tackles + interceptions, minutes)
    raw     = min(def_p90 / 6.0, 1.0) * 20.0
    return _clamp(raw)


def calc_positioning(interceptions: float, defensive_errors: float, minutes: float) -> float:
    """
    Positioning = interceptions per 90 (reads the game)
    penalised by defensive errors per 90.
    """
    if minutes <= 0:
        return None
    int_p90   = _per90(interceptions, minutes)
    err_p90   = _per90(defensive_errors, minutes)
    int_norm  = min(int_p90 / 3.0, 1.0)
    err_pen   = min(err_p90 / 2.0, 1.0)
    raw       = (int_norm * 0.7 + (1.0 - err_pen) * 0.3) * 20.0
    return _clamp(raw)


def calc_work_rate(tackles: float, key_passes: float, shots: float, minutes: float) -> float:
    """
    Work rate = total actions per 90 across all phases.
    High in all three = box to box engine.
    """
    if minutes <= 0:
        return None
    total_p90 = _per90(tackles + key_passes + shots, minutes)
    raw       = min(total_p90 / 10.0, 1.0) * 20.0
    return _clamp(raw)


def calc_aggression(tackles: float, fouls: float, minutes: float) -> float:
    """
    Aggression = tackling volume + foul rate combined.
    High tackles + some fouls = aggressive player.
    """
    if minutes <= 0:
        return None
    tck_p90  = _per90(tackles, minutes)
    foul_p90 = _per90(fouls, minutes)
    tck_norm = min(tck_p90 / 5.0, 1.0)
    foul_norm = min(foul_p90 / 3.0, 1.0)
    raw      = (tck_norm * 0.6 + foul_norm * 0.4) * 20.0
    return _clamp(raw)


# ─────────────────────────────────────────────
# MAIN CALCULATOR
# ─────────────────────────────────────────────

def calculate_attributes(player: dict, physical: dict) -> dict:
    """
    Takes a player dict (from DB, with season stats) and
    a physical dict (from player_physical_attributes row).
    Returns full attribute profile as 1-20 ratings.
    None means insufficient data to calculate.

    player keys expected:
        season_goals, season_assists, season_shots, season_key_passes,
        season_passes_completed, season_passes_attempted, season_tackles,
        season_interceptions, season_defensive_errors, season_saves,
        season_matches_played
    
    physical keys expected:
        height_cm, weight_kg, beep_test_level,
        sprint_time_20m, vertical_jump_cm
    """
    mins = player.get("season_matches_played", 0) * 90  # estimate total minutes

    # Physical
    pace         = calc_pace(physical.get("sprint_time_20m"))
    acceleration = calc_acceleration(physical.get("sprint_time_20m"))
    stamina      = calc_stamina(physical.get("beep_test_level"))
    jumping      = calc_jumping(physical.get("vertical_jump_cm"))
    strength     = calc_strength(physical.get("weight_kg"), physical.get("beep_test_level"))
    heading      = calc_heading(physical.get("vertical_jump_cm"), physical.get("height_cm"))

    # Technical
    finishing    = calc_finishing(
        player.get("season_goals", 0),
        player.get("season_shots", 0),
        mins
    )
    passing      = calc_passing(
        player.get("season_passes_completed", 0),
        player.get("season_passes_attempted", 0)
    )
    creativity   = calc_creativity(
        player.get("season_key_passes", 0),
        player.get("season_assists", 0),
        mins
    )
    tackling     = calc_tackling(
        player.get("season_tackles", 0),
        player.get("season_interceptions", 0),
        mins
    )
    positioning  = calc_positioning(
        player.get("season_interceptions", 0),
        player.get("season_defensive_errors", 0),
        mins
    )
    work_rate    = calc_work_rate(
        player.get("season_tackles", 0),
        player.get("season_key_passes", 0),
        player.get("season_shots", 0),
        mins
    )
    aggression   = calc_aggression(
        player.get("season_tackles", 0),
        0,   # fouls not in season stats yet — will improve when CV adds it
        mins
    )

    return {
        # Physical
        "pace":          pace,
        "acceleration":  acceleration,
        "stamina":       stamina,
        "jumping":       jumping,
        "strength":      strength,
        "heading":       heading,
        # Technical
        "finishing":     finishing,
        "passing":       passing,
        "creativity":    creativity,
        "tackling":      tackling,
        "positioning":   positioning,
        "work_rate":     work_rate,
        "aggression":    aggression,
    }


def calculate_role_rating(attributes: dict, specific_position: str) -> float:
    """
    Calculates a 1-20 role suitability rating for a player's specific position.
    Weights are position-specific — a CB's heading matters more than a ST's.
    None attributes are skipped and weights redistributed.
    """
    ROLE_WEIGHTS = {
        "GK":  {"stamina": 0.2, "jumping": 0.2, "strength": 0.15,
                "positioning": 0.25, "aggression": 0.1, "passing": 0.1},
        "CB":  {"heading": 0.2, "tackling": 0.2, "strength": 0.15,
                "positioning": 0.2, "pace": 0.1, "passing": 0.1, "aggression": 0.05},
        "RB":  {"pace": 0.2, "stamina": 0.2, "tackling": 0.15,
                "crossing": 0.15, "positioning": 0.15, "acceleration": 0.15},
        "LB":  {"pace": 0.2, "stamina": 0.2, "tackling": 0.15,
                "crossing": 0.15, "positioning": 0.15, "acceleration": 0.15},
        "RWB": {"pace": 0.25, "stamina": 0.2, "acceleration": 0.15,
                "tackling": 0.1, "creativity": 0.15, "work_rate": 0.15},
        "LWB": {"pace": 0.25, "stamina": 0.2, "acceleration": 0.15,
                "tackling": 0.1, "creativity": 0.15, "work_rate": 0.15},
        "CDM": {"tackling": 0.25, "positioning": 0.2, "stamina": 0.15,
                "passing": 0.2, "strength": 0.1, "aggression": 0.1},
        "CM":  {"passing": 0.2, "stamina": 0.2, "work_rate": 0.2,
                "creativity": 0.15, "tackling": 0.15, "pace": 0.1},
        "CAM": {"creativity": 0.3, "passing": 0.2, "finishing": 0.2,
                "pace": 0.15, "work_rate": 0.15},
        "RM":  {"pace": 0.25, "acceleration": 0.2, "creativity": 0.2,
                "stamina": 0.15, "finishing": 0.1, "tackling": 0.1},
        "LM":  {"pace": 0.25, "acceleration": 0.2, "creativity": 0.2,
                "stamina": 0.15, "finishing": 0.1, "tackling": 0.1},
        "RW":  {"pace": 0.25, "acceleration": 0.2, "finishing": 0.2,
                "creativity": 0.2, "stamina": 0.15},
        "LW":  {"pace": 0.25, "acceleration": 0.2, "finishing": 0.2,
                "creativity": 0.2, "stamina": 0.15},
        "ST":  {"finishing": 0.3, "pace": 0.2, "heading": 0.15,
                "strength": 0.15, "acceleration": 0.1, "work_rate": 0.1},
        "CF":  {"finishing": 0.25, "creativity": 0.25, "pace": 0.15,
                "work_rate": 0.15, "acceleration": 0.1, "heading": 0.1},
        "SS":  {"creativity": 0.3, "finishing": 0.2, "pace": 0.15,
                "passing": 0.15, "work_rate": 0.2},
    }

    weights = ROLE_WEIGHTS.get(specific_position, {})
    if not weights:
        return None

    total_weight = 0.0
    weighted_sum = 0.0
    for attr, weight in weights.items():
        val = attributes.get(attr)
        if val is not None:
            weighted_sum += val * weight
            total_weight += weight

    if total_weight == 0:
        return None

    # Redistribute for missing attributes
    raw = weighted_sum / total_weight
    return _clamp(raw)


def calculate_overall_rating(attributes: dict, role_rating: float) -> float:
    """
    Overall rating = role rating (60%) + average of all available attributes (40%).
    Gives a single number that reflects both positional suitability and general ability.
    """
    available = [v for v in attributes.values() if v is not None]
    if not available:
        return role_rating

    avg_all = sum(available) / len(available)
    if role_rating is None:
        return _clamp(avg_all)

    raw = role_rating * 0.6 + avg_all * 0.4
    return _clamp(raw)