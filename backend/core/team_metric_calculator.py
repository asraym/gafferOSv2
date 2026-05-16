from collections import defaultdict
from ml.metrics import compute_metrics

TEAM_METRICS = [
    "offensive_output_index",
    "shot_quality_index",
    "defensive_solidity_index",
    "passing_stability_index",
    "possession_share",
    "discipline_index",
    "defensive_line_height",
]

METRIC_DEFAULTS = {
    "offensive_output_index":   0.38,
    "shot_quality_index":       0.32,
    "defensive_solidity_index": 0.55,
    "passing_stability_index":  0.78,
    "possession_share":         0.50,
    "discipline_index":         0.65,
    "defensive_line_height":    0.50,
}


class TeamMetricCalculator:
    """
    Computes the 7 model metrics from DB data.

    Priority order per metric:
    1. match_team_stats row (full mode — from CV pipeline)
    2. Aggregated from player_match_snapshots (basic mode)
    3. Population average fallback (default mode)

    Uses the same compute_metrics() formula as training
    to guarantee training/inference consistency.
    """

    def calculate(self, data: dict) -> dict:
        team_stats = data.get("team_stats")
        snapshots  = data.get("snapshots", [])
        opposition = data.get("opposition")

        source = "basic"  # fix #6 — initialise before any conditional

        team_metrics, source = self._compute_team_metrics(team_stats, snapshots, source)
        opp_metrics, _       = self._compute_opp_metrics(opposition)

        if source == "full":
            data_mode = "full"
        elif snapshots:
            data_mode = "basic"
        else:
            data_mode = "default"

        missing = []
        if source != "full":
            missing.append("match_team_stats (possession, pressures, transition, line height)")
        if not snapshots:
            missing.append("player match snapshots (no match footage processed yet)")
        if not opposition:
            missing.append("opposition profile (no scouting notes submitted)")

        data["team_metrics"]   = team_metrics
        data["opp_metrics"]    = opp_metrics
        data["data_mode"]      = data_mode
        data["missing_fields"] = missing
        return data

    def _compute_team_metrics(self, team_stats: dict, snapshots: list, source: str) -> tuple:
        if not snapshots:
            return dict(METRIC_DEFAULTS), "default"

        n_matches = self._estimate_match_count(snapshots)

        total_shots    = sum(s.get("shots", 0) for s in snapshots)
        total_kp       = sum(s.get("key_passes", 0) for s in snapshots)
        total_goals    = sum(s.get("goals", 0) for s in snapshots)
        total_tackles  = sum(s.get("tackles", 0) for s in snapshots)
        total_intercep = sum(s.get("interceptions", 0) for s in snapshots)
        total_errors   = sum(s.get("defensive_errors", 0) for s in snapshots)
        total_fouls    = sum(s.get("fouls_committed", 0) for s in snapshots)
        total_passes_c = sum(s.get("passes_completed", 0) for s in snapshots)
        total_passes_a = sum(s.get("passes_attempted", 0) for s in snapshots)

        # Build a stat dict matching the shape compute_metrics() expects
        # so the exact same formula runs at inference as at training.
        # xg is unavailable from snapshots — use goals/shots proxy.
        shots_safe = max(total_shots, 1)
        xg_proxy        = total_goals * 0.8           # rough xG proxy
        xg_per_shot     = xg_proxy / shots_safe
        pass_acc        = total_passes_c / max(total_passes_a, 1)

        # Possession share — fix #5
        # Estimate opposition passes as league average minus ours per match.
        # 400 total pass actions per match is a reasonable baseline.
        est_total_passes = n_matches * 400.0
        est_opp_passes   = max(est_total_passes - total_passes_a, 1.0)
        possession_pct   = total_passes_a / (total_passes_a + est_opp_passes)

        # Defensive line height — use team_stats if available, else default
        def_line_norm = METRIC_DEFAULTS["defensive_line_height"]
        if team_stats and team_stats.get("defensive_line_height") is not None:
            def_line_norm = team_stats["defensive_line_height"]
            source = "full"

        # Possession from team_stats overrides proxy when available
        if team_stats and team_stats.get("possession_pct") is not None:
            possession_pct = team_stats["possession_pct"] / 100.0
            source = "full"

        team_stat_dict = {
            "xg":               xg_proxy,
            "xg_per_shot":      xg_per_shot,
            "shots":            total_shots,
            "key_passes":       total_kp,
            "tackles":          total_tackles,
            "interceptions":    total_intercep,
            "defensive_errors": total_errors,
            "pass_accuracy":    pass_acc,
            "possession_pct":   possession_pct,
            "def_line_norm":    def_line_norm,
            "fouls":            total_fouls,
        }

        # opp_stats for DSI — we use opp_metrics defaults unless team_stats has opp xg
        # For basic mode we don't have opposition xg, so opp_xg defaults to 0
        # which means DSI will be optimistic. Acceptable — flag in missing_fields.
        opp_stat_dict = {"xg": 0.0}

        metrics = compute_metrics(team_stat_dict, opp_stat_dict)
        return metrics, source

    def _compute_opp_metrics(self, opposition: dict) -> tuple:
        """
        Derive opposition metrics from parsed scouting notes.
        Uses additive adjustments from baseline — fix #15.
        """
        metrics = dict(METRIC_DEFAULTS)

        if not opposition:
            return metrics, "default"

        style = (opposition.get("playing_style") or "").lower()
        press = (opposition.get("press_style") or "").lower()
        line  = (opposition.get("defensive_line") or "").lower()

        # Additive adjustments from baseline — never overwrite, always adjust.
        # Multiple styles stack correctly.
        if "possession" in style or "tiki" in style:
            metrics["possession_share"]        = round(metrics["possession_share"] + 0.08, 3)
            metrics["passing_stability_index"] = round(metrics["passing_stability_index"] + 0.04, 3)
        if "direct" in style or "long ball" in style:
            metrics["possession_share"]        = round(metrics["possession_share"] - 0.08, 3)
            metrics["passing_stability_index"] = round(metrics["passing_stability_index"] - 0.10, 3)

        if "high press" in press:
            metrics["offensive_output_index"]   = round(metrics["offensive_output_index"] + 0.17, 3)
            metrics["defensive_solidity_index"] = round(metrics["defensive_solidity_index"] + 0.05, 3)
        if "low block" in press or "sit deep" in press:
            metrics["defensive_solidity_index"] = round(metrics["defensive_solidity_index"] + 0.15, 3)
            metrics["offensive_output_index"]   = round(metrics["offensive_output_index"] - 0.08, 3)

        if "high" in line:
            metrics["defensive_line_height"] = round(metrics["defensive_line_height"] + 0.20, 3)
        if "deep" in line or "low" in line:
            metrics["defensive_line_height"] = round(metrics["defensive_line_height"] - 0.20, 3)

        # Clamp all to [0, 1]
        for k in metrics:
            metrics[k] = round(max(0.0, min(1.0, metrics[k])), 3)

        return metrics, "opposition_notes"

    def _estimate_match_count(self, snapshots: list) -> int:
        if not snapshots:
            return 1
        return max(len(set(s["match_id"] for s in snapshots)), 1)