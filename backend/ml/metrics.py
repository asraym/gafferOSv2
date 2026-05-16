# ml/metrics.py
# Single source of truth for metric formulas.
# Imported by both feature_engineering.py (training) and
# team_metric_calculator.py (inference) to guarantee consistency.

def compute_metrics(team_stats: dict, opp_stats: dict) -> dict:
    """
    Compute 7 normalised indices from raw match stats.
    Both team_stats and opp_stats must contain the keys
    produced by feature_engineering.get_match_stats().

    Returns only the 7 TEAM_METRICS used by the model.
    The 5 dropped metrics (aerial, press, transition,
    match_performance_score, chance_creation_rate) are
    excluded — they had extraction issues in StatsBomb data
    and are not in the trained model's feature set.
    """
    xg          = team_stats.get("xg", 0.0)
    xg_per_shot = team_stats.get("xg_per_shot", 0.0)
    shots       = team_stats.get("shots", 0)
    key_passes  = team_stats.get("key_passes", 0)
    tackles     = team_stats.get("tackles", 0)
    errors      = team_stats.get("defensive_errors", 0)
    pass_acc    = team_stats.get("pass_accuracy", 0.0)
    poss_pct    = team_stats.get("possession_pct", 0.5)
    def_line    = team_stats.get("def_line_norm", 0.5)
    fouls       = team_stats.get("fouls", 0)
    opp_xg      = opp_stats.get("xg", 0.0)

    # 1. Offensive Output Index
    osi = min(
        (min(xg / 2.5, 1.0) * 0.50) +
        (min(shots / 20.0, 1.0) * 0.25) +
        (min(key_passes / 10.0, 1.0) * 0.25),
        1.0
    )

    # 2. Shot Quality Index
    sqi = min(xg_per_shot / 0.2, 1.0)

    # 3. Defensive Solidity Index
    dsi = max(
        1.0 - (
            (min(opp_xg / 2.5, 1.0) * 0.60) +
            (min(errors / 5.0, 1.0) * 0.40)
        ),
        0.0
    )

    # 4. Passing Stability Index
    psi = min(pass_acc, 1.0)

    # 5. Possession Share
    pos = min(poss_pct, 1.0)

    # 6. Discipline Index
    discipline = max(1.0 - min(fouls / 20.0, 1.0), 0.0)

    # 7. Defensive Line Height
    dlh = min(def_line, 1.0)

    return {
        "offensive_output_index":   round(osi, 3),
        "shot_quality_index":       round(sqi, 3),
        "defensive_solidity_index": round(dsi, 3),
        "passing_stability_index":  round(psi, 3),
        "possession_share":         round(pos, 3),
        "discipline_index":         round(discipline, 3),
        "defensive_line_height":    round(dlh, 3),
    }