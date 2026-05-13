import random

# ---------------------------------------------------------------------------
# Position mapping — opposition mention → your player positions at risk/benefit
# ---------------------------------------------------------------------------

# When opposition has a weakness at position X, which of YOUR players exploit it
OPP_WEAKNESS_EXPLOITERS = {
    "left_back":    ["RW", "RM", "RB"],   # their LB weak → your right side attacks
    "right_back":   ["LW", "LM", "LB"],   # their RB weak → your left side attacks
    "centre_back":  ["ST", "CF", "SS"],   # their CB weak → your strikers
    "striker":      ["CB"],               # their ST weak → less aerial threat
    "winger":       ["CB", "RB", "LB"],   # their winger weak → wide defenders safe
    "goalkeeper":   ["ST", "CF", "SS"],   # their GK weak → shots from range
    "midfielder":   ["CM", "CAM", "CDM"], # their mid weak → your midfield can dominate
    "fullback":     ["ST", "CF", "LW", "RW"],
}

# When opposition has a strength at position X, which of YOUR players are at risk
OPP_STRENGTH_THREATS = {
    "left_back":    ["LW", "LM"],         # their LB strong → your left winger will struggle
    "right_back":   ["RW", "RM"],         # their RB strong → your right winger will struggle
    "centre_back":  ["ST", "CF", "SS"],   # their CB strong → your strikers have it tough
    "striker":      ["CB"],               # their ST strong → your CBs under pressure
    "winger":       ["RB", "LB"],         # their winger strong → your fullbacks at risk
    "goalkeeper":   [],                   # strong GK → general note, no specific matchup
    "midfielder":   ["CM", "CDM"],        # their mid strong → your midfield pressed
    "fullback":     ["LW", "RW"],
}

# Attribute descriptors that signal weakness
WEAKNESS_DESCRIPTORS = {
    "slow", "lacks pace", "not quick", "poor touch", "heavy touch",
    "not technical", "poor in the air", "weak aerially", "weak", "poor",
    "inexperienced", "raw", "young",
}

# Attribute descriptors that signal strength
STRENGTH_DESCRIPTORS = {
    "fast", "quick", "pacey", "rapid", "strong", "technical", "skilful",
    "experienced", "dangerous", "good", "aerial threat", "strong in the air",
}

# General attribute matchup thresholds (1-20 scale)
PACE_LOW_THRESHOLD    = 12   # below this → vulnerability vs pace threat
PACE_HIGH_THRESHOLD   = 15   # above this → exploit vs slow defender
HEADING_HIGH          = 15
TACKLING_HIGH         = 15


# ---------------------------------------------------------------------------
# Variation pools
# ---------------------------------------------------------------------------

EXPLOIT_TEMPLATES = [
    "{your_name} ({your_pos}, pace {your_val:.1f}) can exploit {opp_pos} — {opp_descriptor}.",
    "{opp_pos} is {opp_descriptor} — {your_name} ({your_pos}) has the pace ({your_val:.1f}) to hurt them.",
    "Target {opp_pos}: {opp_descriptor}. {your_name} pace {your_val:.1f} is a weapon here.",
    "Exploit: {your_name} ({your_val:.1f} pace) vs their {opp_pos} who is {opp_descriptor}.",
]

VULNERABILITY_TEMPLATES = [
    "{your_name} ({your_pos}, pace {your_val:.1f}) could be exposed by their {opp_pos} — {opp_descriptor}.",
    "Risk: their {opp_pos} is {opp_descriptor} — {your_name} ({your_pos}) pace {your_val:.1f} may struggle.",
    "{your_name} ({your_pos}) pace {your_val:.1f} is a concern against their {opp_pos} ({opp_descriptor}).",
    "Watch {your_name} ({your_pos}) — pace {your_val:.1f} vs a {opp_descriptor} {opp_pos} is a mismatch.",
]

AERIAL_EXPLOIT_TEMPLATES = [
    "{your_name} ({your_pos}, heading {your_val:.1f}) can dominate their {opp_pos} in the air — {opp_descriptor}.",
    "Aerial advantage: {your_name} heading {your_val:.1f} vs their {opp_pos} who is {opp_descriptor}.",
    "{opp_pos} is {opp_descriptor} — exploit with crosses to {your_name} (heading {your_val:.1f}).",
]

AERIAL_VULNERABILITY_TEMPLATES = [
    "{your_name} ({your_pos}) could be troubled aerially by their {opp_pos} — {opp_descriptor}.",
    "Aerial risk: their {opp_pos} is {opp_descriptor} against {your_name} ({your_pos}).",
    "Watch set pieces — their {opp_pos} is {opp_descriptor}, {your_name} ({your_pos}) may struggle.",
]

GENERAL_PRESS_NOTE = [
    "Opposition press style is {press} — conserve energy in possession, don't get pinned.",
    "{press} press from {opp} — play through quickly or go direct to avoid being pressed.",
    "Expect a {press} press — your midfield needs to be sharp in transition.",
]

GENERAL_SET_PIECE_NOTE = [
    "Opposition set piece threat rated {threat} — defensive organisation at corners is critical.",
    "Be alert at set pieces — opposition rated {threat} threat from dead balls.",
    "{threat} set piece danger from {opp} — ensure marking assignments are clear.",
]


def _pick(pool: list, **kwargs) -> str:
    return random.choice(pool).format(**kwargs)


# ---------------------------------------------------------------------------
# Matchup layer
# ---------------------------------------------------------------------------

class MatchupLayer:
    """
    Cross-references opposition parsed attributes against your squad's
    attribute profiles to produce specific exploit and vulnerability flags.

    Works with what's already in the DB:
    - opposition_profiles.attributes JSONB (from OppositionParser)
    - player_attribute_profiles (pace, heading, tackling etc — 1-20 scale)
    - starting_xi with specific_position and broad_position
    """

    def detect(self, data: dict) -> dict:
        opposition  = data.get("opposition", {})
        starting_xi = data.get("starting_xi", [])

        if not opposition or not starting_xi:
            data["matchup_exploits"]       = []
            data["matchup_vulnerabilities"] = []
            data["matchup_general_notes"]   = []
            return data

        opp_attrs   = opposition.get("attributes", {})
        opp_name    = data.get("opponent_name", "Opposition")
        press_style = opposition.get("press_style")
        set_piece   = opposition.get("set_piece_threat")

        exploits       = []
        vulnerabilities = []
        general_notes  = []

        # --- Position-specific matchup flags ---
        for opp_pos, descriptor in opp_attrs.items():
            if not isinstance(descriptor, str):
                continue

            descriptor_clean = descriptor.strip().lower()
            is_weakness = any(w in descriptor_clean for w in WEAKNESS_DESCRIPTORS)
            is_strength = any(s in descriptor_clean for s in STRENGTH_DESCRIPTORS)

            if not is_weakness and not is_strength:
                continue

            if is_weakness:
                your_positions = OPP_WEAKNESS_EXPLOITERS.get(opp_pos, [])
                candidates = [
                    p for p in starting_xi
                    if p.get("specific_position") in your_positions
                    or p.get("broad_position") in your_positions
                ]
                for p in candidates[:1]:   # cap at 1 per opposition position
                    pace = p.get("attributes", {}).get("pace")
                    if pace and pace >= PACE_HIGH_THRESHOLD:
                        exploits.append(
                            _pick(
                                EXPLOIT_TEMPLATES,
                                your_name=p["name"],
                                your_pos=p.get("specific_position", p.get("broad_position")),
                                your_val=pace,
                                opp_pos=opp_pos.replace("_", " "),
                                opp_descriptor=descriptor_clean,
                            )
                        )
                    heading = p.get("attributes", {}).get("heading")
                    if heading and heading >= HEADING_HIGH and "aerial" in descriptor_clean:
                        exploits.append(
                            _pick(
                                AERIAL_EXPLOIT_TEMPLATES,
                                your_name=p["name"],
                                your_pos=p.get("specific_position", p.get("broad_position")),
                                your_val=heading,
                                opp_pos=opp_pos.replace("_", " "),
                                opp_descriptor=descriptor_clean,
                            )
                        )

            if is_strength:
                your_positions = OPP_STRENGTH_THREATS.get(opp_pos, [])
                candidates = [
                    p for p in starting_xi
                    if p.get("specific_position") in your_positions
                    or p.get("broad_position") in your_positions
                ]
                for p in candidates[:1]:
                    pace = p.get("attributes", {}).get("pace")
                    if pace and pace <= PACE_LOW_THRESHOLD and "pace" in descriptor_clean:
                        vulnerabilities.append(
                            _pick(
                                VULNERABILITY_TEMPLATES,
                                your_name=p["name"],
                                your_pos=p.get("specific_position", p.get("broad_position")),
                                your_val=pace,
                                opp_pos=opp_pos.replace("_", " "),
                                opp_descriptor=descriptor_clean,
                            )
                        )
                    heading = p.get("attributes", {}).get("heading")
                    if heading and heading <= HEADING_HIGH and "aerial" in descriptor_clean:
                        vulnerabilities.append(
                            _pick(
                                AERIAL_VULNERABILITY_TEMPLATES,
                                your_name=p["name"],
                                your_pos=p.get("specific_position", p.get("broad_position")),
                                opp_pos=opp_pos.replace("_", " "),
                                opp_descriptor=descriptor_clean,
                            )
                        )

        # --- General attribute flags (pace, aerial at team level) ---
        general_pace = opp_attrs.get("pace")
        if general_pace == "high":
            slow_defenders = [
                p for p in starting_xi
                if p.get("broad_position") == "DEF"
                and (p.get("attributes", {}).get("pace") or 20) <= PACE_LOW_THRESHOLD
            ]
            for p in slow_defenders[:2]:
                pace_val = p.get("attributes", {}).get("pace", 0)
                vulnerabilities.append(
                    _pick(
                        VULNERABILITY_TEMPLATES,
                        your_name=p["name"],
                        your_pos=p.get("specific_position", "DEF"),
                        your_val=pace_val,
                        opp_pos="attackers",
                        opp_descriptor="fast",
                    )
                )

        elif general_pace == "low":
            fast_attackers = [
                p for p in starting_xi
                if p.get("broad_position") == "FWD"
                and (p.get("attributes", {}).get("pace") or 0) >= PACE_HIGH_THRESHOLD
            ]
            for p in fast_attackers[:2]:
                pace_val = p.get("attributes", {}).get("pace", 0)
                exploits.append(
                    _pick(
                        EXPLOIT_TEMPLATES,
                        your_name=p["name"],
                        your_pos=p.get("specific_position", "FWD"),
                        your_val=pace_val,
                        opp_pos="defence",
                        opp_descriptor="slow",
                    )
                )

        # --- Press style note ---
        if press_style:
            general_notes.append(
                _pick(GENERAL_PRESS_NOTE, press=press_style, opp=opp_name)
            )

        # --- Set piece threat note ---
        if set_piece and set_piece in ("high", "medium"):
            general_notes.append(
                _pick(GENERAL_SET_PIECE_NOTE, threat=set_piece.capitalize(), opp=opp_name)
            )

        data["matchup_exploits"]        = exploits[:4]        # cap — keep report readable
        data["matchup_vulnerabilities"] = vulnerabilities[:4]
        data["matchup_general_notes"]   = general_notes

        return data