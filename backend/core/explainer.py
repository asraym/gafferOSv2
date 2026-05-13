import random

# ---------------------------------------------------------------------------
# Data mode headers — fixed, no variation (these are warnings not narrative)
# ---------------------------------------------------------------------------

DATA_MODE_HEADERS = {
    "full":    None,
    "basic":   (
        "⚠️  Basic analysis — match team stats not yet available. "
        "Submit possession, pressure, and line height data via the CV pipeline "
        "for a more accurate report."
    ),
    "default": (
        "ℹ️  No match data available yet. Showing historically optimal tactics "
        "based on training data. Analysis will improve once matches are logged."
    ),
}


# ---------------------------------------------------------------------------
# Variation pools
# ---------------------------------------------------------------------------

FORMATION_TRAIT_INTROS = [
    "Shaped by {detail}.",
    "{detail} makes this the natural shape.",
    "The {formation} suits the squad — {detail}.",
    "Going with {formation} — {detail}.",
    "Built around {detail}.",
    "{detail} points clearly to the {formation}.",
]

FORMATION_PACE_NOTES = [
    "pace of {names} suits wide forward roles",
    "{names} have the legs to hurt teams in behind on the flanks",
    "width and pace of {names} makes the three-forward shape the right call",
    "{names} give genuine threat in behind — the {formation} unlocks that",
]

FORMATION_PHYSICAL_NOTES = [
    "two-striker partnership provides physical presence",
    "double striker axis gives a direct aerial option up top",
    "front two offer physicality and hold-up — suits the 4-4-2 structure",
    "the partnership up front can cause problems aerially and in behind",
]

HEADING_NOTES = [
    "{name} heading {val:.1f} — aerial dominance from set pieces",
    "{name} wins headers at both ends — heading {val:.1f}",
    "Set piece threat through {name} — heading {val:.1f}",
    "{name} is a genuine aerial threat — heading rated {val:.1f}",
    "Aerial platform: {name} heading {val:.1f}",
]

PACE_NOTES = [
    "{name} pace {val:.1f} — exploit space in behind",
    "{name} has genuine pace to burn — {val:.1f}",
    "Threat in behind through {name} — pace {val:.1f}",
    "{name} pace {val:.1f} — can stretch any defensive line",
    "Pace of {name} ({val:.1f}) is a weapon on the counter",
]

PASSING_NOTES = [
    "{name} passing {val:.1f} — creative outlet in midfield",
    "{name} can pick passes others can't — passing {val:.1f}",
    "Midfield creativity through {name} — passing {val:.1f}",
    "{name} passing {val:.1f} — the engine room of the build-up",
    "Distribution hub: {name} passing {val:.1f}",
]

FINISHING_NOTES = [
    "{name} finishing {val:.1f} — clinical in front of goal",
    "{name} is a genuine goal threat — finishing {val:.1f}",
    "Clinical edge up front: {name} finishing {val:.1f}",
    "{name} finishing {val:.1f} — punishes half chances",
    "Goals will come through {name} — finishing rated {val:.1f}",
]

STAMINA_WARNING_NOTES = [
    "{name} ({pos}) stamina {val:.1f} — may struggle to maintain press intensity for 90 mins",
    "{name} ({pos}) has low stamina ({val:.1f}) — high press could leave them exposed late on",
    "Watch {name} ({pos}) closely — stamina {val:.1f} is a concern at high press intensity",
    "{name} ({pos}) stamina {val:.1f} — consider subbing before the press drops",
    "Fitness flag: {name} ({pos}) stamina {val:.1f} in a high press system",
]

BENCH_UPGRADE_NOTES = [
    "{benched} ({broad}, {b_rating:.1f}) rated higher than {starter} ({s_rating:.1f}) — consider starting",
    "{benched} ({b_rating:.1f}) is sitting on the bench ahead of {starter} ({s_rating:.1f}) at {broad} — worth reconsidering",
    "Upgrade available at {broad}: {benched} ({b_rating:.1f}) vs {starter} ({s_rating:.1f}) starting",
    "{benched} outrates {starter} at {broad} ({b_rating:.1f} vs {s_rating:.1f}) — selection worth revisiting",
    "Bench has a stronger option at {broad}: {benched} {b_rating:.1f} over {starter} {s_rating:.1f}",
]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _pick(pool: list, **kwargs) -> str:
    return random.choice(pool).format(**kwargs)


# ---------------------------------------------------------------------------
# Explainer
# ---------------------------------------------------------------------------

class Explainer:
    """
    Builds the plain English reasoning report from all engine layers.
    Trait and attribute aware — mentions specific players where relevant.
    Picks up matchup layer flags (exploits, vulnerabilities, general notes).
    Language varies per run via random template selection.
    """

    def explain(self, data: dict) -> dict:
        data["reasoning"] = self._build_report(data)
        return data

    def _build_report(self, d: dict) -> str:
        lines = []

        # Data quality header
        mode    = d.get("data_mode", "default")
        warning = DATA_MODE_HEADERS.get(mode)
        if warning:
            lines.append(warning)
            lines.append("")

        opp = d.get("opponent_name", "the opponent")
        tm  = d.get("team_metrics", {})
        om  = d.get("opp_metrics", {})

        # Outcome probabilities
        win_p  = d.get("win_probability",  0.375)
        draw_p = d.get("draw_probability", 0.250)
        loss_p = d.get("loss_probability", 0.375)
        lines.append(
            f"Match outlook vs {opp}: "
            f"Win {win_p:.0%}  ·  Draw {draw_p:.0%}  ·  Loss {loss_p:.0%}."
        )

        # Formation rationale
        formation        = d.get("recommended_formation", "4-3-3")
        scores           = d.get("formation_scores", {})
        formation_reason = self._formation_reason(d)

        if scores and mode != "default":
            ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            top3   = ", ".join(f"{f} ({v:.0%})" for f, v in ranked[:3])
            lines.append(
                f"Recommended formation: {formation}. "
                f"Model tested all candidates — top 3 win probabilities: {top3}. "
                f"{formation_reason}"
            )
        else:
            lines.append(f"Recommended formation: {formation}. {formation_reason}")

        # Tactical decisions
        lines.append(
            f"Tactical approach: {d.get('tactical_focus', 'Balanced Mid-Block')}. "
            f"Defensive line: {d.get('defensive_line', 'Medium')}. "
            f"Press intensity: {d.get('press_intensity', 'Medium')}."
        )

        # Key player attribute callouts
        attr_notes = self._attribute_callouts(d)
        if attr_notes:
            lines.append("Key personnel: " + " | ".join(attr_notes))

        # Metric context
        if mode != "default" and tm:
            lines.append(
                f"Your team: offensive output {tm.get('offensive_output_index', 0):.2f}, "
                f"defensive solidity {tm.get('defensive_solidity_index', 0):.2f}, "
                f"passing stability {tm.get('passing_stability_index', 0):.2f}, "
                f"possession share {tm.get('possession_share', 0):.0%}."
            )
            if om:
                lines.append(
                    f"Opposition estimate: offensive output {om.get('offensive_output_index', 0):.2f}, "
                    f"defensive solidity {om.get('defensive_solidity_index', 0):.2f}."
                )

        # Opposition scouting
        opp_profile = d.get("opposition")
        if opp_profile:
            opp_form  = opp_profile.get("formation", "Unknown")
            opp_style = opp_profile.get("playing_style", "")
            opp_press = opp_profile.get("press_style", "")
            notes = []
            if opp_form and opp_form != "Unknown":
                notes.append(f"plays {opp_form}")
            if opp_style:
                notes.append(opp_style.lower())
            if opp_press:
                notes.append(f"press style: {opp_press.lower()}")
            if notes:
                lines.append(f"Scouting: {opp} " + ", ".join(notes) + ".")

        # --- Matchup layer output ---
        exploits       = d.get("matchup_exploits", [])
        vulnerabilities = d.get("matchup_vulnerabilities", [])
        general_notes  = d.get("matchup_general_notes", [])

        if exploits:
            lines.append("Exploit: " + " | ".join(exploits))

        if vulnerabilities:
            lines.append("Watch out: " + " | ".join(vulnerabilities))

        if general_notes:
            for note in general_notes:
                lines.append(note)

        # Fatigue
        fatigue = d.get("team_fatigue_score", d.get("fatigue_score", 0.30))
        press   = d.get("press_intensity", "Medium")
        if fatigue > 0.60:
            lines.append(
                f"Fatigue risk is elevated ({fatigue:.0%}) — "
                f"press intensity kept at {press} to protect the squad."
            )

        # Stamina warnings for high press
        if press == "High":
            stamina_flags = self._stamina_warnings(d)
            if stamina_flags:
                lines.append("Stamina concern for high press: " + " | ".join(stamina_flags))

        # Bench upgrade flags
        bench_flags = self._bench_upgrade_flags(d)
        if bench_flags:
            lines.append("Bench upgrade available: " + " | ".join(bench_flags))

        # Rotation suggestions
        suggestions = d.get("rotation_suggestions", [])
        if suggestions and suggestions[0] != "Squad form looks solid — no urgent rotation needed.":
            lines.append("Rotation flags: " + " | ".join(suggestions))

        # Missing data nudge
        missing = d.get("missing_fields", [])
        if missing:
            lines.append("To improve accuracy, submit: " + "; ".join(missing) + ".")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Formation reason
    # ------------------------------------------------------------------

    def _formation_reason(self, d: dict) -> str:
        formation = d.get("recommended_formation", "4-3-3")
        xi        = d.get("starting_xi", [])
        if not xi:
            return ""

        notes = []

        trait_mentions = {
            "Ball Playing Defender":  "builds from the back",
            "Progressive Passer":     "progresses play from deep",
            "Target Man":             "aerial threat up front",
            "Deep Playmaker":         "controls tempo from midfield",
            "False Nine":             "fluid attacking movement",
            "Offensive Full-Back":    "width and attacking threat from full-back",
            "High Press Leader":      "leads the press from the front",
        }

        mentioned = []
        for p in xi:
            traits = p.get("traits", [])
            for trait, description in trait_mentions.items():
                if trait in traits and description not in mentioned:
                    mentioned.append(f"{p['name']}'s {trait} trait ({description})")
                    break

        if mentioned:
            detail = ", ".join(mentioned[:2])
            notes.append(
                _pick(FORMATION_TRAIT_INTROS, detail=detail, formation=formation)
            )

        if formation == "4-3-3":
            fast_fwds = [
                p for p in xi
                if p["broad_position"] == "FWD"
                and p.get("attributes", {}).get("pace") is not None
                and p["attributes"]["pace"] >= 15
            ]
            if fast_fwds:
                names = " and ".join(p["name"] for p in fast_fwds[:2])
                notes.append(
                    _pick(FORMATION_PACE_NOTES, names=names, formation=formation)
                )

        elif formation == "4-4-2":
            sts = [p for p in xi if p["broad_position"] == "FWD"]
            if len(sts) >= 2:
                heading_vals = [
                    p["attributes"]["heading"]
                    for p in sts
                    if p.get("attributes", {}).get("heading") is not None
                ]
                if heading_vals and max(heading_vals) >= 15:
                    notes.append(_pick(FORMATION_PHYSICAL_NOTES))

        if not notes:
            return ""

        return " ".join(notes)

    # ------------------------------------------------------------------
    # Attribute callouts
    # ------------------------------------------------------------------

    def _attribute_callouts(self, d: dict) -> list:
        xi    = d.get("starting_xi", [])
        notes = []

        for p in xi:
            attrs = p.get("attributes", {})
            name  = p["name"]
            pos   = p.get("specific_position", p.get("broad_position", ""))

            if not attrs:
                continue

            heading = attrs.get("heading")
            if heading and heading >= 17 and pos in ["CB", "ST", "CF"]:
                notes.append(_pick(HEADING_NOTES, name=name, val=heading))

            pace = attrs.get("pace")
            if pace and pace >= 17 and pos in ["RW", "LW", "RB", "LB", "ST", "CF"]:
                notes.append(_pick(PACE_NOTES, name=name, val=pace))

            passing = attrs.get("passing")
            if passing and passing >= 17 and pos in ["CM", "CAM", "CDM"]:
                notes.append(_pick(PASSING_NOTES, name=name, val=passing))

            finishing = attrs.get("finishing")
            if finishing and finishing >= 17 and pos in ["ST", "CF", "SS"]:
                notes.append(_pick(FINISHING_NOTES, name=name, val=finishing))

        return notes[:3]

    # ------------------------------------------------------------------
    # Stamina warnings
    # ------------------------------------------------------------------

    def _stamina_warnings(self, d: dict) -> list:
        xi    = d.get("starting_xi", [])
        flags = []

        for p in xi:
            stamina = p.get("attributes", {}).get("stamina")
            if stamina is not None and stamina < 10:
                pos = p.get("specific_position", p.get("broad_position", ""))
                flags.append(
                    _pick(STAMINA_WARNING_NOTES, name=p["name"], pos=pos, val=stamina)
                )

        return flags

    # ------------------------------------------------------------------
    # Bench upgrade flags
    # ------------------------------------------------------------------

    def _bench_upgrade_flags(self, d: dict) -> list:
        xi    = d.get("starting_xi", [])
        bench = d.get("bench", [])
        flags = []

        if not xi or not bench:
            return flags

        xi_by_pos    = {}
        bench_by_pos = {}

        for p in xi:
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
                diff    = benched["overall"] - starter["overall"]
                if diff >= 1.5:
                    flags.append(
                        _pick(
                            BENCH_UPGRADE_NOTES,
                            benched=benched["name"],
                            starter=starter["name"],
                            broad=broad,
                            b_rating=benched["overall"],
                            s_rating=starter["overall"],
                        )
                    )

        return flags