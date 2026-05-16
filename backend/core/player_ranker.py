from collections import defaultdict
from core.player_traits import get_tactical_profile


FORMATION_SLOTS = {
    "4-3-3":   {"GK": 1, "DEF": 4, "MID": 3, "FWD": 3},
    "4-4-2":   {"GK": 1, "DEF": 4, "MID": 4, "FWD": 2},
    "4-2-3-1": {"GK": 1, "DEF": 4, "MID": 5, "FWD": 1},
    "4-1-4-1": {"GK": 1, "DEF": 4, "MID": 5, "FWD": 1},
    "4-4-1-1": {"GK": 1, "DEF": 4, "MID": 4, "FWD": 2},
    "4-3-1-2": {"GK": 1, "DEF": 4, "MID": 4, "FWD": 2},
    "3-5-2":   {"GK": 1, "DEF": 3, "MID": 5, "FWD": 2},
    "3-4-3":   {"GK": 1, "DEF": 3, "MID": 4, "FWD": 3},
}

BROAD_FALLBACK = {
    "GK":  ["GK"],
    "DEF": ["CB", "RB", "LB", "RWB", "LWB"],
    "MID": ["CDM", "CM", "CAM", "RM", "LM"],
    "FWD": ["RW", "LW", "ST", "CF", "SS"],
}

# Position-specific stamina thresholds for high press flagging
# Wide players and pressing forwards have higher demand than CBs/GKs
STAMINA_THRESHOLDS = {
    "GK":  10,
    "CB":  10,
    "RB":  11,
    "LB":  11,
    "RWB": 12,
    "LWB": 12,
    "CDM": 11,
    "CM":  11,
    "CAM": 11,
    "RM":  12,
    "LM":  12,
    "RW":  12,
    "LW":  12,
    "ST":  11,
    "CF":  11,
    "SS":  11,
}

# Fitness threshold by match risk level
# High risk — can't carry passengers
# Low risk — can afford slightly tired players
FITNESS_THRESHOLD_BY_RISK = {
    "High":   0.50,
    "Medium": 0.35,
    "Low":    0.30,
}


class PlayerRanker:
    """
    Layer 2 — Squad Constraint Layer.
    Ranks players by form score derived from recent snapshots.
    Fills XI slots for the recommended formation.
    Generates rotation suggestions.
    """
    FORMATION_SLOTS = FORMATION_SLOTS

    def rank(self, data: dict) -> dict:
        players   = data.get("players", [])
        snapshots = data.get("snapshots", [])

        form_scores = self._compute_form_scores(snapshots)

        for p in players:
            p["form_score"]       = form_scores.get(p["player_id"], None)
            traits                = p.get("traits", [])
            p["tactical_profile"] = get_tactical_profile(traits) if traits else {}

        fatigue = self._compute_fatigue(players)
        data["fatigue_score"]      = fatigue
        data["team_fatigue_score"] = fatigue
        data["players"]            = players
        return data

    # ------------------------------------------------------------------
    # Form score
    # ------------------------------------------------------------------

    def _compute_form_scores(self, snapshots: list) -> dict:
        by_player = defaultdict(list)
        for s in snapshots:
            by_player[s["player_id"]].append(s)

        scores = {}
        for pid, snaps in by_player.items():
            n = len(snaps)
            avg_goals   = sum(s["goals"] for s in snaps) / n
            avg_assists = sum(s["assists"] for s in snaps) / n
            avg_kp      = sum(s["key_passes"] for s in snaps) / n
            avg_def     = sum(s["tackles"] + s["interceptions"] for s in snaps) / n
            avg_mins    = sum(s["minutes_played"] for s in snaps) / n
            avg_errors  = sum(s["defensive_errors"] for s in snaps) / n

            goals_n   = min(avg_goals / 1.0,  1.0)
            assists_n = min(avg_assists / 0.8, 1.0)
            kp_n      = min(avg_kp / 3.0,     1.0)
            def_n     = min(avg_def / 6.0,    1.0)
            mins_n    = min(avg_mins / 90.0,  1.0)
            error_n   = max(1.0 - avg_errors / 3.0, 0.0)

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

    def _compute_form_trajectory(self, snapshots: list, player_id: int) -> str:
        """
        Returns 'Rising', 'Falling', or 'Stable' based on last 3 snapshots.
        Used by explainer for form trajectory notes.
        """
        player_snaps = sorted(
            [s for s in snapshots if s["player_id"] == player_id],
            key=lambda s: s.get("match_id", 0)
        )
        if len(player_snaps) < 3:
            return "Stable"

        def snap_score(s):
            return (
                s.get("goals", 0) * 0.25 +
                s.get("assists", 0) * 0.20 +
                s.get("key_passes", 0) * 0.10 +
                (s.get("tackles", 0) + s.get("interceptions", 0)) * 0.10
            )

        recent   = snap_score(player_snaps[-1])
        previous = snap_score(player_snaps[-2])
        earlier  = snap_score(player_snaps[-3])
        trend    = (recent - earlier) / max(earlier, 0.1)

        if trend > 0.20:
            return "Rising"
        elif trend < -0.20:
            return "Falling"
        return "Stable"

    # ------------------------------------------------------------------
    # Fatigue
    # ------------------------------------------------------------------

    def _compute_fatigue(self, players: list) -> float:
        fatigue_scores = []
        for p in players:
            attrs   = p.get("attributes", {})
            stamina = attrs.get("stamina")
            if stamina is not None:
                fatigue_scores.append(round(1.0 - (stamina / 20.0) * 0.95, 3))
            else:
                matches = p.get("season_matches_played", 0)
                fatigue_scores.append(min(matches / 30.0, 1.0))
        if not fatigue_scores:
            return 0.30
        return round(sum(fatigue_scores) / len(fatigue_scores), 3)

    # ------------------------------------------------------------------
    # XI selection
    # ------------------------------------------------------------------

    def _fill_xi(self, players: list, slots: dict, form_scores: dict) -> tuple:
        starting_xi = []
        used_ids    = set()

        for broad, count in slots.items():
            selected = self._pick_for_slot(players, broad, count, used_ids, form_scores)
            for p, is_mismatch in selected:
                xi_entry = dict(p)
                xi_entry["slot_broad"]          = broad
                xi_entry["positional_mismatch"] = is_mismatch
                starting_xi.append(xi_entry)
                used_ids.add(p["player_id"])

        return starting_xi, used_ids

    def _pick_for_slot(self, players, broad, count, used_ids, form_scores) -> list:
        """
        Returns list of (player, is_mismatch) tuples.
        is_mismatch=True when player fills slot from tertiary pool (wrong position).
        Fixes Deepak Nair slot_broad bug — mismatches are flagged not silently accepted.
        """
        primary   = []
        secondary = []
        tertiary  = []

        spec_options = BROAD_FALLBACK.get(broad, [])

        for p in players:
            if p["player_id"] in used_ids:
                continue
            if p["broad_position"] == broad:
                primary.append(p)
            elif p.get("secondary_position") in spec_options:
                secondary.append(p)
            else:
                tertiary.append(p)

        def sort_key(p):
            attrs = p.get("attributes", {})
            if attrs.get("overall_rating") is not None:
                return (3, attrs["overall_rating"])
            if attrs.get("role_rating") is not None:
                return (2, attrs["role_rating"])
            fs = form_scores.get(p["player_id"])
            if fs is not None:
                return (1, fs * 20)
            matches = max(p.get("season_matches_played", 0), 1)
            return (0, p.get("season_goals", 0) / matches)

        primary.sort(key=sort_key,   reverse=True)
        secondary.sort(key=sort_key, reverse=True)
        tertiary.sort(key=sort_key,  reverse=True)

        result  = []
        needed  = count

        # Fill from primary (no mismatch)
        for p in primary[:needed]:
            result.append((p, False))
        needed -= len(result)

        # Fill from secondary (no mismatch — secondary position covers slot)
        if needed > 0:
            for p in secondary[:needed]:
                result.append((p, False))
            needed -= len([r for r in result if not r[1]])
            needed  = count - len(result)

        # Fill from tertiary (mismatch — flag it)
        if needed > 0:
            for p in tertiary[:needed]:
                result.append((p, True))

        return result

    # ------------------------------------------------------------------
    # Rotation suggestions
    # ------------------------------------------------------------------

    def _generate_rotation(
        self,
        starting_xi: list,
        bench: list,
        fatigue: float,
        press_intensity: str = "Medium",
        match_risk: str = "Medium",
        snapshots: list = None,
    ) -> list:
        suggestions = []
        snapshots   = snapshots or []

        if not starting_xi:
            if fatigue > 0.55:
                suggestions.append(
                    "No player data available. Fatigue risk elevated — rotate if possible."
                )
            return suggestions

        # Forced selection flag — fewer than 11 available players
        available_count = len([p for p in starting_xi if not p.get("positional_mismatch")])
        mismatch_count  = len([p for p in starting_xi if p.get("positional_mismatch")])
        if mismatch_count > 0:
            suggestions.append(
                f"Forced selection — {mismatch_count} player(s) filling out-of-position slot(s) "
                f"due to squad availability. Monitor these players closely."
            )

        # Fitness threshold driven by match risk
        fitness_threshold = FITNESS_THRESHOLD_BY_RISK.get(match_risk, 0.35)

        for p in starting_xi:
            fs    = p.get("form_score")
            name  = p["name"]
            pos   = p.get("specific_position", p.get("broad_position", ""))
            attrs = p.get("attributes", {})

            # Flag 1 — low form score (risk-adjusted threshold)
            if fs is not None and fs < fitness_threshold:
                replacement = self._find_bench_cover(bench, p["broad_position"])
                if replacement:
                    suggestions.append(
                        f"{name} ({pos}) — form score {fs:.2f} below threshold for "
                        f"{match_risk.lower()} risk match. "
                        f"Consider starting {replacement['name']} "
                        f"({replacement.get('specific_position', replacement['broad_position'])}, "
                        f"form: {replacement.get('form_score', 'N/A')})."
                    )
                else:
                    suggestions.append(
                        f"{name} ({pos}) — form score {fs:.2f}. No bench cover available."
                    )

            # Flag 2 — position-specific stamina threshold for high press
            stamina = attrs.get("stamina")
            if stamina is not None and press_intensity == "High":
                threshold = STAMINA_THRESHOLDS.get(pos, 11)
                if stamina < threshold:
                    suggestions.append(
                        f"{name} ({pos}) — stamina {stamina:.1f} below {threshold} "
                        f"required for high press at this position. Plan early substitution."
                    )

            # Flag 3 — positional mismatch
            if p.get("positional_mismatch"):
                suggestions.append(
                    f"{name} filling {p.get('slot_broad')} out of position — "
                    f"primary position is {p.get('broad_position')}. Limited cover available."
                )

            # Flag 4 — low role_rating
            role_rating = attrs.get("role_rating")
            if role_rating is not None and role_rating < 12 and not p.get("positional_mismatch"):
                suggestions.append(
                    f"{name} ({pos}) — role rating {role_rating:.1f} suggests "
                    f"positional fit concern. Monitor performance closely."
                )

            # Flag 5 — form trajectory
            if snapshots:
                trajectory = self._compute_form_trajectory(snapshots, p["player_id"])
                if trajectory == "Falling" and fs is not None and fs < 0.50:
                    suggestions.append(
                        f"{name} ({pos}) — form trending downward over last 3 matches. Watch closely."
                    )

        # Flag 6 — bench player rated higher than starter
        xi_by_pos    = {}
        bench_by_pos = {}

        for p in starting_xi:
            broad   = p["broad_position"]
            overall = p.get("attributes", {}).get("overall_rating")
            if overall is not None:
                if broad not in xi_by_pos or overall > xi_by_pos[broad]["overall"]:
                    xi_by_pos[broad] = {"name": p["name"], "overall": overall}

        for p in bench:
            broad   = p["broad_position"]
            overall = p.get("attributes", {}).get("overall_rating")
            if overall is not None:
                if broad not in bench_by_pos or overall > bench_by_pos[broad]["overall"]:
                    bench_by_pos[broad] = {"name": p["name"], "overall": overall}

        for broad in xi_by_pos:
            if broad in bench_by_pos:
                starter = xi_by_pos[broad]
                benched = bench_by_pos[broad]
                if benched["overall"] - starter["overall"] >= 1.5:
                    suggestions.append(
                        f"{benched['name']} ({broad}, {benched['overall']:.1f}) rated higher than "
                        f"{starter['name']} ({starter['overall']:.1f}) — consider starting."
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