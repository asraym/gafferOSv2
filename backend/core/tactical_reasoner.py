import os
import joblib
import numpy as np


FORMATION_DECODING = {
    0:  "4-3-3",
    1:  "4-4-2",
    2:  "4-2-3-1",
    7:  "4-1-4-1",
    10: "4-4-1-1",
    # 3-4-3 (key 6) removed — no recommendation rule exists for it (#10)
}

PRESS_RULES = [
    (lambda d: d["fatigue_score"] > 0.65,                                          "Low"),
    (lambda d: d["opp"]["defensive_solidity_index"] > 0.70,                        "Low"),
    (lambda d: d["team"]["offensive_output_index"] > 0.55
               and d["team"]["passing_stability_index"] > 0.75
               and d["fatigue_score"] < 0.40,                                      "High"),
]

LINE_RULES = [
    (lambda d: d["opp"]["offensive_output_index"] > 0.55,                          "Deep"),
    (lambda d: d["team"]["defensive_solidity_index"] < 0.40,                       "Deep"),
    (lambda d: d["team"]["offensive_output_index"] > 0.55
               and d["opp"]["offensive_output_index"] < 0.40,                      "High"),
]

FOCUS_RULES = [
    (lambda d: d["team"]["defensive_solidity_index"] < 0.40
               and d["opp"]["offensive_output_index"] > 0.55,                      "Defensive Solidity"),
    (lambda d: d["team"]["offensive_output_index"] > 0.55
               and d["opp"]["defensive_solidity_index"] < 0.40,                    "High Press & Dominate"),
    (lambda d: d["team"]["possession_share"] > 0.55
               and d["team"]["passing_stability_index"] > 0.78,                    "Possession & Build-Up"),
    (lambda d: d["team"]["passing_stability_index"] < 0.65,                        "Counter-Attacking"),
]

FORMATION_PROFILES = {
    "4-3-3":   {"GK":1,"DEF":4,"MID":3,"FWD":3,
                "needs_wingers":True,  "needs_fullbacks":True,
                "needs_cam":False, "three_back":False},
    "4-4-2":   {"GK":1,"DEF":4,"MID":4,"FWD":2,
                "needs_wingers":False, "needs_fullbacks":True,
                "needs_cam":False, "three_back":False},
    "4-2-3-1": {"GK":1,"DEF":4,"MID":5,"FWD":1,
                "needs_wingers":False, "needs_fullbacks":True,
                "needs_cam":True,  "three_back":False},
    "4-1-4-1": {"GK":1,"DEF":4,"MID":5,"FWD":1,
                "needs_wingers":False, "needs_fullbacks":True,
                "needs_cam":False, "three_back":False},
    "4-4-1-1": {"GK":1,"DEF":4,"MID":4,"FWD":2,
                "needs_wingers":False, "needs_fullbacks":True,
                "needs_cam":True,  "three_back":False},
    "4-3-1-2": {"GK":1,"DEF":4,"MID":4,"FWD":2,
                "needs_wingers":False, "needs_fullbacks":True,
                "needs_cam":True,  "three_back":False},
    "3-5-2":   {"GK":1,"DEF":3,"MID":5,"FWD":2,
                "needs_wingers":False, "needs_fullbacks":False,
                "needs_cam":False, "three_back":True},
    "3-4-3":   {"GK":1,"DEF":3,"MID":4,"FWD":3,
                "needs_wingers":True,  "needs_fullbacks":False,
                "needs_cam":False, "three_back":True},
}

# Opponent strength levels that block 3-back systems
THREE_BACK_BLOCKED_STRENGTHS = {"high"}


# Opposition formation → recommended counter-shape (#8 addition)
OPP_FORMATION_RESPONSES = {
    "5-4-1": "4-2-3-1",   # low block — width to stretch them
    "5-3-2": "4-3-3",     # low block — wide overloads
    "4-3-3": "4-2-3-1",   # high press — extra mid body to play through
    "4-4-2": "4-3-3",     # direct — midfield numbers to win second balls
}


class TacticalReasoner:
    """
    Layer 1 — loads the trained XGBoost pkl.
    Derives press intensity, defensive line, tactical focus as post-model decisions.
    Formation chosen by metric + trait + opposition-aware rules.
    """

    PKL_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "match_predictor.pkl")

    def __init__(self):
        self._artifact = None

    def _load(self):
        if self._artifact is None:
            if not os.path.exists(self.PKL_PATH):
                raise FileNotFoundError(
                    "match_predictor.pkl not found. "
                    "Run python ml/train.py to generate it."
                )
            self._artifact = joblib.load(self.PKL_PATH)

    def reason(self, data: dict) -> dict:
        self._load()
        model         = self._artifact["model"]
        feature_names = self._artifact["feature_names"]

        team_m  = data["team_metrics"]
        opp_m   = data["opp_metrics"]
        home_aw = 1 if data.get("home_away") == "home" else 0
        roll_m  = team_m  # bug #13 — rolling == current until history accumulates

        data_mode = data.get("data_mode", "default")

        # bug #9 — default mode returns None for formation, base rates for probs
        if data_mode == "default":
            win_p, draw_p, loss_p = 0.375, 0.250, 0.375
            best_formation = None
        else:
            features = self._build_feature_vector(
                feature_names, team_m, opp_m, roll_m, home_aw
            )
            probs    = model.predict_proba([features])[0]
            loss_p, draw_p, win_p = float(probs[0]), float(probs[1]), float(probs[2])
            initial_formation = self._pick_formation(team_m, opp_m, data)
            available_counts  = self._count_available(data.get("players", []))
            best_formation, formation_note = self._resolve_formation(
                initial_formation, data.get("players", []), available_counts, data
            )
            if formation_note:
                data["formation_selection_note"] = formation_note

        context = {
            "team":          team_m,
            "opp":           opp_m,
            "fatigue_score": data.get("fatigue_score", 0.30),
        }
        press = self._apply_rules(PRESS_RULES, context, default="Medium")
        line  = self._apply_rules(LINE_RULES,  context, default="Medium")
        focus = self._apply_rules(FOCUS_RULES, context, default="Balanced Mid-Block")

        opp_profile       = data.get("opposition") or {}
        opp_formation_str = opp_profile.get("likely_formation") or opp_profile.get("formation") or "Unknown"

        data.update({
            "recommended_formation": best_formation,
            "win_probability":       round(win_p,  3),
            "draw_probability":      round(draw_p, 3),
            "loss_probability":      round(loss_p, 3),
            "press_intensity":       press,
            "defensive_line":        line,
            "tactical_focus":        focus,
            "opp_formation":         opp_formation_str,
        })
        return data

    def _pick_formation(self, team_m: dict, opp_m: dict, data: dict) -> str:
        """
        Formation selection — priority order:
        1. Defensive emergency / fatigue edge cases
        2. Matchup vulnerability flags (#11)
        3. Opposition formation response
        4. Squad depth check
        5. Trait-informed decisions
        6. Attribute-informed decisions (pace, physical) — moved after edge cases (#8)
        7. Metric fallbacks
        """
        pss     = team_m["passing_stability_index"]
        osi     = team_m["offensive_output_index"]
        dsi     = team_m["defensive_solidity_index"]
        opp_osi = opp_m["offensive_output_index"]
        fat     = data.get("fatigue_score", 0.30)
        home    = 1 if data.get("home_away") == "home" else 0
        players = data.get("players", [])

        # ── 1. Edge cases — fatigue and defensive emergency first (#8 fix) ──
        if dsi < 0.45 and opp_osi > 0.55:
            return "4-4-1-1"

        if fat > 0.60 and opp_osi > 0.45:
            return "4-1-4-1"

        # ── 2. Matchup vulnerability adjustment (#11) ──
        # If matchup layer flagged a pace vulnerability on a fullback,
        # prefer a formation that gives them more cover (extra mid shield).
        vulnerabilities = data.get("matchup_vulnerabilities", [])
        has_fb_pace_vuln = any(
            "fullback" in v.lower() or "full back" in v.lower() or "rb" in v.lower() or "lb" in v.lower()
            for v in vulnerabilities
            if "pace" in v.lower() or "slow" in v.lower()
        )
        if has_fb_pace_vuln and opp_osi > 0.45:
            # Extra midfielder covers exposed FB channels
            return "4-2-3-1"

        # ── 3. Opposition formation response ──
        opp_profile = data.get("opposition") or {}
        opp_formation_str = (
            opp_profile.get("likely_formation") or
            opp_profile.get("formation") or ""
        )
        if opp_formation_str in OPP_FORMATION_RESPONSES:
            return OPP_FORMATION_RESPONSES[opp_formation_str]

        # ── 4. Squad depth check ──
        # Count available players per broad position.
        # If recommended shape can't be filled, fall back.
        formation_needs = {
            "4-3-3":   {"GK": 1, "DEF": 4, "MID": 3, "FWD": 3},
            "4-4-2":   {"GK": 1, "DEF": 4, "MID": 4, "FWD": 2},
            "4-2-3-1": {"GK": 1, "DEF": 4, "MID": 5, "FWD": 1},
            "4-1-4-1": {"GK": 1, "DEF": 4, "MID": 5, "FWD": 1},
            "4-4-1-1": {"GK": 1, "DEF": 4, "MID": 5, "FWD": 1},
        }
        available_counts = self._count_available(players)

        def can_field(formation: str) -> bool:
            needs = formation_needs.get(formation, {})
            for pos, count in needs.items():
                if available_counts.get(pos, 0) < count:
                    return False
            return True

        # ── 5. Trait-informed decisions ──
        sq_off, sq_def, sq_air, sq_prog = self._squad_tendencies(players)

        has_target_man = any(
            p.get("broad_position") == "FWD"
            and "Target Man Play" in p.get("traits", [])
            for p in players
        )
        has_false_nine = any(
            p.get("broad_position") == "FWD"
            and "False Nine Tendencies" in p.get("traits", [])
            for p in players
        )
        has_deep_playmaker = any(
            p.get("specific_position") == "CDM"
            and "Deep Playmaker" in p.get("traits", [])
            for p in players
        )
        fb_offensive = any(
            p.get("broad_position") == "DEF"
            and p.get("tactical_profile", {}).get("offensive_tendency", 0) > 0.3
            for p in players
        )

        trait_candidates = []
        if has_target_man and sq_air > 0.2:
            trait_candidates.append("4-4-2")
        if has_false_nine and pss >= 0.75:
            trait_candidates.append("4-3-3")
        if has_deep_playmaker and dsi > 0.50:
            trait_candidates.append("4-2-3-1")
        if fb_offensive and sq_prog > 0.2 and osi > 0.45:
            trait_candidates.append("4-3-3")
        if sq_def > 0.25 and opp_osi > 0.50:
            trait_candidates.append("4-4-2")

        for f in trait_candidates:
            if can_field(f):
                return f

        # ── 6. Attribute-informed decisions — after edge cases (#8 fix) ──
        fwd_pace = [
            p.get("attributes", {}).get("pace")
            for p in players
            if p.get("broad_position") == "FWD"
            and p.get("attributes", {}).get("pace") is not None
        ]
        avg_fwd_pace = sum(fwd_pace) / len(fwd_pace) if fwd_pace else None

        has_physical_st = any(
            p.get("broad_position") == "FWD"
            and p.get("attributes", {}).get("heading", 0) >= 15
            and p.get("attributes", {}).get("strength", 0) >= 14
            for p in players
        )

        if avg_fwd_pace is not None and avg_fwd_pace >= 15 and osi > 0.40:
            f = "4-3-3"
            if can_field(f):
                return f

        if has_physical_st and not has_false_nine:
            f = "4-4-2"
            if can_field(f):
                return f

        # ── 7. Metric fallbacks ──
        metric_candidates = []
        if pss >= 0.77:
            metric_candidates.append("4-3-3")
        if pss < 0.77 and opp_osi >= 0.50:
            metric_candidates.append("4-4-2")
        metric_candidates.append("4-2-3-1" if home == 1 else "4-4-2")

        for f in metric_candidates:
            if can_field(f):
                return f

        # Final fallback — return whatever we can field
        for f in ["4-4-2", "4-3-3", "4-2-3-1", "4-1-4-1", "4-4-1-1"]:
            if can_field(f):
                return f

        return "4-4-2"  # absolute last resort

    def _count_available(self, players: list) -> dict:
        """Count available players per broad position."""
        counts = {"GK": 0, "DEF": 0, "MID": 0, "FWD": 0}
        for p in players:
            if p.get("available", True):
                pos = p.get("broad_position") or p.get("position", "")
                if pos in counts:
                    counts[pos] += 1
        return counts

    def _squad_tendencies(self, players: list) -> tuple:
        """Return (sq_off, sq_def, sq_air, sq_prog) averages from tactical profiles."""
        if not players:
            return 0.0, 0.0, 0.0, 0.0
        n = len(players)
        sq_off  = sum(p.get("tactical_profile", {}).get("offensive_tendency",   0.0) for p in players) / n
        sq_def  = sum(p.get("tactical_profile", {}).get("defensive_tendency",   0.0) for p in players) / n
        sq_air  = sum(p.get("tactical_profile", {}).get("aerial_tendency",      0.0) for p in players) / n
        sq_prog = sum(p.get("tactical_profile", {}).get("progressive_tendency", 0.0) for p in players) / n
        return sq_off, sq_def, sq_air, sq_prog

    def _build_feature_vector(self, feature_names, team_m, opp_m, roll_m, home_aw) -> list:
        PKL_METRICS = [
            "offensive_output_index",
            "shot_quality_index",
            "defensive_solidity_index",
            "passing_stability_index",
            "possession_share",
            "discipline_index",
            "defensive_line_height",
        ]

        diff_m = {k: round(team_m[k] - opp_m[k], 4) for k in PKL_METRICS}

        lookup = {}
        for k in PKL_METRICS:
            lookup[f"team_{k}"] = team_m.get(k, 0.0)
            lookup[f"opp_{k}"]  = opp_m.get(k, 0.0)
            lookup[f"roll_{k}"] = roll_m.get(k, 0.0)
            lookup[f"diff_{k}"] = diff_m.get(k, 0.0)

        lookup["attack_vs_defense"]       = round(team_m["offensive_output_index"] - opp_m["defensive_solidity_index"], 4)
        lookup["shot_quality_vs_defense"] = round(team_m["shot_quality_index"] - opp_m["defensive_solidity_index"], 4)
        lookup["possession_battle"]       = round(team_m["possession_share"] - opp_m["possession_share"], 4)
        lookup["home_away"]               = home_aw

        return [lookup.get(f, 0.0) for f in feature_names]

    def _apply_rules(self, rules: list, context: dict, default: str) -> str:
        for condition, label in rules:
            try:
                if condition(context):
                    return label
            except (KeyError, TypeError):
                continue
        return default
    def _resolve_formation(self, recommended: str, players: list,
                        available_counts: dict, data: dict) -> tuple:
        """
        Validates recommended formation against squad availability
        and opponent strength. Finds best alternative if gaps exist.
        Returns (formation, explanation_note).
        """
        opp_profile  = data.get("opposition") or {}
        opp_strength = opp_profile.get("opponent_strength")
        league_pos   = opp_profile.get("league_position")
        opp_osi      = data.get("opp_metrics", {}).get("offensive_output_index", 0.38)

        # Determine if opponent is strong enough to block 3-back
        opp_is_strong = (
            opp_strength in THREE_BACK_BLOCKED_STRENGTHS
            or (league_pos is not None and league_pos <= 3)
            or opp_osi > 0.55
        )

        profile = FORMATION_PROFILES.get(recommended, {})
        gaps    = self._detect_gaps(recommended, profile, players,
                                    available_counts, opp_is_strong)

        if not gaps:
            return recommended, ""

        # Find best alternative
        alternatives = self._score_alternatives(players, available_counts,
                                                opp_is_strong)
        if not alternatives:
            return recommended, f"Squad gaps detected: {', '.join(gaps)}. No better alternative found."

        best, score, reason = alternatives[0]
        gap_summary = ", ".join(gaps)
        return best, (
            f"Switched from {recommended} to {best} — {gap_summary}. "
            f"{reason}."
        )

    def _detect_gaps(self, formation: str, profile: dict, players: list,
                    available_counts: dict, opp_is_strong: bool) -> list:
        """
        Returns list of gap descriptions for a formation against this squad.
        Empty list means no gaps — formation is viable.
        """
        gaps = []

        wide_positions = {"RW", "LW", "RM", "LM"}
        fb_positions   = {"RB", "LB", "RWB", "LWB"}
        cam_positions  = {"CAM"}

        available_wide = sum(
            1 for p in players
            if p.get("specific_position") in wide_positions
            and p.get("available", True)
        )
        available_fb = sum(
            1 for p in players
            if p.get("specific_position") in fb_positions
            and p.get("available", True)
        )
        available_cam = sum(
            1 for p in players
            if p.get("specific_position") in cam_positions
            and p.get("available", True)
        )
        available_cb = sum(
            1 for p in players
            if p.get("specific_position") == "CB"
            and p.get("available", True)
        )

        # Winger gap
        if profile.get("needs_wingers") and available_wide < 2:
            gaps.append("no fit wide players for winger roles")

        # Fullback gap
        if profile.get("needs_fullbacks") and available_fb < 2:
            gaps.append("no fit fullbacks available")

        # CAM gap
        if profile.get("needs_cam") and available_cam < 1:
            # Check if a CM can cover — softer gap
            available_cm = sum(
                1 for p in players
                if p.get("specific_position") == "CM"
                and p.get("available", True)
            )
            if available_cm < 1:
                gaps.append("no CAM or CM to fill #10 role")

        # 3-back vs strong opponent
        if profile.get("three_back") and opp_is_strong:
            gaps.append("3-back system too exposed against strong opposition")

        # General slot coverage
        for broad, count in profile.items():
            if broad in ("needs_wingers", "needs_fullbacks",
                        "needs_cam", "three_back"):
                continue
            if not isinstance(count, int):
                continue
            if available_counts.get(broad, 0) < count:
                gaps.append(
                    f"only {available_counts.get(broad,0)} "
                    f"{broad} available, {count} needed"
                )

        return gaps

    def _score_alternatives(self, players: list, available_counts: dict,
                            opp_is_strong: bool) -> list:
        """
        Scores all candidate formations by squad fit.
        Returns sorted list of (formation, score, reason) tuples.
        Higher score = better fit.
        """
        wide_positions = {"RW", "LW", "RM", "LM"}
        fb_positions   = {"RB", "LB", "RWB", "LWB"}
        cam_positions  = {"CAM"}

        available_wide = sum(
            1 for p in players
            if p.get("specific_position") in wide_positions
            and p.get("available", True)
        )
        available_fb = sum(
            1 for p in players
            if p.get("specific_position") in fb_positions
            and p.get("available", True)
        )
        available_cam = sum(
            1 for p in players
            if p.get("specific_position") in cam_positions
            and p.get("available", True)
        )

        scored = []

        for formation, profile in FORMATION_PROFILES.items():
            score   = 0
            reasons = []
            penalty = 0

            # Hard block: 3-back vs strong opponent
            if profile.get("three_back") and opp_is_strong:
                continue

            # Winger requirement check
            if profile.get("needs_wingers"):
                if available_wide >= 2:
                    score += 3
                    reasons.append("wide players available")
                else:
                    penalty += 5  # heavy penalty — structural gap

            # Fullback requirement check
            if profile.get("needs_fullbacks"):
                if available_fb >= 2:
                    score += 2
                    reasons.append("fullbacks available")
                else:
                    penalty += 4

            # CAM requirement check
            if profile.get("needs_cam"):
                if available_cam >= 1:
                    score += 2
                    reasons.append("CAM available for #10 role")
                else:
                    # CM can cover — softer penalty
                    available_cm = sum(
                        1 for p in players
                        if p.get("specific_position") == "CM"
                        and p.get("available", True)
                    )
                    if available_cm >= 1:
                        score += 1
                        reasons.append("CM covering #10 role")
                    else:
                        penalty += 2

            # General slot coverage
            all_covered = True
            for broad, count in profile.items():
                if broad in ("needs_wingers", "needs_fullbacks",
                            "needs_cam", "three_back"):
                    continue
                if not isinstance(count, int):
                    continue
                available = available_counts.get(broad, 0)
                if available >= count:
                    score += count
                elif available > 0:
                    score += available
                    penalty += (count - available)
                else:
                    all_covered = False
                    penalty += count * 2

            if all_covered:
                score += 2  # bonus for full coverage

            final_score = score - penalty
            if final_score > 0:
                scored.append((formation, final_score,
                            ", ".join(reasons[:2]) if reasons else "best available fit"))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored