from collections import defaultdict


# These 7 must match the TEAM_METRICS order in the pkl exactly.
TEAM_METRICS = [
    "offensive_output_index",
    "shot_quality_index",
    "defensive_solidity_index",
    "passing_stability_index",
    "possession_share",
    "discipline_index",
    "defensive_line_height",
]

# Population averages used as fallback when a metric can't be computed.
# Derived from StatsBomb EDA — roughly mid-table values.
METRIC_DEFAULTS = {
    "offensive_output_index": 0.38,
    "shot_quality_index":     0.32,
    "defensive_solidity_index": 0.55,
    "passing_stability_index": 0.78,
    "possession_share":        0.50,
    "discipline_index":        0.65,
    "defensive_line_height":   0.50,
}


class TeamMetricCalculator:
    """
    Computes the 7 model metrics from DB data.

    Priority order per metric:
    1. match_team_stats row (most accurate — from CV pipeline)
    2. Aggregated from player_match_snapshots (reasonable estimate)
    3. Population average fallback (flags as basic mode)
    """

    def calculate(self, data: dict) -> dict:
        """
        data: the dict returned by MatchDataFetcher.fetch()
        Returns: data enriched with 'team_metrics', 'opp_metrics',
                 'data_mode', and 'missing_fields' keys.
        """
        team_stats = data.get("team_stats")       # match_team_stats row or None
        snapshots  = data.get("snapshots", [])
        opposition = data.get("opposition")

        team_metrics, team_source = self._compute_team_metrics(team_stats, snapshots)
        opp_metrics,  opp_source  = self._compute_opp_metrics(opposition)

        # Decide data mode
        if team_source == "full" and len(snapshots) > 0:
            data_mode = "full"
        elif len(snapshots) > 0:
            data_mode = "basic"
        else:
            data_mode = "default"

        missing = []
        if team_source != "full":
            missing.append("match_team_stats (possession, pressures, transition, line height)")
        if not snapshots:
            missing.append("player match snapshots (no match footage processed yet)")
        if not opposition:
            missing.append("opposition profile (no scouting notes submitted)")

        data["team_metrics"]  = team_metrics
        data["opp_metrics"]   = opp_metrics
        data["data_mode"]     = data_mode
        data["missing_fields"] = missing
        return data

    # ------------------------------------------------------------------
    # Team metrics
    # ------------------------------------------------------------------

    def _compute_team_metrics(self, team_stats: dict, snapshots: list) -> tuple:
        """Returns (metrics_dict, source_label)."""
        metrics = {}

        # Group snapshots by player for per-player aggregation
        by_player = defaultdict(list)
        for s in snapshots:
            by_player[s["player_id"]].append(s)

        n_matches = self._estimate_match_count(snapshots)

        # --- offensive_output_index ---
        # Full: needs xG (not in our schema yet) + shots + key_passes from team_stats
        # Basic: shots + key_passes from snapshots
        total_shots     = sum(s["shots"] for s in snapshots)
        total_kp        = sum(s["key_passes"] for s in snapshots)
        shots_norm      = min(total_shots / max(n_matches * 15.0, 1), 1.0)
        kp_norm         = min(total_kp / max(n_matches * 10.0, 1), 1.0)
        metrics["offensive_output_index"] = round(shots_norm * 0.6 + kp_norm * 0.4, 3)

        # --- shot_quality_index ---
        # Proxy: shots on target / shots (we don't have xG)
        # When we get xG from CV, this upgrades automatically
        total_shots_all = max(total_shots, 1)
        # No shots_on_target in snapshots schema currently — use goals as proxy
        total_goals = sum(s["goals"] for s in snapshots)
        metrics["shot_quality_index"] = round(
            min(total_goals / max(total_shots_all * 0.3, 1), 1.0), 3
        )

        # --- defensive_solidity_index ---
        total_tackles       = sum(s["tackles"] for s in snapshots)
        total_interceptions = sum(s["interceptions"] for s in snapshots)
        total_errors        = sum(s["defensive_errors"] for s in snapshots)
        defensive_actions   = min((total_tackles + total_interceptions) / max(n_matches * 20.0, 1), 1.0)
        error_penalty       = min(total_errors / max(n_matches * 5.0, 1), 1.0)
        metrics["defensive_solidity_index"] = round(
            defensive_actions * 0.7 + (1.0 - error_penalty) * 0.3, 3
        )

        # --- passing_stability_index ---
        total_completed  = sum(s["passes_completed"] for s in snapshots)
        total_attempted  = sum(s["passes_attempted"] for s in snapshots)
        if total_attempted > 0:
            metrics["passing_stability_index"] = round(
                min(total_completed / total_attempted, 1.0), 3
            )
        else:
            metrics["passing_stability_index"] = METRIC_DEFAULTS["passing_stability_index"]

        # --- possession_share ---
        if team_stats and team_stats.get("possession_pct") is not None:
            metrics["possession_share"] = round(team_stats["possession_pct"] / 100.0, 3)
            source = "full"
        else:
            # Pass volume proxy: our passes / assumed total passes in game
            # crude but directional
            metrics["possession_share"] = round(
                min(total_completed / max(n_matches * 400.0, 1), 1.0), 3
            )
            source = "basic"

        # --- discipline_index ---
        total_fouls = sum(s["fouls_committed"] for s in snapshots)
        fouls_per_match = total_fouls / max(n_matches, 1)
        metrics["discipline_index"] = round(
            max(1.0 - (fouls_per_match / 20.0), 0.0), 3
        )

        # --- defensive_line_height ---
        if team_stats and team_stats.get("defensive_line_height") is not None:
            metrics["defensive_line_height"] = round(team_stats["defensive_line_height"], 3)
        else:
            # Estimate from avg_position_x of defenders in snapshots (when CV adds it)
            # For now use population default
            metrics["defensive_line_height"] = METRIC_DEFAULTS["defensive_line_height"]

        # Apply defaults for any zero-data metrics
        for key in TEAM_METRICS:
            if metrics.get(key) is None:
                metrics[key] = METRIC_DEFAULTS[key]

        final_source = "full" if source == "full" else "basic" if snapshots else "default"
        if not snapshots:
            # No data at all — return all defaults
            metrics = dict(METRIC_DEFAULTS)
            final_source = "default"

        return metrics, final_source

    def _compute_opp_metrics(self, opposition: dict) -> tuple:
        """
        We never have CV data on the opposition.
        Derive what we can from the parsed scouting profile.
        Everything else defaults to population average.
        """
        metrics = dict(METRIC_DEFAULTS)

        if not opposition:
            return metrics, "default"

        attrs = opposition.get("attributes", {})
        style = opposition.get("playing_style", "")
        press = opposition.get("press_style", "")
        line  = opposition.get("defensive_line", "")

        # Qualitative → quantitative mappings
        if "possession" in style.lower() or "tiki" in style.lower():
            metrics["possession_share"]        = 0.58
            metrics["passing_stability_index"] = 0.82
        elif "direct" in style.lower() or "long ball" in style.lower():
            metrics["possession_share"]        = 0.42
            metrics["passing_stability_index"] = 0.68

        if "high press" in press.lower():
            metrics["offensive_output_index"]    = 0.55
            metrics["defensive_solidity_index"]  = 0.60
        elif "low block" in press.lower() or "sit deep" in press.lower():
            metrics["defensive_solidity_index"]  = 0.70
            metrics["offensive_output_index"]    = 0.30

        if "high" in line.lower():
            metrics["defensive_line_height"] = 0.70
        elif "deep" in line.lower() or "low" in line.lower():
            metrics["defensive_line_height"] = 0.30

        return metrics, "opposition_notes"

    def _estimate_match_count(self, snapshots: list) -> int:
        """Estimate how many matches the snapshots span."""
        if not snapshots:
            return 1
        match_ids = set(s["match_id"] for s in snapshots)
        return max(len(match_ids), 1)