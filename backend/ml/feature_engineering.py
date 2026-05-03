import pandas as pd
import numpy as np
from statsbombpy import sb
import warnings
warnings.filterwarnings('ignore')

COMPETITIONS = [
    {"competition_id": 11, "season_id": 4},
    {"competition_id": 11, "season_id": 1},
    {"competition_id": 11, "season_id": 2},
    {"competition_id": 16, "season_id": 4},
    {"competition_id": 16, "season_id": 1},
    {"competition_id": 2,  "season_id": 27},
    {"competition_id": 7,  "season_id": 235},
    {"competition_id": 9,  "season_id": 281},
]


def get_match_stats(match_id: int) -> dict | None:
    """Pull all events for a match and compute raw per-team stats."""
    try:
        events = sb.events(match_id=match_id)
    except Exception as e:
        print(f"  Failed to pull events for match {match_id}: {e}")
        return None

    teams = events['team'].dropna().unique()
    if len(teams) != 2:
        return None

    stats = {}
    for team in teams:
        te = events[events['team'] == team]
        opp = events[events['team'] != team]

        # ── Shots & xG ──────────────────────────────────────────────────────
        shots_df = te[te['type'] == 'Shot']
        shots = len(shots_df)
        goals = len(shots_df[shots_df['shot_outcome'] == 'Goal'])
        xg = float(shots_df['shot_statsbomb_xg'].fillna(0).sum()) \
            if 'shot_statsbomb_xg' in shots_df.columns else 0.0
        xg_per_shot = xg / shots if shots > 0 else 0.0

        # Shot locations — list of (x, y) tuples
        shot_locs = []
        if 'location' in shots_df.columns:
            shot_locs = [
                loc for loc in shots_df['location'].dropna().tolist()
                if isinstance(loc, list) and len(loc) == 2
            ]

        # ── Passes ──────────────────────────────────────────────────────────
        passes_df = te[te['type'] == 'Pass']
        passes_attempted = len(passes_df)
        passes_completed = int(passes_df['pass_outcome'].isna().sum())
        pass_accuracy = passes_completed / passes_attempted \
            if passes_attempted > 0 else 0.0

        key_passes = 0
        if 'pass_shot_assist' in passes_df.columns:
            key_passes += int(passes_df['pass_shot_assist'].fillna(False).sum())
        if 'pass_goal_assist' in passes_df.columns:
            key_passes += int(passes_df['pass_goal_assist'].fillna(False).sum())

        # ── Defensive ───────────────────────────────────────────────────────
        tackles = len(te[te['type'] == 'Tackle'])
        interceptions = len(te[te['type'] == 'Interception'])
        defensive_errors = len(te[te['type'] == 'Error'])
        fouls = len(te[te['type'] == 'Foul Committed'])
        saves = len(te[
            (te['type'] == 'Goal Keeper') &
            (te.get('goalkeeper_type', pd.Series(dtype=str)) == 'Shot Saved')
        ]) if 'goalkeeper_type' in te.columns else 0

        # ── Aerial duels ─────────────────────────────────────────────────────
        if 'duel_type' in te.columns:
            aerial_df = te[te['duel_type'].isin(['Aerial Lost', 'Aerial Won'])]
            aerial_attempted = len(aerial_df)
            aerial_won = len(aerial_df[aerial_df['duel_type'] == 'Aerial Won'])
        else:
            aerial_attempted = 0
            aerial_won = 0
        aerial_win_rate = aerial_won / aerial_attempted \
            if aerial_attempted > 0 else 0.5

        # ── Possession proxy ─────────────────────────────────────────────────
        carries = len(te[te['type'] == 'Carry'])
        possession_proxy = passes_attempted + carries

        opp_passes = len(opp[opp['type'] == 'Pass'])
        opp_carries = len(opp[opp['type'] == 'Carry'])
        opp_possession_proxy = opp_passes + opp_carries

        total_poss = possession_proxy + opp_possession_proxy
        possession_pct = possession_proxy / total_poss \
            if total_poss > 0 else 0.5

        # ── Press intensity ──────────────────────────────────────────────────
        pressures = len(te[te['type'] == 'Pressure'])
        press_intensity = pressures / (opp_possession_proxy + 1)

        # ── Defensive line height ────────────────────────────────────────────
        # Average y-position of defensive events (tackles + interceptions)
        def_events = te[te['type'].isin(['Tackle', 'Interception', 'Clearance'])]
        if 'location' in def_events.columns and len(def_events) > 0:
            locs = def_events['location'].dropna().tolist()
            valid_locs = [l for l in locs if isinstance(l, list) and len(l) == 2]
            def_line = float(np.mean([l[0] for l in valid_locs])) \
                if valid_locs else 50.0
            # Normalise to 0-1 (pitch length 120)
            def_line_norm = round(def_line / 120.0, 3)
        else:
            def_line_norm = 0.5

        # ── Transition speed proxy ───────────────────────────────────────────
        # Ratio of carries in first 5 seconds after a tackle/interception
        # StatsBomb has timestamps — we approximate with carry rate after defensive actions
        defensive_actions = len(te[te['type'].isin(['Tackle', 'Interception'])])
        transition_proxy = min(carries / (defensive_actions + 1), 5.0) / 5.0

        stats[team] = {
            "goals": goals,
            "shots": shots,
            "xg": round(xg, 3),
            "xg_per_shot": round(xg_per_shot, 3),
            "key_passes": key_passes,
            "passes_attempted": passes_attempted,
            "passes_completed": passes_completed,
            "pass_accuracy": round(pass_accuracy, 3),
            "tackles": tackles,
            "interceptions": interceptions,
            "defensive_errors": defensive_errors,
            "fouls": fouls,
            "saves": saves,
            "aerial_won": aerial_won,
            "aerial_attempted": aerial_attempted,
            "aerial_win_rate": round(aerial_win_rate, 3),
            "pressures": pressures,
            "possession_proxy": possession_proxy,
            "opp_possession_proxy": opp_possession_proxy,
            "possession_pct": round(possession_pct, 3),
            "press_intensity": round(press_intensity, 3),
            "def_line_norm": def_line_norm,
            "transition_proxy": round(transition_proxy, 3),
        }

    return stats


def compute_metrics(team_stats: dict, opp_stats: dict, goals_conceded: int) -> dict:
    """Compute 12 normalised indices from raw stats."""

    xg           = team_stats["xg"]
    xg_per_shot  = team_stats["xg_per_shot"]
    shots        = team_stats["shots"]
    key_passes   = team_stats["key_passes"]
    tackles      = team_stats["tackles"]
    errors       = team_stats["defensive_errors"]
    aerial_rate  = team_stats["aerial_win_rate"]
    press_idx    = team_stats["press_intensity"]
    pass_acc     = team_stats["pass_accuracy"]
    poss_pct     = team_stats["possession_pct"]
    def_line     = team_stats["def_line_norm"]
    transition   = team_stats["transition_proxy"]
    opp_xg       = opp_stats["xg"]

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

    # 4. Aerial Dominance Index
    adi = aerial_rate

    # 5. Press Intensity Index
    pii = min(press_idx, 1.0)

    # 6. Passing Stability Index
    psi = pass_acc

    # 7. Possession Share
    pos = poss_pct

    # 8. Transition Speed Index
    tsi = transition

    # 9. Defensive Line Height
    dlh = def_line

    # 10. Match Performance Score
    mps = min(
        (min(xg / 2.5, 1.0) * 0.40) +
        (min(key_passes / 10.0, 1.0) * 0.30) +
        (min(tackles / 20.0, 1.0) * 0.30),
        1.0
    )

    # 11. Discipline Index (higher = more disciplined)
    discipline = max(1.0 - min(team_stats["fouls"] / 20.0, 1.0), 0.0)

    # 12. Chance Creation Rate
    ccr = min(key_passes / 10.0, 1.0)

    return {
        "offensive_output_index":    round(osi, 3),
        "shot_quality_index":        round(sqi, 3),
        "defensive_solidity_index":  round(dsi, 3),
        "aerial_dominance_index":    round(adi, 3),
        "press_intensity_index":     round(pii, 3),
        "passing_stability_index":   round(psi, 3),
        "possession_share":          round(pos, 3),
        "transition_speed_index":    round(tsi, 3),
        "defensive_line_height":     round(dlh, 3),
        "match_performance_score":   round(mps, 3),
        "discipline_index":          round(discipline, 3),
        "chance_creation_rate":      round(ccr, 3),
    }


def build_dataset():
    rows = []

    for comp in COMPETITIONS:
        cid = comp["competition_id"]
        sid = comp["season_id"]
        print(f"\nPulling competition_id={cid} season_id={sid}...")

        try:
            matches = sb.matches(competition_id=cid, season_id=sid)
        except Exception as e:
            print(f"  Could not pull matches: {e}")
            continue

        print(f"  {len(matches)} matches found")

        for _, match in matches.iterrows():
            match_id   = match["match_id"]
            home_team  = match["home_team"]
            away_team  = match["away_team"]
            home_score = match["home_score"]
            away_score = match["away_score"]
            match_date = str(match.get("match_date", ""))

            if pd.isna(home_score) or pd.isna(away_score):
                continue

            result_home = "W" if home_score > away_score else (
                "D" if home_score == away_score else "L"
            )
            result_away = "L" if result_home == "W" else (
                "D" if result_home == "D" else "W"
            )
            outcome_map = {"W": 2, "D": 1, "L": 0}

            print(f"  Processing {match_id}: {home_team} vs {away_team}", end=" ")

            stats = get_match_stats(match_id)
            if stats is None or home_team not in stats or away_team not in stats:
                print("— skipped")
                continue

            home_metrics = compute_metrics(
                stats[home_team], stats[away_team], int(away_score)
            )
            away_metrics = compute_metrics(
                stats[away_team], stats[home_team], int(home_score)
            )

            rows.append({
                "match_id":   match_id,
                "match_date": match_date,
                "team":       home_team,
                "opponent":   away_team,
                "home_away":  1,
                **{f"team_{k}": v for k, v in home_metrics.items()},
                **{f"opp_{k}": v for k, v in away_metrics.items()},
                "outcome": outcome_map[result_home],
            })

            rows.append({
                "match_id":   match_id,
                "match_date": match_date,
                "team":       away_team,
                "opponent":   home_team,
                "home_away":  0,
                **{f"team_{k}": v for k, v in away_metrics.items()},
                **{f"opp_{k}": v for k, v in home_metrics.items()},
                "outcome": outcome_map[result_away],
            })

            print("— done")

    df = pd.DataFrame(rows)
    output_path = "ml/statsbomb_features.csv"
    df.to_csv(output_path, index=False)
    print(f"\nDone. {len(df)} rows saved to {output_path}")
    print(f"\nOutcome distribution:\n{df['outcome'].value_counts()}")
    print(f"\nColumns: {list(df.columns)}")
    print(f"\nSample:\n{df.head(2).to_string()}")
    return df


if __name__ == "__main__":
    build_dataset()