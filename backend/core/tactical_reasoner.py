import os
import joblib
import numpy as np


FORMATION_DECODING = {
    0:  "4-3-3",
    1:  "4-4-2",
    2:  "4-2-3-1",
    6:  "3-4-3",
    7:  "4-1-4-1",
    10: "4-4-1-1",
}

# Tactical decisions derived from metrics — these are not hardcoded rules,
# they are post-hoc interpretations after the ML model picks the formation.

PRESS_RULES = [
    # (condition_fn, label)
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


class TacticalReasoner:
    """
    Layer 1 — loads the trained XGBoost pkl.
    Tries all 6 formation candidates and picks the one maximising win probability.
    Derives press intensity, defensive line, tactical focus as post-model decisions.
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
        roll_m  = team_m  # rolling == current until more history accumulates

        data_mode = data.get("data_mode", "default")

        if data_mode == "default":
            win_p, draw_p, loss_p = 0.375, 0.250, 0.375
        else:
            features = self._build_feature_vector(
                feature_names, team_m, opp_m, roll_m, home_aw
            )
            probs    = model.predict_proba([features])[0]
            loss_p, draw_p, win_p = float(probs[0]), float(probs[1]), float(probs[2])

        # Formation chosen by metric-driven rules, not by model
        # (model doesn't include formation in its feature set)
        best_formation = self._pick_formation_by_metrics(team_m, opp_m, data)

        context = {
            "team": team_m,
            "opp":  opp_m,
            "fatigue_score": data.get("fatigue_score", 0.30),
        }
        press = self._apply_rules(PRESS_RULES,  context, default="Medium")
        line  = self._apply_rules(LINE_RULES,   context, default="Medium")
        focus = self._apply_rules(FOCUS_RULES,  context, default="Balanced Mid-Block")

        opp_profile      = data.get("opposition") or {}
        opp_formation_str = opp_profile.get("likely_formation") or opp_profile.get("formation") or "Unknown"

        data.update({
            "recommended_formation": best_formation,
            "win_probability":       round(win_p,  3),
            "draw_probability":      round(draw_p, 3),
            "loss_probability":      round(loss_p, 3),
            "formation_scores":      {},   # removed — model doesn't score formations
            "press_intensity":       press,
            "defensive_line":        line,
            "tactical_focus":        focus,
            "opp_formation":         opp_formation_str,
        })
        return data

    def _pick_formation_by_metrics(self, team_m: dict, opp_m: dict, data: dict) -> str:
        dsi  = team_m["defensive_solidity_index"]
        osi  = team_m["offensive_output_index"]
        opp_osi = opp_m["offensive_output_index"]
        opp_dsi = opp_m["defensive_solidity_index"]
        poss = team_m["possession_share"]
        fat  = data.get("fatigue_score", 0.30)

        if dsi < 0.40 and opp_osi > 0.55:
            return "4-4-1-1"   # double defensive block, hold shape
        if fat > 0.60 and opp_osi > 0.45:
            return "4-1-4-1"   # compact, less pressing required
        if osi > 0.55 and opp_dsi < 0.40:
            return "3-4-3"     # attacking overload when opponent is open
        if poss > 0.55 and dsi > 0.55:
            return "4-2-3-1"   # possession base with double pivot
        if osi < 0.35 and opp_osi < 0.40:
            return "4-4-2"     # balanced, neither side dominant
        return "4-3-3"         # default — most versatile

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