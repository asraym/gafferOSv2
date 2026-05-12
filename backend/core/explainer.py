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


class Explainer:
    """
    Builds the plain English reasoning report from all engine layers.
    Trait and attribute aware — mentions specific players where relevant.
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

        # Formation rationale — mention traits that drove the decision
        formation = d.get("recommended_formation", "4-3-3")
        scores    = d.get("formation_scores", {})
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
    # Formation reason — trait-driven explanation
    # ------------------------------------------------------------------

    def _formation_reason(self, d: dict) -> str:
        """
        Looks at starting XI traits and attributes to explain why the
        formation was chosen in plain English.
        """
        formation  = d.get("recommended_formation", "4-3-3")
        xi         = d.get("starting_xi", [])
        if not xi:
            return ""

        notes = []

        # Look for specific traits in the XI that justify the formation
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
                    break  # one mention per player

        if mentioned:
            notes.append("Shaped by " + ", ".join(mentioned[:2]))  # cap at 2 to keep it concise

        # Attribute-driven reason
        if formation == "4-3-3":
            fast_fwds = [
                p for p in xi
                if p["broad_position"] == "FWD"
                and p.get("attributes", {}).get("pace") is not None
                and p["attributes"]["pace"] >= 15
            ]
            if fast_fwds:
                names = " and ".join(p["name"] for p in fast_fwds[:2])
                notes.append(f"pace of {names} suits wide forward roles")

        elif formation == "4-4-2":
            sts = [p for p in xi if p["broad_position"] == "FWD"]
            if len(sts) >= 2:
                heading_vals = [
                    p["attributes"]["heading"]
                    for p in sts
                    if p.get("attributes", {}).get("heading") is not None
                ]
                if heading_vals and max(heading_vals) >= 15:
                    notes.append("two-striker partnership provides physical presence")

        if not notes:
            return ""

        return ". ".join(notes) + "."

    # ------------------------------------------------------------------
    # Attribute callouts — highlight standout players
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

            # Heading dominance for CBs and STs
            heading = attrs.get("heading")
            if heading and heading >= 17 and pos in ["CB", "ST", "CF"]:
                notes.append(f"{name} heading {heading:.1f} — aerial dominance from set pieces")

            # Pace for wide players and forwards
            pace = attrs.get("pace")
            if pace and pace >= 17 and pos in ["RW", "LW", "RB", "LB", "ST", "CF"]:
                notes.append(f"{name} pace {pace:.1f} — exploit space in behind")

            # Passing for playmakers
            passing = attrs.get("passing")
            if passing and passing >= 17 and pos in ["CM", "CAM", "CDM"]:
                notes.append(f"{name} passing {passing:.1f} — creative outlet in midfield")

            # Finishing for strikers
            finishing = attrs.get("finishing")
            if finishing and finishing >= 17 and pos in ["ST", "CF", "SS"]:
                notes.append(f"{name} finishing {finishing:.1f} — clinical in front of goal")

        return notes[:3]  # cap at 3 to keep report readable

    # ------------------------------------------------------------------
    # Stamina warnings for high press
    # ------------------------------------------------------------------

    def _stamina_warnings(self, d: dict) -> list:
        xi    = d.get("starting_xi", [])
        flags = []

        for p in xi:
            stamina = p.get("attributes", {}).get("stamina")
            if stamina is not None and stamina < 10:
                pos = p.get("specific_position", p.get("broad_position", ""))
                flags.append(
                    f"{p['name']} ({pos}) stamina {stamina:.1f} — "
                    f"may struggle to maintain press intensity for 90 mins"
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

        # Group starters and bench by broad position
        xi_by_pos    = {}
        bench_by_pos = {}

        for p in xi:
            broad = p["broad_position"]
            overall = p.get("attributes", {}).get("overall_rating")
            if overall is not None:
                if broad not in xi_by_pos or overall > xi_by_pos[broad]["overall"]:
                    xi_by_pos[broad] = {"name": p["name"], "overall": overall}

        for p in bench:
            broad = p["broad_position"]
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
                        f"{benched['name']} ({broad}, {benched['overall']:.1f}) "
                        f"rated higher than {starter['name']} ({starter['overall']:.1f}) — "
                        f"consider starting"
                    )

        return flags