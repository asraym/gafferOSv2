# ml/validate_pipeline.py
#
# Synthetic validation of the tactical engine against held-out StatsBomb data.
# Treats historical matches as if they were live matches coming through the system.
# Stores recommendations and compares against known outcomes.
#
# Usage:
#   cd D:\gafferOS\v2\backend
#   venv\Scripts\activate
#   python ml/validate_pipeline.py
#
# Output:
#   ml/validation_results.csv  — per-match recommendations vs actual outcomes
#   Console summary            — calibration, formation distribution, accuracy

import os
import sys
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

# Make sure backend modules resolve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from statsbombpy import sb
from ml.metrics import compute_metrics
from core.tactical_reasoner import TacticalReasoner
from core.tactical_style import TacticalStyle
from core.tactical_constraints import TacticalConstraints

# ---------------------------------------------------------------------------
# Held-out competitions — NOT in feature_engineering.py COMPETITIONS list
# ---------------------------------------------------------------------------

VALIDATION_COMPETITIONS = [
    {"competition_id": 37, "season_id": 90},   # FA Women's Super League 2020/21
    {"competition_id": 53, "season_id": 106},  # Euro 2020
    {"competition_id": 55, "season_id": 43},   # Copa America 2021
]

OUTCOME_MAP = {2: "Win", 1: "Draw", 0: "Loss"}
RESULT_TO_OUTCOME = {"W": 2, "D": 1, "L": 0}


# ---------------------------------------------------------------------------
# Metric computation from StatsBomb events
# ---------------------------------------------------------------------------

def get_team_stats(match_id: int):
    """
    Pull events and compute raw stats for both teams.
    Reuses the same extraction logic as feature_engineering.py.
    Returns {team_name: stats_dict} or None on failure.
    """
    try:
        from ml.feature_engineering import get_match_stats
        return get_match_stats(match_id)
    except Exception as e:
        print(f"    Stats extraction failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Build engine input from StatsBomb stats
# ---------------------------------------------------------------------------

def build_engine_input(team_stats: dict, opp_stats: dict, venue: str) -> dict:
    """
    Constructs the data dict that TacticalReasoner expects.
    No player data — tactics-only validation.
    """
    team_metrics = compute_metrics(team_stats, opp_stats)
    opp_metrics  = compute_metrics(opp_stats, team_stats)

    return {
        "team_metrics":      team_metrics,
        "opp_metrics":       opp_metrics,
        "data_mode":         "full",
        "home_away":         venue,
        "players":           [],
        "snapshots":         [],
        "opposition":        {},
        "starting_xi":       [],
        "team_fatigue_score": 0.30,   # no player data — use default
        "fatigue_score":     0.30,
        "matchup_vulnerabilities": [],
    }


# ---------------------------------------------------------------------------
# Calibration analysis
# ---------------------------------------------------------------------------

def analyse_calibration(results: pd.DataFrame) -> None:
    """
    Groups predictions by probability bucket and checks actual win rate.
    Well-calibrated model: 60-70% bucket should win ~65% of the time.
    """
    print("\n── Probability Calibration ──")
    print(f"{'Bucket':<15} {'Predicted':>10} {'Actual Win%':>12} {'N':>6}")
    print("-" * 45)

    buckets = [(0.0, 0.4), (0.4, 0.5), (0.5, 0.6), (0.6, 0.7), (0.7, 1.01)]
    for lo, hi in buckets:
        mask   = (results["win_probability"] >= lo) & (results["win_probability"] < hi)
        subset = results[mask]
        if len(subset) == 0:
            continue
        actual_win_rate = (subset["actual_outcome"] == 2).mean()
        label = f"{lo:.0%}–{hi:.0%}" if hi < 1.01 else f"{lo:.0%}+"
        print(
            f"{label:<15} "
            f"{subset['win_probability'].mean():>10.1%} "
            f"{actual_win_rate:>12.1%} "
            f"{len(subset):>6}"
        )


def analyse_formations(results: pd.DataFrame) -> None:
    """
    Shows formation distribution and win rate per recommended formation.
    """
    print("\n── Formation Recommendations ──")
    print(f"{'Formation':<12} {'Count':>6} {'Win%':>8} {'Draw%':>8} {'Loss%':>8}")
    print("-" * 45)

    for formation in sorted(results["recommended_formation"].dropna().unique()):
        subset = results[results["recommended_formation"] == formation]
        n      = len(subset)
        win_r  = (subset["actual_outcome"] == 2).mean()
        draw_r = (subset["actual_outcome"] == 1).mean()
        loss_r = (subset["actual_outcome"] == 0).mean()
        print(
            f"{formation:<12} {n:>6} "
            f"{win_r:>8.1%} {draw_r:>8.1%} {loss_r:>8.1%}"
        )


def analyse_coherence(results: pd.DataFrame) -> None:
    """
    Checks whether high coherence recommendations produce better outcomes.
    This is the key signal for whether TacticalConstraints is useful.
    """
    if "coherence_score" not in results.columns:
        return

    print("\n── Coherence Score vs Outcome ──")
    print(f"{'Coherence':<15} {'Win%':>8} {'N':>6}")
    print("-" * 30)

    buckets = [(0.0, 0.6), (0.6, 0.8), (0.8, 1.01)]
    for lo, hi in buckets:
        mask   = (results["coherence_score"] >= lo) & (results["coherence_score"] < hi)
        subset = results[mask]
        if len(subset) == 0:
            continue
        win_rate = (subset["actual_outcome"] == 2).mean()
        label    = f"{lo:.0%}–{hi:.0%}" if hi < 1.01 else f"{lo:.0%}+"
        print(f"{label:<15} {win_rate:>8.1%} {len(subset):>6}")


def analyse_accuracy(results: pd.DataFrame) -> None:
    """
    At high confidence (>60% win probability), how often does the team win?
    """
    print("\n── High Confidence Accuracy ──")
    high_conf = results[results["win_probability"] > 0.60]
    if len(high_conf) == 0:
        print("  No high-confidence predictions found.")
        return
    accuracy = (high_conf["actual_outcome"] == 2).mean()
    print(f"  Matches where win prob > 60%: {len(high_conf)}")
    print(f"  Actual win rate:              {accuracy:.1%}")
    print(f"  (Expected if calibrated:      ~65%)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_validation():
    reasoner    = TacticalReasoner()
    style_deriv = TacticalStyle()
    constraints = TacticalConstraints()

    rows = []

    for comp in VALIDATION_COMPETITIONS:
        cid = comp["competition_id"]
        sid = comp["season_id"]
        print(f"\nValidating competition_id={cid} season_id={sid}...")

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

            if pd.isna(home_score) or pd.isna(away_score):
                continue

            result_home = "W" if home_score > away_score else (
                "D" if home_score == away_score else "L"
            )
            result_away = "L" if result_home == "W" else (
                "D" if result_home == "D" else "W"
            )

            print(f"  {match_id}: {home_team} vs {away_team}", end=" ")

            stats = get_team_stats(match_id)
            if stats is None or home_team not in stats or away_team not in stats:
                print("— skipped")
                continue

            for team, opp_team, venue, result in [
                (home_team, away_team, "home", result_home),
                (away_team, home_team, "away", result_away),
            ]:
                try:
                    data = build_engine_input(
                        stats[team], stats[opp_team], venue
                    )
                    data = reasoner.reason(data)

                    # Style + coherence (no squad — will be sparse but structural)
                    data = style_deriv.derive(data)
                    data = constraints.validate(data)

                    rows.append({
                        "match_id":              match_id,
                        "team":                  team,
                        "opponent":              opp_team,
                        "venue":                 venue,
                        "actual_result":         result,
                        "actual_outcome":        RESULT_TO_OUTCOME[result],
                        "win_probability":       data.get("win_probability"),
                        "draw_probability":      data.get("draw_probability"),
                        "loss_probability":      data.get("loss_probability"),
                        "recommended_formation": data.get("recommended_formation"),
                        "press_intensity":       data.get("press_intensity"),
                        "defensive_line":        data.get("defensive_line"),
                        "tactical_focus":        data.get("tactical_focus"),
                        "squad_style":           data.get("squad_style", {}).get("style"),
                        "coherence_score":       data.get("coherence_score"),
                        "data_mode":             data.get("data_mode"),
                    })
                except Exception as e:
                    print(f"\n    Engine failed for {team}: {e}")
                    continue

            print("— done")

    if not rows:
        print("\nNo results collected. Check competition IDs are valid.")
        return

    results = pd.DataFrame(rows)

    output_path = "ml/validation_results.csv"
    results.to_csv(output_path, index=False)
    print(f"\n{len(results)} rows saved to {output_path}")

    # Summary
    print("\n" + "═" * 50)
    print("VALIDATION SUMMARY")
    print("═" * 50)
    print(f"Total predictions: {len(results)}")
    print(f"Competitions:      {len(VALIDATION_COMPETITIONS)}")
    print(f"\nActual outcome distribution:")
    for outcome, label in OUTCOME_MAP.items():
        n = (results["actual_outcome"] == outcome).sum()
        print(f"  {label}: {n} ({n/len(results):.1%})")

    analyse_calibration(results)
    analyse_formations(results)
    analyse_coherence(results)
    analyse_accuracy(results)

    print("\n" + "═" * 50)
    print("What to look for:")
    print("  Calibration   — predicted % should match actual win rate per bucket")
    print("  Formations    — no single formation should dominate (check #9 default mode)")
    print("  Coherence     — higher coherence should correlate with better outcomes")
    print("  High conf     — >60% win prob should win ~65% of the time")
    print("═" * 50)


if __name__ == "__main__":
    run_validation()