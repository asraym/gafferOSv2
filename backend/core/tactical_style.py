
# Derives a squad style vector from player traits and team metrics.
# Used by:
#   - TacticalReasoner  — to align formation with squad identity
#   - TacticalConstraints — to validate coherence of recommendations
#   - Feedback storage  — so the model can learn which styles win
#
# This is a stub. Rules grow as match feedback accumulates and
# incoherent combinations are identified from outcome audit queries.

from core.player_traits import (
    OFFENSIVE_TRAITS,
    DEFENSIVE_TRAITS,
    PROGRESSIVE_TRAITS,
    PRESS_TRAITS,
    CREATOR_TRAITS,
    AERIAL_TRAITS,
)

# ---------------------------------------------------------------------------
# Style labels
# ---------------------------------------------------------------------------

STYLES = [
    "direct",        # long ball, target man, aerial
    "possession",    # short pass, build-up, patient
    "counter",       # fast transitions, low block, pace
    "pressing",      # high press, gegenpressing, high line
    "hybrid",        # no dominant style — balanced
]

TEMPO_LEVELS  = ["high", "medium", "low"]
WIDTH_LEVELS  = ["wide", "balanced", "narrow"]
BLOCK_LEVELS  = ["high", "mid", "low"]


# ---------------------------------------------------------------------------
# Style derivation
# ---------------------------------------------------------------------------

class TacticalStyle:
    """
    Derives a style vector from squad trait profiles and team metrics.
    Returns a dict that feeds into TacticalConstraints and feedback storage.
    """

    def derive(self, data: dict) -> dict:
        players    = data.get("players", [])
        tm         = data.get("team_metrics", {})
        press      = data.get("press_intensity", "Medium")
        line       = data.get("defensive_line", "Medium")
        formation  = data.get("recommended_formation", "4-3-3")

        style  = self._derive_style(players, tm)
        tempo  = self._derive_tempo(players, press, tm)
        width  = self._derive_width(players, formation)
        block  = self._derive_block(line, press)

        style_vector = {
            "style":  style,
            "tempo":  tempo,
            "width":  width,
            "block":  block,
        }

        data["squad_style"] = style_vector
        return data

    def _derive_style(self, players: list, tm: dict) -> str:
        if not players:
            return "hybrid"

        trait_counts = {
            "aerial":      0,
            "pressing":    0,
            "progressive": 0,
            "creative":    0,
            "defensive":   0,
        }

        for p in players:
            traits = p.get("traits", [])
            trait_counts["aerial"]      += sum(1 for t in traits if t in AERIAL_TRAITS)
            trait_counts["pressing"]    += sum(1 for t in traits if t in PRESS_TRAITS)
            trait_counts["progressive"] += sum(1 for t in traits if t in PROGRESSIVE_TRAITS)
            trait_counts["creative"]    += sum(1 for t in traits if t in CREATOR_TRAITS)
            trait_counts["defensive"]   += sum(1 for t in traits if t in DEFENSIVE_TRAITS)

        n = max(len(players), 1)

        # Normalise to per-player rates
        aerial_rate      = trait_counts["aerial"]      / n
        pressing_rate    = trait_counts["pressing"]    / n
        progressive_rate = trait_counts["progressive"] / n
        creative_rate    = trait_counts["creative"]    / n

        # Metric signals
        pss = tm.get("passing_stability_index", 0.78)
        pos = tm.get("possession_share", 0.50)
        osi = tm.get("offensive_output_index", 0.38)

        # Style decision — order matters
        # Direct: aerial dominance is the clearest signal
        if aerial_rate > 0.3:
            return "direct"

        # Pressing: press traits + high line
        if pressing_rate > 0.25:
            return "pressing"

        # Possession: passing stability + possession share + progressive traits
        if pss >= 0.80 and pos >= 0.55 and progressive_rate > 0.15:
            return "possession"

        # Counter: high offensive output but low possession (fast transitions)
        if osi > 0.45 and pos < 0.48 and creative_rate < 0.15:
            return "counter"

        return "hybrid"

    def _derive_tempo(self, players: list, press: str, tm: dict) -> str:
        # Press intensity is the primary tempo signal
        if press == "High":
            return "high"
        if press == "Low":
            return "low"

        # Medium press — check squad traits for nuance
        press_count = sum(
            1 for p in players
            if any(t in PRESS_TRAITS for t in p.get("traits", []))
        )
        if press_count >= 3:
            return "high"

        pss = tm.get("passing_stability_index", 0.78)
        if pss >= 0.82:
            return "medium"  # patient build-up, controlled tempo

        return "medium"

    def _derive_width(self, players: list, formation: str) -> str:
        # Formation is the primary width signal
        wide_formations = {"4-3-3", "4-4-2", "3-4-3"}
        narrow_formations = {"4-2-3-1", "4-1-4-1", "4-4-1-1"}

        if formation in wide_formations:
            base = "wide"
        elif formation in narrow_formations:
            base = "narrow"
        else:
            base = "balanced"

        # Offensive fullback traits push width further
        offensive_fbs = sum(
            1 for p in players
            if p.get("broad_position") == "DEF"
            and p.get("tactical_profile", {}).get("offensive_tendency", 0) > 0.3
        )
        if offensive_fbs >= 2 and base == "balanced":
            return "wide"

        return base

    def _derive_block(self, line: str, press: str) -> str:
        # Defensive line is the primary block signal
        if line == "High":
            return "high"
        if line == "Deep":
            return "low"

        # Medium line — press refines it
        if press == "High":
            return "high"
        if press == "Low":
            return "low"

        return "mid"