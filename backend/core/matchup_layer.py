import random

# ---------------------------------------------------------------------------
# Position mapping
# ---------------------------------------------------------------------------

OPP_WEAKNESS_EXPLOITERS = {
    "left_back":    ["RW", "RM", "RB"],
    "right_back":   ["LW", "LM", "LB"],
    "centre_back":  ["ST", "CF", "SS"],
    "striker":      ["CB"],
    "winger":       ["CB", "RB", "LB"],
    "goalkeeper":   ["ST", "CF", "SS"],
    "midfielder":   ["CM", "CAM", "CDM"],
    "fullback":     ["ST", "CF", "LW", "RW"],
}

OPP_STRENGTH_THREATS = {
    "left_back":    ["LW", "LM"],
    "right_back":   ["RW", "RM"],
    "centre_back":  ["ST", "CF", "SS"],
    "striker":      ["CB"],
    "winger":       ["RB", "LB"],
    "goalkeeper":   [],
    "midfielder":   ["CM", "CDM"],
    "fullback":     ["LW", "RW"],
}

WEAKNESS_DESCRIPTORS = {
    "slow", "lacks pace", "not quick", "poor touch", "heavy touch",
    "not technical", "poor in the air", "weak aerially", "weak", "poor",
    "inexperienced", "raw", "young",
}

STRENGTH_DESCRIPTORS = {
    "fast", "quick", "pacey", "rapid", "strong", "technical", "skilful",
    "experienced", "dangerous", "good", "aerial threat", "strong in the air",
    "dribbler", "direct", "tricky",
}

# Attribute thresholds (1-20 scale)
PACE_LOW_THRESHOLD     = 12   # below this → vulnerability vs pace threat
PACE_HIGH_THRESHOLD    = 15   # above this → exploit vs slow defender
HEADING_HIGH           = 15   # above this → aerial exploit
HEADING_LOW_THRESHOLD  = 11   # fix #14 — below this → aerial vulnerability (was wrongly using HEADING_HIGH)
TACKLING_LOW_THRESHOLD = 12   # below this → vulnerability vs dribbler
PASSING_LOW_THRESHOLD  = 12   # below this → vulnerability vs high press


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

TACKLING_VULNERABILITY_TEMPLATES = [
    "{your_name} ({your_pos}, tackling {your_val:.1f}) may be beaten by their {opp_pos} — {opp_descriptor}.",
    "Risk: their {opp_pos} is {opp_descriptor} — {your_name} tackling {your_val:.1f} could be a problem.",
    "Watch {your_name} ({your_pos}) vs their {opp_descriptor} {opp_pos} — tackling only {your_val:.1f}.",
]

PASSING_VULNERABILITY_TEMPLATES = [
    "{your_name} ({your_pos}, passing {your_val:.1f}) could be pressed into errors — opposition press is {opp_descriptor}.",
    "High press risk: {your_name} ({your_pos}) passing {your_val:.1f} under a {opp_descriptor} press.",
    "{your_name} ({your_pos}) passing {your_val:.1f} — could struggle to play through a {opp_descriptor} press.",
]

ST_AERIAL_EXPLOIT_TEMPLATES = [
    "{your_name} ({your_pos}, heading {your_val:.1f}) can exploit aerial weakness in their defence.",
    "Aerial platform: {your_name} heading {your_val:.1f} vs an opposition weak in the air.",
    "Target {your_name} ({your_pos}) from set pieces — heading {your_val:.1f} vs weak aerial defence.",
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


def _pick(pool: list, seed: int = None, **kwargs) -> str:
    """Pick a template deterministically using seed, then format it."""
    rng = random.Random(seed)  # fix #16 — seeded per call, deterministic per match
    return rng.choice(pool).format(**kwargs)


# ---------------------------------------------------------------------------
# Matchup layer
# ---------------------------------------------------------------------------

class MatchupLayer:
    """
    Cross-references opposition parsed attributes against your squad's
    attribute profiles to produce specific exploit and vulnerability flags.
    """

    def detect(self, data: dict) -> dict:
        opposition  = data.get("opposition", {})
        starting_xi = data.get("starting_xi", [])

        if not opposition or not starting_xi:
            data["matchup_exploits"]        = []
            data["matchup_vulnerabilities"] = []
            data["matchup_general_notes"]   = []
            return data

        # fix #16 — seed derived from match_id for deterministic output per match
        match_id   = data.get("match_id", 0)
        seed_base  = match_id * 1000  # offset per flag position below

        opp_attrs   = opposition.get("attributes", {})
        opp_name    = data.get("opponent_name", "Opposition")
        press_style = opposition.get("press_style") or ""
        set_piece   = opposition.get("set_piece_threat")

        exploits        = []
        vulnerabilities = []
        general_notes   = []
        flag_index      = 0  # increments per flag so each gets a unique seed

        # ── Position-specific matchup flags ──
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
                for p in candidates[:1]:
                    pace = p.get("attributes", {}).get("pace")
                    if pace and pace >= PACE_HIGH_THRESHOLD:
                        exploits.append(_pick(
                            EXPLOIT_TEMPLATES,
                            seed=seed_base + flag_index,
                            your_name=p["name"],
                            your_pos=p.get("specific_position", p.get("broad_position")),
                            your_val=pace,
                            opp_pos=opp_pos.replace("_", " "),
                            opp_descriptor=descriptor_clean,
                        ))
                        flag_index += 1

                    heading = p.get("attributes", {}).get("heading")
                    if heading and heading >= HEADING_HIGH and "aerial" in descriptor_clean:
                        exploits.append(_pick(
                            AERIAL_EXPLOIT_TEMPLATES,
                            seed=seed_base + flag_index,
                            your_name=p["name"],
                            your_pos=p.get("specific_position", p.get("broad_position")),
                            your_val=heading,
                            opp_pos=opp_pos.replace("_", " "),
                            opp_descriptor=descriptor_clean,
                        ))
                        flag_index += 1

            if is_strength:
                your_positions = OPP_STRENGTH_THREATS.get(opp_pos, [])
                candidates = [
                    p for p in starting_xi
                    if p.get("specific_position") in your_positions
                    or p.get("broad_position") in your_positions
                ]
                for p in candidates[:1]:
                    # Pace vulnerability
                    pace = p.get("attributes", {}).get("pace")
                    if pace and pace <= PACE_LOW_THRESHOLD and (
                        "pace" in descriptor_clean or "fast" in descriptor_clean
                        or "quick" in descriptor_clean
                    ):
                        vulnerabilities.append(_pick(
                            VULNERABILITY_TEMPLATES,
                            seed=seed_base + flag_index,
                            your_name=p["name"],
                            your_pos=p.get("specific_position", p.get("broad_position")),
                            your_val=pace,
                            opp_pos=opp_pos.replace("_", " "),
                            opp_descriptor=descriptor_clean,
                        ))
                        flag_index += 1

                    # Aerial vulnerability — fix #14: use HEADING_LOW_THRESHOLD not HEADING_HIGH
                    heading = p.get("attributes", {}).get("heading")
                    if heading and heading <= HEADING_LOW_THRESHOLD and "aerial" in descriptor_clean:
                        vulnerabilities.append(_pick(
                            AERIAL_VULNERABILITY_TEMPLATES,
                            seed=seed_base + flag_index,
                            your_name=p["name"],
                            your_pos=p.get("specific_position", p.get("broad_position")),
                            opp_pos=opp_pos.replace("_", " "),
                            opp_descriptor=descriptor_clean,
                        ))
                        flag_index += 1

                    # Tackling vs dribbler vulnerability (new depth)
                    tackling = p.get("attributes", {}).get("tackling")
                    if tackling and tackling <= TACKLING_LOW_THRESHOLD and (
                        "dribbl" in descriptor_clean or "skilful" in descriptor_clean
                        or "technical" in descriptor_clean or "tricky" in descriptor_clean
                    ):
                        vulnerabilities.append(_pick(
                            TACKLING_VULNERABILITY_TEMPLATES,
                            seed=seed_base + flag_index,
                            your_name=p["name"],
                            your_pos=p.get("specific_position", p.get("broad_position")),
                            your_val=tackling,
                            opp_pos=opp_pos.replace("_", " "),
                            opp_descriptor=descriptor_clean,
                        ))
                        flag_index += 1

        # ── Passing vs high press vulnerability (new depth) ──
        if "high" in press_style.lower():
            midfielders_at_risk = [
                p for p in starting_xi
                if p.get("specific_position") in ("CDM", "CM")
                and (p.get("attributes", {}).get("passing") or 20) <= PASSING_LOW_THRESHOLD
            ]
            for p in midfielders_at_risk[:2]:
                passing_val = p.get("attributes", {}).get("passing", 0)
                vulnerabilities.append(_pick(
                    PASSING_VULNERABILITY_TEMPLATES,
                    seed=seed_base + flag_index,
                    your_name=p["name"],
                    your_pos=p.get("specific_position", "MID"),
                    your_val=passing_val,
                    opp_descriptor="high",
                ))
                flag_index += 1

        # ── General team-level pace flags ──
        general_pace = opp_attrs.get("pace")
        if general_pace == "high":
            slow_defenders = [
                p for p in starting_xi
                if p.get("broad_position") == "DEF"
                and (p.get("attributes", {}).get("pace") or 20) <= PACE_LOW_THRESHOLD
            ]
            for p in slow_defenders[:2]:
                pace_val = p.get("attributes", {}).get("pace", 0)
                vulnerabilities.append(_pick(
                    VULNERABILITY_TEMPLATES,
                    seed=seed_base + flag_index,
                    your_name=p["name"],
                    your_pos=p.get("specific_position", "DEF"),
                    your_val=pace_val,
                    opp_pos="attackers",
                    opp_descriptor="fast",
                ))
                flag_index += 1

        elif general_pace == "low":
            fast_attackers = [
                p for p in starting_xi
                if p.get("broad_position") == "FWD"
                and (p.get("attributes", {}).get("pace") or 0) >= PACE_HIGH_THRESHOLD
            ]
            for p in fast_attackers[:2]:
                pace_val = p.get("attributes", {}).get("pace", 0)
                exploits.append(_pick(
                    EXPLOIT_TEMPLATES,
                    seed=seed_base + flag_index,
                    your_name=p["name"],
                    your_pos=p.get("specific_position", "FWD"),
                    your_val=pace_val,
                    opp_pos="defence",
                    opp_descriptor="slow",
                ))
                flag_index += 1

        # ── Aerial threat cross-reference: your ST vs their weak aerial defence ──
        opp_aerial = opp_attrs.get("aerial") or opp_attrs.get("aerial_strength") or ""
        if isinstance(opp_aerial, str) and any(
            w in opp_aerial.lower() for w in ("weak", "poor", "struggles")
        ):
            strong_aerial_sts = [
                p for p in starting_xi
                if p.get("broad_position") == "FWD"
                and (p.get("attributes", {}).get("heading") or 0) >= HEADING_HIGH
            ]
            for p in strong_aerial_sts[:1]:
                heading_val = p.get("attributes", {}).get("heading", 0)
                exploits.append(_pick(
                    ST_AERIAL_EXPLOIT_TEMPLATES,
                    seed=seed_base + flag_index,
                    your_name=p["name"],
                    your_pos=p.get("specific_position", "FWD"),
                    your_val=heading_val,
                ))
                flag_index += 1

        # ── CB heading vs strong aerial opposition ──
        opp_aerial_threat = opp_attrs.get("aerial") or ""
        if isinstance(opp_aerial_threat, str) and any(
            s in opp_aerial_threat.lower() for s in ("strong", "threat", "dominant")
        ):
            cb_headings = [
                p.get("attributes", {}).get("heading", 0)
                for p in starting_xi
                if p.get("specific_position") == "CB"
                and p.get("attributes", {}).get("heading") is not None
            ]
            if cb_headings and (sum(cb_headings) / len(cb_headings)) < 13:
                general_notes.append(
                    "Opposition have a strong aerial presence — average CB heading rating is low. "
                    "Prioritise defensive organisation at set pieces."
                )

        # ── Press style note ──
        if press_style:
            general_notes.append(_pick(
                GENERAL_PRESS_NOTE,
                seed=seed_base + flag_index,
                press=press_style,
                opp=opp_name,
            ))
            flag_index += 1

        # ── Set piece threat note ──
        if set_piece and set_piece in ("high", "medium"):
            general_notes.append(_pick(
                GENERAL_SET_PIECE_NOTE,
                seed=seed_base + flag_index,
                threat=set_piece.capitalize(),
                opp=opp_name,
            ))

        data["matchup_exploits"]        = exploits[:4]
        data["matchup_vulnerabilities"] = vulnerabilities[:4]
        data["matchup_general_notes"]   = general_notes

        return data