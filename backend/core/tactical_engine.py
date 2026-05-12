from sqlalchemy.orm import Session
from core.match_data_fetcher import MatchDataFetcher
from core.team_metric_calculator import TeamMetricCalculator
from core.tactical_reasoner import TacticalReasoner
from core.player_ranker import PlayerRanker
from core.explainer import Explainer


class TacticalEngine:
    """
    Orchestrates the full analysis pipeline for POST /api/matches/analyse.

    Execution order:
    1. MatchDataFetcher    → pull everything from DB
    2. PlayerRanker        → form scores + fatigue (needed by TacticalReasoner)
    3. TeamMetricCalculator → 7 model metrics + data_mode detection
    4. TacticalReasoner    → ML model → formation, probabilities, press/line/focus
    5. Explainer           → plain English report
    """

    def __init__(self):
        self.fetcher    = MatchDataFetcher()
        self.ranker     = PlayerRanker()
        self.calculator = TeamMetricCalculator()
        self.reasoner   = TacticalReasoner()
        self.explainer  = Explainer()

    def analyse(self, db: Session, match_id: int, team_id: int) -> dict:
        data = self.fetcher.fetch(db, match_id, team_id)
        data = self.ranker.rank(data)           # needs to run before calculator (provides fatigue_score)
        data = self.calculator.calculate(data)
        data = self.reasoner.reason(data)
        data = self._fill_squad(data)
        data = self.explainer.explain(data)
        return self._build_response(data)
    def _fill_squad(self, data: dict) -> dict:
        players    = data.get("players", [])
        formation  = data.get("recommended_formation", "4-3-3")
        form_scores = {p["player_id"]: p.get("form_score") for p in players}

        slots = self.ranker.FORMATION_SLOTS.get(formation, self.ranker.FORMATION_SLOTS["4-3-3"])
        starting_xi, used_ids = self.ranker._fill_xi(players, slots, form_scores)
        bench = [p for p in players if p["player_id"] not in used_ids]
        rotation = self.ranker._generate_rotation(starting_xi, bench, data.get("team_fatigue_score", 0.30), data.get("press_intensity", "Medium")
        )

        data["starting_xi"]          = starting_xi
        data["bench"]                = bench
        data["rotation_suggestions"] = rotation
        return data

    def _build_response(self, data: dict) -> dict:
        return {
            # Identifiers
            "match_id":             data["match_id"],
            "team_id":              data["team_id"],
            "opponent_name":        data["opponent_name"],
            "match_date":           data["match_date"],
            "venue":                data.get("home_away"),

            # Data quality
            "data_mode":            data["data_mode"],
            "missing_fields":       data.get("missing_fields", []),

            # ML outputs
            "win_probability":      data["win_probability"],
            "draw_probability":     data["draw_probability"],
            "loss_probability":     data["loss_probability"],
            "formation_scores":     data.get("formation_scores", {}),

            # Tactical decisions
            "recommended_formation": data["recommended_formation"],
            "press_intensity":       data["press_intensity"],
            "defensive_line":        data["defensive_line"],
            "tactical_focus":        data["tactical_focus"],
            "opp_formation":         data.get("opp_formation", "Unknown"),

            # Squad
            "starting_xi":           data.get("starting_xi", []),
            "bench":                 data.get("bench", []),
            "rotation_suggestions":  data.get("rotation_suggestions", []),
            "team_fatigue_score":    data.get("team_fatigue_score", 0.30),

            # Metrics (for display in UI)
            "team_metrics":          data.get("team_metrics", {}),
            "opp_metrics":           data.get("opp_metrics", {}),

            # Report
            "reasoning":             data["reasoning"],
        }