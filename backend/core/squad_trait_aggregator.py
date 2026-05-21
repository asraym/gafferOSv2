# core/squad_trait_aggregator.py
import random
from core.player_traits import get_tactical_profile

# ── Position weights ────────────────────────────────────────────────────────
# How much each broad position contributes to the squad trait profile.
# Outfield only — GK excluded from tactical tendency aggregation.
POSITION_WEIGHTS = {
    "DEF": 0.25,
    "MID": 0.45,
    "FWD": 0.30,
}

# ── Minimum form score to be included in linkup pair ────────────────────────
LINKUP_FORM_THRESHOLD = 0.35

# ── Linkup pair definitions ──────────────────────────────────────────────────
# Each entry: (pos_a, traits_a, pos_b, traits_b, description_templates)
# pos_a / pos_b are broad positions (DEF / MID / FWD)
# traits_a / traits_b are sets — player must have AT LEAST ONE matching trait
LINKUP_DEFINITIONS = [
    {
        "pos_a":     "DEF",
        "traits_a":  {"Progressive Passer", "Ball Playing Defender", "Brings Ball Out Of Defence"},
        "pos_b":     "MID",
        "traits_b":  {"Deep Playmaker", "Dictates Tempo", "Drops Between Centre Backs", "Recycles Possession"},
        "templates": [
            "{a} picks up the ball from deep and finds {b} as the first midfield outlet.",
            "Build-up flows through {a} → {b} — progressive passing from the back.",
            "{a}'s ball-playing ability feeds directly into {b}'s tempo control.",
        ],
        "id": "outlet_from_back",
    },
    {
        "pos_a":     "DEF",
        "traits_a":  {"Overlaps Winger", "Gets Forward Often", "Carries Ball Into Final Third"},
        "pos_b":     "FWD",
        "traits_b":  {"Holds Width", "Cuts Inside", "Combination Player"},
        "templates": [
            "{a} overlaps to provide width while {b} cuts inside — flank overload.",
            "The {a}–{b} combination on the flank creates 2v1 situations.",
            "{a} joins the attack down the flank, {b} moves inside to create space.",
        ],
        "id": "fb_winger_overlap",
    },
    {
        "pos_a":     "MID",
        "traits_a":  {"Box To Box Runner", "Late Runs Into Box", "Vertical Runner", "Attacks Half Spaces"},
        "pos_b":     "FWD",
        "traits_b":  {"Drops Deep To Link Play", "False Nine Tendencies", "Combination Play"},
        "templates": [
            "{b} drops deep to link play, freeing space for {a} to arrive late.",
            "Second-man runs from {a} exploit the space vacated by {b} dropping off.",
            "{b} draws defenders deep — {a} times the run in behind.",
        ],
        "id": "cm_second_runner",
    },
    {
        "pos_a":     "MID",
        "traits_a":  {"Through Ball Specialist", "Tries Killer Balls Often", "Creative Playmaker", "High Creativity"},
        "pos_b":     "FWD",
        "traits_b":  {"Likes To Beat Offside Trap", "Runs In Behind", "Counterattacking Threat", "Moves Into Channels"},
        "templates": [
            "{a} has the vision to find {b} in behind — a direct threat on the counter.",
            "The {a}–{b} combination is the primary transition weapon — {b} runs, {a} delivers.",
            "{b}'s movement off the last line is unlocked by {a}'s passing range.",
        ],
        "id": "through_ball_runner",
    },
    {
        "pos_a":     "MID",
        "traits_a":  {"Combination Play Specialist", "Progressive Carrier", "Progressive Passer"},
        "pos_b":     "FWD",
        "traits_b":  {"Combination Play", "Presses Aggressively", "Dribbles At Defenders"},
        "templates": [
            "{a} and {b} combine in tight spaces to break through the press.",
            "Quick combinations between {a} and {b} in the final third.",
            "{a} drives forward and links with {b} — fluid one-two potential.",
        ],
        "id": "midfield_forward_combo",
    },
    {
        "pos_a":     "DEF",
        "traits_a":  {"Sweeper Tendencies", "Fast Recovery Runner", "Steps Into Midfield"},
        "pos_b":     "MID",
        "traits_b":  {"Counterpresses Aggressively", "High Workrate", "Ball Winner"},
        "templates": [
            "{a} steps forward aggressively — {b} provides defensive cover behind.",
            "Counterpress shape: {b} hunts the ball, {a} sweeps in behind.",
            "{a} and {b} form a high-energy press-and-recover unit.",
        ],
        "id": "press_cover_pair",
    },
]

# ── Defensive shape derivation ───────────────────────────────────────────────
PRESS_TRIGGER_MAP = {
    "high": "on GK distribution and short goal kicks",
    "mid":  "on back-pass to goalkeeper or slow build-up",
    "low":  "in own half only — organised retreat first",
}

TRANSITION_MAP = {
    # (offensive_tendency > threshold, progressive_tendency > threshold) → description
    (True,  True):  "immediate vertical counter — exploit space quickly",
    (True,  False): "direct transition — play forward fast when possible",
    (False, True):  "controlled transition — carry ball forward before committing",
    (False, False): "patient reset — reorganise before building forward",
}


class SquadTraitAggregator:

    def aggregate(self, data: dict) -> dict:
        starting_xi = data.get("starting_xi", [])
        if not starting_xi:
            data["squad_trait_profile"] = {}
            data["linkup_pairs"]        = []
            data["defensive_shape"]     = {}
            return data

        squad_profile  = self._aggregate_profile(starting_xi)
        linkup_pairs   = self._find_linkups(starting_xi)
        defensive_shape = self._derive_defensive_shape(
            squad_profile,
            data.get("defensive_line", "Medium"),   # must match engine output
            data.get("press_intensity", "Medium"),
        )

        data["squad_trait_profile"] = squad_profile
        data["linkup_pairs"]        = linkup_pairs
        data["defensive_shape"]     = defensive_shape
        return data

    # ── Profile aggregation ─────────────────────────────────────────────────

    def _aggregate_profile(self, xi: list) -> dict:
        """
        Weighted average of tactical profile scores across the XI.
        GK excluded. Positions weighted by POSITION_WEIGHTS.
        """
        totals  = {k: 0.0 for k in [
            "offensive_tendency", "defensive_tendency", "progressive_tendency",
            "press_tendency", "creator_tendency", "aerial_tendency"
        ]}
        weight_sum = 0.0

        for player in xi:
            broad = player.get("position", "")
            if broad == "GK":
                continue
            weight = POSITION_WEIGHTS.get(broad, 0.30)
            traits = player.get("traits", [])
            profile = get_tactical_profile(traits)
            for key in totals:
                totals[key] += profile[key] * weight
            weight_sum += weight

        if weight_sum == 0:
            return {k: 0.0 for k in totals}

        return {k: round(v / weight_sum, 3) for k, v in totals.items()}

    # ── Linkup pairs ────────────────────────────────────────────────────────

    def _find_linkups(self, xi: list) -> list:
        """
        Finds up to 4 linkup pairs from the starting XI.
        Both players must meet the form threshold.
        """
        pairs_found = []

        for defn in LINKUP_DEFINITIONS:
            if len(pairs_found) >= 4:
                break

            player_a = self._find_player(xi, defn["pos_a"], defn["traits_a"])
            player_b = self._find_player(xi, defn["pos_b"], defn["traits_b"])

            if not player_a or not player_b:
                continue

            # Both players must clear form threshold
            form_a = player_a.get("form_score") or 0.0
            form_b = player_b.get("form_score") or 0.0
            if form_a < LINKUP_FORM_THRESHOLD or form_b < LINKUP_FORM_THRESHOLD:
                continue

            name_a = player_a.get("name", "Player A")
            name_b = player_b.get("name", "Player B")
            template = random.choice(defn["templates"])

            pairs_found.append({
                "id":          defn["id"],
                "player_a":    name_a,
                "player_b":    name_b,
                "description": template.format(a=name_a, b=name_b),
                "form_a":      round(form_a, 3),
                "form_b":      round(form_b, 3),
            })

        return pairs_found

    def _find_player(self, xi: list, broad_pos: str, required_traits: set):
        """
        Returns the highest-rated player in the XI at the given broad position
        who has at least one of the required traits and clears the form threshold.
        """
        candidates = []
        for p in xi:
            if p.get("position") != broad_pos:
                continue
            if not (set(p.get("traits", [])) & required_traits):
                continue
            form = p.get("form_score") or 0.0
            if form < LINKUP_FORM_THRESHOLD:
                continue
            candidates.append(p)

        if not candidates:
            return None

        # Prefer highest overall_rating, fall back to form_score
        return max(
            candidates,
            key=lambda p: (
                p.get("attributes", {}).get("overall_rating") or 0,
                p.get("form_score") or 0,
            )
        )

    # ── Defensive shape ─────────────────────────────────────────────────────

    def _derive_defensive_shape(
        self,
        profile: dict,
        defensive_line: str,
        press_intensity: str,
    ) -> dict:
        """
        Derives off-ball defensive shape from squad trait profile.
        Block height is consistent with the engine's defensive_line output.
        """
        # Map engine defensive_line → block label (never diverge from engine)
        block_map = {"High": "high", "Medium": "mid", "Deep": "low"}
        block = block_map.get(defensive_line, "mid")

        # Compactness — driven by defensive tendency
        compactness = (
            "compact" if profile.get("defensive_tendency", 0) > 0.45
            else "open"
        )

        # Press trigger — driven by press intensity + press tendency
        press_trigger = PRESS_TRIGGER_MAP.get(
            press_intensity.lower() if press_intensity else "mid",
            PRESS_TRIGGER_MAP["mid"]
        )

        # Transition behaviour — driven by offensive + progressive tendency
        off_high  = profile.get("offensive_tendency", 0) > 0.50
        prog_high = profile.get("progressive_tendency", 0) > 0.50
        transition = TRANSITION_MAP.get((off_high, prog_high), "patient reset — reorganise before building forward")

        # Out of possession shape description
        shape_label = self._shape_label(block, compactness, press_intensity)

        return {
            "block":        block,
            "compactness":  compactness,
            "press_trigger": press_trigger,
            "transition":   transition,
            "shape_label":  shape_label,
        }

    def _shape_label(self, block: str, compactness: str, press_intensity: str) -> str:
        """Human readable shape description for the UI."""
        intensity = press_intensity.lower() if press_intensity else "medium"
        if block == "high" and intensity == "high":
            return "High Press — aggressive out-of-possession shape"
        if block == "high" and intensity == "medium":
            return "High Line — press selectively, recover quickly"
        if block == "mid" and compactness == "compact":
            return "Compact Mid-Block — deny space between the lines"
        if block == "mid" and compactness == "open":
            return "Mid-Block — organised but with press triggers"
        if block == "low" and compactness == "compact":
            return "Deep Compact Block — absorb and counter"
        if block == "low":
            return "Deep Block — defend deep, limit space in behind"
        return "Organised Mid-Block"