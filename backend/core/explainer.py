import random

DATA_MODE_HEADERS = {
    "full":    None,
    "basic":   (
        "⚠️  Basic analysis — match team stats not yet available. "
        "Submit possession, pressure, and line height data via the CV pipeline "
        "for a more accurate report."
    ),
    "default": (
        "ℹ️  No match data available yet. Showing base rate probabilities only. "
        "Submit match snapshots and scouting notes before requesting tactical analysis."
    ),
}

# Defensive line reasoning
DEFENSIVE_LINE_REASONING = {
    "High":   "pushing the line high to compress space and catch attackers offside — requires pace from CBs",
    "Medium": "balanced shape — standard cover, adaptable in and out of possession",
    "Deep":   "sitting deep to absorb pressure — organised defensive block is the priority",
}

# Press intensity reasoning
PRESS_INTENSITY_REASONING = {
    "High":   {
        "form":    "form and fitness support an aggressive press — press triggers should be set pieces and back passes",
        "default": "squad condition allows high intensity — press early and force errors",
    },
    "Medium": "balanced approach given squad fitness and opponent quality — press selectively",
    "Low":    {
        "fatigue": "fatigue risk is elevated — conserve energy, stay compact, press only when safe",
        "opp":     "opponent quality is high — avoid pressing into their strengths, stay organised",
        "default": "low press recommended — stay compact and hit on the counter",
    },
}

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

TRAJECTORY_RISING_NOTES = [
    "{name} ({pos}) is in excellent recent form — trending upward over last 3 matches",
    "{name} ({pos}) form is rising — confident selection",
    "{name} ({pos}) has been getting better each match — key player right now",
]

TRAJECTORY_FALLING_NOTES = [
    "{name} ({pos}) form has dropped over the last 3 matches — monitor closely",
    "{name} ({pos}) trending downward in recent games — bench option worth considering",
    "Form concern: {name} ({pos}) has been declining — watch the first 30 mins",
]


def _pick(pool: list, **kwargs) -> str:
    return random.choice(pool).format(**kwargs)


class Explainer:
    """
    Builds the plain English reasoning report from all engine layers.
    """

    def explain(self, data: dict) -> dict:
        try:
            data["reasoning"] = self._build_report(data)
        except Exception as e:
            data["reasoning"] = f"Explainer error: {str(e)}"
        return data

    def _build_report(self, d: dict) -> str:
        lines = []

        mode    = d.get("data_mode", "default")
        warning = DATA_MODE_HEADERS.get(mode)
        if warning:
            lines.append(warning)
            lines.append("")

        opp    = d.get("opponent_name", "the opponent")
        tm     = d.get("team_metrics", {})
        om     = d.get("opp_metrics", {})
        press  = d.get("press_intensity", "Medium")
        line   = d.get("defensive_line", "Medium")
        fatigue = d.get("team_fatigue_score", d.get("fatigue_score", 0.30))

        # Outcome probabilities
        win_p  = d.get("win_probability",  0.375)
        draw_p = d.get("draw_probability", 0.250)
        loss_p = d.get("loss_probability", 0.375)
        lines.append(
            f"Match outlook vs {opp}: "
            f"Win {win_p:.0%}  ·  Draw {draw_p:.0%}  ·  Loss {loss_p:.0%}."
        )

        # Formation — handle None for default mode (#9)
        formation = d.get("recommended_formation")
        if formation is None:
            lines.append(
                "Formation: insufficient data to recommend a shape. "
                "Submit match snapshots and scouting notes to unlock tactical recommendations."
            )
        else:
            formation_reason = self._formation_reason(d)
            lines.append(
                f"Recommended formation: {formation}."
                + (f" {formation_reason}" if formation_reason else "")
            )
            formation_note = d.get("formation_selection_note", "")
            if formation_note:
                lines.append(f"Formation adjusted: {formation_note}")

            # Defensive line reasoning
            line_reason = DEFENSIVE_LINE_REASONING.get(line, "")
            if line_reason:
                lines.append(f"Defensive line: {line} — {line_reason}.")

            # Press intensity reasoning
            press_reason = self._press_reason(press, fatigue, om)
            lines.append(f"Press intensity: {press} — {press_reason}.")

            # Tactical focus
            lines.append(f"Tactical focus: {d.get('tactical_focus', 'Balanced Mid-Block')}.")

        # Key player attribute callouts
        attr_notes = self._attribute_callouts(d)
        if attr_notes:
            lines.append("Key personnel: " + " | ".join(attr_notes))

        # Form trajectory callouts
        trajectory_notes = self._trajectory_notes(d)
        if trajectory_notes:
            lines.append("Form: " + " | ".join(trajectory_notes))

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
            opp_form  = opp_profile.get("likely_formation") or opp_profile.get("formation", "Unknown")
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

        # Matchup layer
        exploits        = d.get("matchup_exploits", [])
        vulnerabilities = d.get("matchup_vulnerabilities", [])
        general_notes   = d.get("matchup_general_notes", [])

        if exploits:
            lines.append("Exploit: " + " | ".join(exploits))
        if vulnerabilities:
            lines.append("Watch out: " + " | ".join(vulnerabilities))
        for note in general_notes:
            lines.append(note)

        # Fatigue
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

        # Replace the missing data nudge block at the bottom of _build_report

        # Constraint violations — separate from missing data
        violations = d.get("constraint_violations", [])
        if violations:
            lines.append(
                "Tactical conflicts: " +
                " | ".join(v["reason"] for v in violations)
            )

        # Missing data nudge — filter out constraint violations
        missing = [
            m for m in d.get("missing_fields", [])
            if not m.startswith("Tactical conflict:")
        ]
        if missing:
            lines.append("To improve accuracy, submit: " + "; ".join(missing) + ".")
        
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Press intensity reasoning
    # ------------------------------------------------------------------

    def _press_reason(self, press: str, fatigue: float, opp_metrics: dict) -> str:
        opp_dsi = opp_metrics.get("defensive_solidity_index", 0.55)
        opp_osi = opp_metrics.get("offensive_output_index", 0.38)

        if press == "High":
            if fatigue < 0.35:
                return PRESS_INTENSITY_REASONING["High"]["form"]
            return PRESS_INTENSITY_REASONING["High"]["default"]

        if press == "Low":
            if fatigue > 0.60:
                return PRESS_INTENSITY_REASONING["Low"]["fatigue"]
            if opp_osi > 0.55:
                return PRESS_INTENSITY_REASONING["Low"]["opp"]
            return PRESS_INTENSITY_REASONING["Low"]["default"]

        return PRESS_INTENSITY_REASONING["Medium"]

    # ------------------------------------------------------------------
    # Formation reason
    # ------------------------------------------------------------------

    def _formation_reason(self, d: dict) -> str:
        formation = d.get("recommended_formation")
        if not formation:
            return ""

        xi    = d.get("starting_xi", [])
        notes = []

        trait_mentions = {
            "Ball Playing Defender": "builds from the back",
            "Progressive Passer":    "progresses play from deep",
            "Target Man":            "aerial threat up front",
            "Deep Playmaker":        "controls tempo from midfield",
            "False Nine":            "fluid attacking movement",
            "Offensive Full-Back":   "width and attacking threat from full-back",
            "High Press Leader":     "leads the press from the front",
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
            notes.append(_pick(FORMATION_TRAIT_INTROS, detail=detail, formation=formation))

        if formation == "4-3-3":
            fast_fwds = [
                p for p in xi
                if p["broad_position"] == "FWD"
                and p.get("attributes", {}).get("pace", 0) >= 15
            ]
            if fast_fwds:
                names = " and ".join(p["name"] for p in fast_fwds[:2])
                notes.append(_pick(FORMATION_PACE_NOTES, names=names, formation=formation))

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
            if heading and heading >= 17 and pos in ("CB", "ST", "CF"):
                notes.append(_pick(HEADING_NOTES, name=name, val=heading))

            pace = attrs.get("pace")
            if pace and pace >= 17 and pos in ("RW", "LW", "RB", "LB", "ST", "CF"):
                notes.append(_pick(PACE_NOTES, name=name, val=pace))

            passing = attrs.get("passing")
            if passing and passing >= 17 and pos in ("CM", "CAM", "CDM"):
                notes.append(_pick(PASSING_NOTES, name=name, val=passing))

            finishing = attrs.get("finishing")
            if finishing and finishing >= 17 and pos in ("ST", "CF", "SS"):
                notes.append(_pick(FINISHING_NOTES, name=name, val=finishing))

        return notes[:3]

    # ------------------------------------------------------------------
    # Form trajectory
    # ------------------------------------------------------------------

    def _trajectory_notes(self, d: dict) -> list:
        xi        = d.get("starting_xi", [])
        snapshots = d.get("snapshots", [])
        notes     = []

        if not snapshots:
            return notes

        # Build trajectory per player from snapshots
        from collections import defaultdict
        by_player = defaultdict(list)
        for s in snapshots:
            by_player[s["player_id"]].append(s)

        for p in xi:
            pid   = p["player_id"]
            snaps = sorted(by_player.get(pid, []), key=lambda s: s.get("match_id", 0))
            if len(snaps) < 3:
                continue

            def snap_score(s):
                return (
                    s.get("goals", 0) * 0.25 +
                    s.get("assists", 0) * 0.20 +
                    s.get("key_passes", 0) * 0.10 +
                    (s.get("tackles", 0) + s.get("interceptions", 0)) * 0.10
                )

            recent  = snap_score(snaps[-1])
            earlier = snap_score(snaps[-3])
            trend   = (recent - earlier) / max(earlier, 0.1)
            pos     = p.get("specific_position", p.get("broad_position", ""))

            if trend > 0.20:
                notes.append(_pick(TRAJECTORY_RISING_NOTES, name=p["name"], pos=pos))
            elif trend < -0.20 and p.get("form_score", 1.0) < 0.50:
                notes.append(_pick(TRAJECTORY_FALLING_NOTES, name=p["name"], pos=pos))

        return notes[:3]  # cap — don't flood the report

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
                flags.append(_pick(STAMINA_WARNING_NOTES, name=p["name"], pos=pos, val=stamina))

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
                if benched["overall"] - starter["overall"] >= 1.5:
                    flags.append(_pick(
                        BENCH_UPGRADE_NOTES,
                        benched=benched["name"],
                        starter=starter["name"],
                        broad=broad,
                        b_rating=benched["overall"],
                        s_rating=starter["overall"],
                    ))

        return flags