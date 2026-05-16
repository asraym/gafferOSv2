from sqlalchemy.orm import Session
from core.match_data_fetcher import MatchDataFetcher
from core.team_metric_calculator import TeamMetricCalculator
from core.tactical_reasoner import TacticalReasoner
from core.player_ranker import PlayerRanker
from core.matchup_layer import MatchupLayer
from core.explainer import Explainer
from core.tactical_style import TacticalStyle
from core.tactical_constraints import TacticalConstraints


class TacticalEngine:
    """
    Orchestrates the full analysis pipeline for POST /api/matches/analyse.

    Execution order:
    1. MatchDataFetcher         → pull everything from DB
    2. PlayerRanker             → form scores + fatigue (needed by TacticalReasoner)
    3. TeamMetricCalculator     → 7 model metrics + data_mode detection
    4. MatchupLayer (pass 1)    → pre-formation vulnerability flags (#11)
                                  runs on full squad before XI is selected
                                  TacticalReasoner reads matchup_vulnerabilities
                                  to avoid exposing flagged players in formation
    5. TacticalReasoner         → ML model → formation, probabilities, press/line/focus
    6. _fill_squad()            → XI selection now that formation is known
    7. MatchupLayer (pass 2)    → re-runs on starting_xi only for player-specific flags
                                  replaces pass 1 output with more precise results
    8. Explainer                → plain English report (picks up all layer outputs)
    """

    def __init__(self):
        self.fetcher    = MatchDataFetcher()
        self.ranker     = PlayerRanker()
        self.calculator = TeamMetricCalculator()
        self.reasoner   = TacticalReasoner()
        self.matchup    = MatchupLayer()
        self.explainer  = Explainer()
        self._style_deriver = TacticalStyle()
        self.constraints = TacticalConstraints()

    def analyse(self, db: Session, match_id: int, team_id: int) -> dict:
        data = self.fetcher.fetch(db, match_id, team_id)
        data = self.ranker.rank(data)
        data = self.calculator.calculate(data)
        data = self._matchup_pass(data, use_full_squad=True)
        data = self.reasoner.reason(data)

        # Handle default mode — no formation recommended (#9)
        if data.get("recommended_formation") is None:
            data["starting_xi"]         = []
            data["bench"]               = []
            data["rotation_suggestions"] = [
                "Insufficient data — submit match snapshots or scouting notes "
                "before requesting tactical analysis."
            ]
            data["squad_style"]             = {}
            data["coherence_score"]         = None
            data["constraint_violations"]   = [] 
        else:
            data = self._fill_squad(data)
            data = self._matchup_pass(data, use_full_squad=False)
            data = self._style_deriver.derive(data)
            data = self.constraints.validate(data)

        data = self.explainer.explain(data)
        return self._build_response(data)
        self._store_recommendation(db, match_id, data)
    
    def _store_recommendation(self, db, match_id: int, data: dict) -> None:
        """
        Stores engine recommendations into the match row immediately.
        Coach doesn't need to submit feedback for the prediction to be recorded.
        """
        try:
            from db.models import Match
            match = db.query(Match).filter(Match.id == match_id).first()
            if not match:
                return
            fields = {
                "recommended_formation": data.get("recommended_formation"),
                "recommended_line":      data.get("defensive_line"),
                "recommended_press":     data.get("press_intensity"),
                "recommended_focus":     data.get("tactical_focus"),
                "predicted_win_prob":    data.get("win_probability"),
                "squad_style":           data.get("squad_style", {}).get("style"),
                "coherence_score":       data.get("coherence_score"),
            }
            for field, val in fields.items():
                if val is not None and hasattr(match, field):
                    setattr(match, field, val)
            db.commit()
        except Exception as e:
            # Non-fatal — don't crash the analysis if storage fails
            print(f"[Engine] Failed to store recommendation: {e}")

    def _matchup_pass(self, data: dict, use_full_squad: bool) -> dict:
        """
        Run MatchupLayer against either the full squad (pre-formation pass)
        or the starting_xi only (post-formation pass).
        Temporarily swaps starting_xi so MatchupLayer always reads from
        the same key, then restores it.
        """
        if use_full_squad:
            original_xi = data.get("starting_xi", [])
            data["starting_xi"] = data.get("players", [])
            data = self.matchup.detect(data)
            data["starting_xi"] = original_xi
        else:
            data = self.matchup.detect(data)
        return data

    def _fill_squad(self, data: dict) -> dict:
        players     = data.get("players", [])
        formation   = data.get("recommended_formation", "4-3-3")
        form_scores = {p["player_id"]: p.get("form_score") for p in players}

        slots = self.ranker.FORMATION_SLOTS.get(
            formation,
            self.ranker.FORMATION_SLOTS["4-3-3"]
        )
        starting_xi, used_ids = self.ranker._fill_xi(players, slots, form_scores)
        bench = [p for p in players if p["player_id"] not in used_ids]
        rotation = self.ranker._generate_rotation(
            starting_xi,
            bench,
            data.get("team_fatigue_score", 0.30),
            data.get("press_intensity", "Medium"),
            data.get("match_risk_level", "Medium"),   # new
            data.get("snapshots", []),                 # new
        )

        data["starting_xi"]          = starting_xi
        data["bench"]                = bench
        data["rotation_suggestions"] = rotation
        return data
        
    def _build_response(self, data: dict) -> dict:
        formation = data.get("recommended_formation")
        return {
            # Identifiers
            "match_id":              data["match_id"],
            "team_id":               data["team_id"],
            "opponent_name":         data["opponent_name"],
            "match_date":            data["match_date"],
            "venue":                 data.get("home_away"),

            # Data quality
            "data_mode":             data["data_mode"],
            "missing_fields":        data.get("missing_fields", []),

            # ML outputs
            "win_probability":       data["win_probability"],
            "draw_probability":      data["draw_probability"],
            "loss_probability":      data["loss_probability"],

            # Tactical decisions
            # None when data_mode is "default" — UI should show
            # "Insufficient data" rather than a formation card (#9)
            "recommended_formation": formation,
            "press_intensity":       data["press_intensity"],
            "defensive_line":        data["defensive_line"],
            "tactical_focus":        data["tactical_focus"],
            "opp_formation":         data.get("opp_formation", "Unknown"),

            # Squad
            "starting_xi":           data.get("starting_xi", []),
            "bench":                 data.get("bench", []),
            "rotation_suggestions":  data.get("rotation_suggestions", []),
            "team_fatigue_score":    data.get("team_fatigue_score", 0.30),
            "squad_style":           data.get("squad_style", {}),
            "coherence_score":       data.get("coherence_score", {}),
            "constraint_violations": data.get("constraint_violations", {}),

            # Metrics
            "team_metrics":          data.get("team_metrics", {}),
            "opp_metrics":           data.get("opp_metrics", {}),

            # Matchup layer
            "matchup_exploits":        data.get("matchup_exploits", []),
            "matchup_vulnerabilities": data.get("matchup_vulnerabilities", []),
            "matchup_general_notes":   data.get("matchup_general_notes", []),

            # Report
            "reasoning":             data["reasoning"],
        }