
#
# Validates tactical combinations and scores their coherence.
# Hard constraints block invalid combinations entirely.
# Coherence score (0-1) measures how well tactical pieces fit together.
#
# Used by:
#   - TacticalEngine — to validate recommendations before output
#   - Feedback storage — coherence_score stored per match for model training
#
# Rules grow based on outcome audit queries.
# When a combination consistently underperforms in match feedback,
# add it here as a constraint or adjust its coherence penalty.
#
# Current constraint coverage:
#   - Tempo vs block coherence
#   - Line height vs CB pace
#   - Width vs personnel availability
#   - Press vs fatigue (already in TacticalReasoner — mirrored here for scoring)
#   - Style vs formation alignment

from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Hard constraints
# ---------------------------------------------------------------------------

@dataclass
class ConstraintViolation:
    rule:   str    # short identifier
    reason: str    # human-readable explanation


HARD_CONSTRAINTS = [
    # Tempo vs block
    {
        "id":     "tempo_block_contradiction",
        "reason": "High tempo and low block are contradictory — "
                  "a low block is a defensive posture that conserves energy, "
                  "not compatible with high intensity play.",
        "check":  lambda s, sq, tm: (
            s.get("tempo") == "high" and s.get("block") == "low"
        ),
    },

    # High line without CB pace
    {
        "id":     "high_line_no_cb_pace",
        "reason": "High defensive line requires pace from CBs to recover. "
                  "Average CB pace below 13 makes this suicidal against pace.",
        "check":  lambda s, sq, tm: (
            s.get("block") == "high"
            and _avg_cb_pace(sq) is not None
            and _avg_cb_pace(sq) < 13
        ),
    },

    # Extreme width without wide players
    {
        "id":     "wide_formation_no_wingers",
        "reason": "Wide formation selected but no fit wide players available. "
                  "Width without wide players leaves channels exposed.",
        "check":  lambda s, sq, tm: (
            s.get("width") == "wide"
            and _count_available_wide(sq) < 2
        ),
    },

    # High press with elevated fatigue
    {
        "id":     "high_press_high_fatigue",
        "reason": "High press is not sustainable with elevated squad fatigue. "
                  "Press will drop in the second half leaving the team exposed.",
        "check":  lambda s, sq, tm: (
            s.get("tempo") == "high"
            and tm.get("fatigue_score", 0.30) > 0.65
        ),
    },

    # Direct style with possession-dominant metrics
    # (contradictory — suggests rule misfire)
    {
        "id":     "direct_style_high_possession",
        "reason": "Direct style recommended but team metrics show high possession. "
                  "Style derivation may be misreading the squad.",
        "check":  lambda s, sq, tm: (
            s.get("style") == "direct"
            and tm.get("possession_share", 0.50) > 0.60
            and tm.get("passing_stability_index", 0.78) > 0.82
        ),
    },
]


# ---------------------------------------------------------------------------
# Coherence scoring
# ---------------------------------------------------------------------------

# Each rule contributes a penalty (0.0–1.0) to incoherence.
# coherence_score = 1.0 - total_penalty (clamped to [0, 1])
# Higher coherence = tactical pieces fit together better.

COHERENCE_PENALTIES = [
    # Tempo vs block mismatch (softer than hard constraint)
    {
        "id":      "tempo_block_mismatch",
        "penalty": 0.25,
        "check":   lambda s, sq, tm: (
            s.get("tempo") == "high" and s.get("block") == "mid"
            and s.get("style") not in ("pressing", "counter")
        ),
    },

    # High line without ideal CB pace (not impossible, just risky)
    {
        "id":      "high_line_cb_pace_risk",
        "penalty": 0.15,
        "check":   lambda s, sq, tm: (
            s.get("block") == "high"
            and _avg_cb_pace(sq) is not None
            and 13 <= _avg_cb_pace(sq) < 15
        ),
    },

    # Counter style but slow forwards
    {
        "id":      "counter_slow_forwards",
        "penalty": 0.20,
        "check":   lambda s, sq, tm: (
            s.get("style") == "counter"
            and _avg_fwd_pace(sq) is not None
            and _avg_fwd_pace(sq) < 13
        ),
    },

    # Possession style but low passing stability
    {
        "id":      "possession_low_passing",
        "penalty": 0.20,
        "check":   lambda s, sq, tm: (
            s.get("style") == "possession"
            and tm.get("passing_stability_index", 0.78) < 0.72
        ),
    },

    # Pressing style but low stamina squad
    {
        "id":      "pressing_low_stamina",
        "penalty": 0.20,
        "check":   lambda s, sq, tm: (
            s.get("style") == "pressing"
            and tm.get("fatigue_score", 0.30) > 0.50
        ),
    },

    # Wide formation but narrow playing style
    {
        "id":      "wide_narrow_style_mismatch",
        "penalty": 0.10,
        "check":   lambda s, sq, tm: (
            s.get("width") == "wide"
            and s.get("style") in ("direct", "possession")
            and _count_available_wide(sq) < 3
        ),
    },
]


# ---------------------------------------------------------------------------
# Helper attribute extractors
# ---------------------------------------------------------------------------

def _avg_cb_pace(squad: list) -> Optional[float]:
    paces = [
        p.get("attributes", {}).get("pace")
        for p in squad
        if p.get("specific_position") == "CB"
        and p.get("attributes", {}).get("pace") is not None
    ]
    return round(sum(paces) / len(paces), 1) if paces else None


def _avg_fwd_pace(squad: list) -> Optional[float]:
    paces = [
        p.get("attributes", {}).get("pace")
        for p in squad
        if p.get("broad_position") == "FWD"
        and p.get("attributes", {}).get("pace") is not None
    ]
    return round(sum(paces) / len(paces), 1) if paces else None


def _count_available_wide(squad: list) -> int:
    wide_positions = {"RW", "LW", "RM", "LM", "RWB", "LWB"}
    return sum(
        1 for p in squad
        if p.get("specific_position") in wide_positions
        and p.get("available", True)
    )


# ---------------------------------------------------------------------------
# Main validator
# ---------------------------------------------------------------------------

class TacticalConstraints:
    """
    Validates tactical recommendations and scores their coherence.
    Called by TacticalEngine after TacticalStyle derives the style vector.
    """

    def validate(self, data: dict) -> dict:
        style_vector = data.get("squad_style", {})
        squad        = data.get("players", [])
        tm           = data.get("team_metrics", {})
        tm["fatigue_score"] = data.get("team_fatigue_score", 0.30)

        violations      = self._check_hard_constraints(style_vector, squad, tm)
        coherence_score = self._score_coherence(style_vector, squad, tm)

        data["constraint_violations"] = [
            {"rule": v.rule, "reason": v.reason}
            for v in violations
        ]
        data["coherence_score"] = coherence_score

        # If hard constraints violated, flag in missing_fields so explainer surfaces it
        if violations:
            existing = data.get("missing_fields", [])
            for v in violations:
                existing.append(f"Tactical conflict: {v.reason}")
            data["missing_fields"] = existing

        return data

    def _check_hard_constraints(
        self, style: dict, squad: list, tm: dict
    ) -> list:
        violations = []
        for constraint in HARD_CONSTRAINTS:
            try:
                if constraint["check"](style, squad, tm):
                    violations.append(
                        ConstraintViolation(
                            rule=constraint["id"],
                            reason=constraint["reason"],
                        )
                    )
            except (KeyError, TypeError):
                continue
        return violations

    def _score_coherence(self, style: dict, squad: list, tm: dict) -> float:
        total_penalty = 0.0
        for rule in COHERENCE_PENALTIES:
            try:
                if rule["check"](style, squad, tm):
                    total_penalty += rule["penalty"]
            except (KeyError, TypeError):
                continue
        return round(max(0.0, min(1.0, 1.0 - total_penalty)), 3)