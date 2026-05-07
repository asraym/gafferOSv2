DATA_MODE_HEADERS = {
    "full":    None,   # No warning — full data
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
    Leads with a data quality warning when relevant.
    """

    def explain(self, data: dict) -> dict:
        reasoning = self._build_report(data)
        data["reasoning"] = reasoning
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
        tm  = d["team_metrics"]
        om  = d["opp_metrics"]

        # Outcome probabilities
        win_p  = d.get("win_probability",  0.375)
        draw_p = d.get("draw_probability", 0.250)
        loss_p = d.get("loss_probability", 0.375)
        lines.append(
            f"Match outlook vs {opp}: "
            f"Win {win_p:.0%}  ·  Draw {draw_p:.0%}  ·  Loss {loss_p:.0%}."
        )

        # Formation rationale
        formation = d.get("recommended_formation", "4-3-3")
        scores    = d.get("formation_scores", {})
        if scores and mode != "default":
            ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            top3   = ", ".join(f"{f} ({v:.0%})" for f, v in ranked[:3])
            lines.append(
                f"Recommended formation: {formation}. "
                f"Model tested all candidates — top 3 win probabilities: {top3}."
            )
        else:
            lines.append(f"Recommended formation: {formation}.")

        # Tactical decisions
        lines.append(
            f"Tactical approach: {d.get('tactical_focus', 'Balanced Mid-Block')}. "
            f"Defensive line: {d.get('defensive_line', 'Medium')}. "
            f"Press intensity: {d.get('press_intensity', 'Medium')}."
        )

        # Metric context
        if mode != "default":
            lines.append(
                f"Your team: offensive output {tm['offensive_output_index']:.2f}, "
                f"defensive solidity {tm['defensive_solidity_index']:.2f}, "
                f"passing stability {tm['passing_stability_index']:.2f}, "
                f"possession share {tm['possession_share']:.0%}."
            )
            lines.append(
                f"Opposition estimate: offensive output {om['offensive_output_index']:.2f}, "
                f"defensive solidity {om['defensive_solidity_index']:.2f}."
            )

        # Opposition scouting
        opp_profile = d.get("opposition")
        if opp_profile:
            opp_form = opp_profile.get("formation", "Unknown")
            opp_style = opp_profile.get("playing_style", "")
            opp_press = opp_profile.get("press_style", "")
            scouting_notes = []
            if opp_form and opp_form != "Unknown":
                scouting_notes.append(f"plays {opp_form}")
            if opp_style:
                scouting_notes.append(opp_style.lower())
            if opp_press:
                scouting_notes.append(f"press style: {opp_press.lower()}")
            if scouting_notes:
                lines.append(f"Scouting: {opp} " + ", ".join(scouting_notes) + ".")

        # Fatigue
        fatigue = d.get("team_fatigue_score", d.get("fatigue_score", 0.30))
        if fatigue > 0.60:
            lines.append(
                f"Fatigue risk is elevated ({fatigue:.0%}) — "
                f"press intensity kept at {d.get('press_intensity')} to protect the squad."
            )

        # Rotation
        suggestions = d.get("rotation_suggestions", [])
        if suggestions and suggestions[0] != "Squad form looks solid — no urgent rotation needed.":
            lines.append("Rotation flags: " + " | ".join(suggestions))

        # Missing data nudge
        missing = d.get("missing_fields", [])
        if missing:
            lines.append(
                "To improve accuracy, submit: " + "; ".join(missing) + "."
            )

        return "\n".join(lines)