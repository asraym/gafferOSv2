from collections import defaultdict
from core.player_traits import get_tactical_profile 


FORMATION_SLOTS = {
    "4-3-3":   {"GK": 1, "DEF": 4, "MID": 3, "FWD": 3},
    "4-4-2":   {"GK": 1, "DEF": 4, "MID": 4, "FWD": 2},
    "4-2-3-1": {"GK": 1, "DEF": 4, "MID": 5, "FWD": 1},
    "3-4-3":   {"GK": 1, "DEF": 3, "MID": 4, "FWD": 3},
    "4-1-4-1": {"GK": 1, "DEF": 4, "MID": 5, "FWD": 1},
    "4-4-1-1": {"GK": 1, "DEF": 4, "MID": 4, "FWD": 2},
}

BROAD_FALLBACK = {
    "GK":  ["GK"],
    "DEF": ["CB", "RB", "LB", "RWB", "LWB"],
    "MID": ["CDM", "CM", "CAM", "RM", "LM"],
    "FWD": ["RW", "LW", "ST", "CF", "SS"],
}

FATIGUE_THRESHOLD = 0.65


class PlayerRanker:
    """
    Layer 2 — Squad Constraint Layer.
    Ranks players by form score derived from recent snapshots.
    Fills XI slots for the recommended formation.
    Generates rotation suggestions for fatigued or low-form players.
    """
    FORMATION_SLOTS = FORMATION_SLOTS

    def rank(self, data: dict) -> dict:
        players   = data.get("players", [])
        snapshots = data.get("snapshots", [])

        # Compute per-player form scores from snapshots
        form_scores = self._compute_form_scores(snapshots)

        # Attach form score and tactical profile to each player
        for p in players:
            p["form_score"]      = form_scores.get(p["player_id"], None)
            traits               = p.get("traits", [])
            p["tactical_profile"] = get_tactical_profile(traits) if traits else {}

        # Estimate team fatigue score (feeds into tactical reasoner context)
        fatigue          = self._compute_fatigue(players)
        data["fatigue_score"] = fatigue

        # NOTE: formation is not known yet at this stage — TacticalReasoner runs after us
        # XI selection happens in a second pass after formation is decided
        # Store players + fatigue now, XI filled later
        data["players"]        = players
        data["team_fatigue_score"] = fatigue
        return data

    # ------------------------------------------------------------------
    # Form score
    # ------------------------------------------------------------------

    def _compute_form_scores(self, snapshots: list) -> dict:
        """
        Calculates a 0.0–1.0 form score per player from their recent snapshots.
        Weights: goals(0.25) assists(0.20) key_passes(0.20) tackles+interceptions(0.20)
                 minutes_played(0.10) defensive_errors inverse(0.05)
        """
        by_player = defaultdict(list)
        for s in snapshots:
            by_player[s["player_id"]].append(s)

        scores = {}
        for pid, snaps in by_player.items():
            n = len(snaps)
            avg_goals    = sum(s["goals"] for s in snaps) / n
            avg_assists  = sum(s["assists"] for s in snaps) / n
            avg_kp       = sum(s["key_passes"] for s in snaps) / n
            avg_def      = sum(s["tackles"] + s["interceptions"] for s in snaps) / n
            avg_mins     = sum(s["minutes_played"] for s in snaps) / n
            avg_errors   = sum(s["defensive_errors"] for s in snaps) / n

            # Normalise each to 0-1
            goals_n   = min(avg_goals / 1.0,  1.0)   # 1 goal/match = max
            assists_n = min(avg_assists / 0.8, 1.0)   # 0.8 assists/match = max
            kp_n      = min(avg_kp / 3.0,     1.0)   # 3 key passes/match = max
            def_n     = min(avg_def / 6.0,    1.0)   # 6 def actions/match = max
            mins_n    = min(avg_mins / 90.0,  1.0)
            error_n   = max(1.0 - avg_errors / 3.0, 0.0)  # 0 errors = best

            form = (
                goals_n   * 0.25 +
                assists_n * 0.20 +
                kp_n      * 0.20 +
                def_n     * 0.20 +
                mins_n    * 0.10 +
                error_n   * 0.05
            )
            scores[pid] = round(form, 3)

        return scores

    # ------------------------------------------------------------------
    # Fatigue
    # ------------------------------------------------------------------

    def _compute_fatigue(self, players: list) -> float:
        """
        Estimates team fatigue from average minutes played in recent snapshots.
        Players with no snapshot data are assumed fresh (0.0 fatigue).
        """
        fatigue_scores = []
        for p in players:
            fs = p.get("form_score")
            # Minutes-based fatigue: high minutes recently = higher fatigue risk
            # We fold this into a simple proxy: if form_score is None → fresh
            if fs is not None:
                # Heavy minutes proxy — using season matches as heuristic
                matches = p.get("season_matches_played", 0)
                fatigue_scores.append(min(matches / 30.0, 1.0))
        if not fatigue_scores:
            return 0.30  # default
        return round(sum(fatigue_scores) / len(fatigue_scores), 3)

    # ------------------------------------------------------------------
    # XI selection
    # ------------------------------------------------------------------

    def _fill_xi(self, players: list, slots: dict, form_scores: dict) -> tuple:
        starting_xi = []
        used_ids    = set()

        for broad, count in slots.items():
            selected = self._pick_for_slot(players, broad, count, used_ids, form_scores)
            for p in selected:
                xi_entry = dict(p)
                xi_entry["slot_broad"] = broad
                starting_xi.append(xi_entry)
                used_ids.add(p["player_id"])

        return starting_xi, used_ids

    def _pick_for_slot(self, players, broad, count, used_ids, form_scores) -> list:
        candidates = []

        # Primary: exact broad position match
        for p in players:
            if p["player_id"] in used_ids:
                continue
            if p["broad_position"] == broad:
                candidates.append(p)

        # Secondary: secondary_position covers the broad group
        if len(candidates) < count:
            spec_options = BROAD_FALLBACK.get(broad, [])
            for p in players:
                if p["player_id"] in used_ids or p in candidates:
                    continue
                if p.get("secondary_position") in spec_options:
                    candidates.append(p)

        # Tertiary: fill from anyone (positional emergency)
        if len(candidates) < count:
            for p in players:
                if p["player_id"] in used_ids or p in candidates:
                    continue
                candidates.append(p)

        # Sort by form_score if available, else by season goals as proxy
        candidates.sort(
            key=lambda p: (
                form_scores.get(p["player_id"]) if form_scores.get(p["player_id"]) is not None
                else p["season_goals"] / max(p["season_matches_played"], 1)
            ),
            reverse=True
        )
        return candidates[:count]

    # ------------------------------------------------------------------
    # Rotation suggestions
    # ------------------------------------------------------------------

    def _generate_rotation(self, starting_xi: list, bench: list, fatigue: float) -> list:
        suggestions = []

        if not starting_xi:
            if fatigue > 0.55:
                suggestions.append(
                    "No player data available. Fatigue risk elevated — rotate if possible."
                )
            return suggestions

        for p in starting_xi:
            fs  = p.get("form_score")
            pid = p["player_id"]
            name = p["name"]
            pos  = p.get("specific_position", p["broad_position"])

            if fs is not None and fs < 0.35:
                replacement = self._find_bench_cover(bench, p["broad_position"])
                if replacement:
                    suggestions.append(
                        f"{name} ({pos}) — low form score {fs:.2f}. "
                        f"Consider starting {replacement['name']} "
                        f"({replacement.get('specific_position', replacement['broad_position'])}, "
                        f"form: {replacement.get('form_score', 'N/A')})."
                    )
                else:
                    suggestions.append(
                        f"{name} ({pos}) — low form score {fs:.2f}. No bench cover available."
                    )

        if not suggestions:
            suggestions.append("Squad form looks solid — no urgent rotation needed.")

        return suggestions

    def _find_bench_cover(self, bench: list, broad: str):
        candidates = [p for p in bench if p["broad_position"] == broad]
        if not candidates:
            return None
        return max(
            candidates,
            key=lambda p: p.get("form_score") if p.get("form_score") is not None else -1
        )