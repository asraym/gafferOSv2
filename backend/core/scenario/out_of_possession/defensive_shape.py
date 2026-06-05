# core/scenario/out_of_possession/defensive_shape.py
#
# Simulates the team's defensive organisation.
#
# Depends on:
#   defensive_shape.block        — high/mid/low/deep → how far up team holds line
#   defensive_shape.compactness  — compact/balanced/open → horizontal spacing
#   defensive_shape.press_trigger — on back pass / on goalkeeper / second ball / never
#   defensive_shape.transition   — counter immediately / hold shape / build slowly
#   defensive_formation          — base slot positions when defending
#   xi traits                    — Organises Defence, Stays Back, Sweeper CB,
#                                   Aggressive Tackler, Tracks Runners, Tight Marker

from core.scenario.types import SimFrame, BallState, PlayerDelta, OppDelta
from core.scenario.helpers import (
    get_slots, mirror_slots, has_trait, find_player,
    player_slot_index, mirror_dy, clamp_x, clamp_y,
    PH, PW,
)


# Block height → x-position of the defensive line
BLOCK_LINE: dict[str, float] = {
    "high":  135.0,
    "mid":   105.0,
    "low":    75.0,
    "deep":   55.0,
}

# Compactness → horizontal spread multiplier (1.0 = normal, 0.7 = narrow)
COMPACTNESS_SPREAD: dict[str, float] = {
    "compact":  0.70,
    "balanced": 1.00,
    "open":     1.25,
}

def metadata(defensive_shape: dict, opposition: dict) -> dict:
    from core.scenario.types import ScenarioMeta
    ds      = defensive_shape or {}
    block   = ds.get("block") or "mid"
    trigger = ds.get("press_trigger") or "second ball"
    label   = ds.get("shape_label") or "Defensive block"
    opp_style = opposition.get("playing_style") or "direct"
 
    block_desc = {
        "high":  "high defensive line — compressing space and catching attackers offside",
        "mid":   "mid-block — balanced shape between penalty areas",
        "low":   "deep block — absorbing pressure and hitting on the counter",
        "deep":  "deep defensive block — organised low shape, hard to break down",
    }.get(block, "mid-block")
 
    return ScenarioMeta(
        scenario="defensive_shape",
        title=label,
        phase="Out of possession",
        purpose=f"Maintain a {block_desc} against {opp_style} opposition",
        takeaway=f"Trigger: {trigger}. Hold the shape until the trigger fires — don't dive in early.",
    ).to_dict()

def build(
    xi: list[dict],
    formation: str,
    defensive_formation: str,
    defensive_shape: dict,
    opposition: dict,
) -> list[dict]:
    ds = defensive_shape or {}
    block        = ds.get("block") or "mid"
    compactness  = ds.get("compactness") or "balanced"
    press_trigger = ds.get("press_trigger") or "second ball"
    transition   = ds.get("transition") or "hold shape"

    def_formation = defensive_formation or formation
    slots     = get_slots(def_formation)
    opp_form  = opposition.get("likely_formation") or "4-3-3"
    opp_slots = mirror_slots(get_slots(opp_form))
    opp_press = opposition.get("press_style") or "medium"

    line_x    = BLOCK_LINE.get(block, 105.0)
    spread    = COMPACTNESS_SPREAD.get(compactness, 1.0)
    centre_y  = PH / 2

    frames: list[SimFrame] = []

    # ── Frame 1: Team sets defensive shape ────────────────────────────────────
    frame1_players = []

    for i, p in enumerate(xi):
        if i >= len(slots):
            continue
        slot = slots[i]
        role = slot["role"]
        pname = p.get("name", f"P{i}")
        dy_from_centre = (slot["y"] - centre_y) * spread

        if role == "GK":
            # GK position based on block
            gk_x = {"high": 35.0, "mid": 25.0, "low": 16.0, "deep": 14.0}.get(block, 22.0)
            frame1_players.append(PlayerDelta(
                name=pname, dx=gk_x - slot["x"], dy=0,
                trait_label="Sets position" if has_trait(p, "Command Of Area") else None,
            ))

        elif role == "DEF":
            # CBs and FBs hold the line
            target_x = line_x - 30  # DEF line is behind the block line
            if has_trait(p, "Sweeper CB"):
                target_x -= 8.0    # sweeper drops slightly deeper
            if has_trait(p, "Stays Back", "Defensive Full-Back"):
                target_x -= 5.0

            frame1_players.append(PlayerDelta(
                name=pname,
                dx=clamp_x(target_x) - slot["x"],
                dy=(centre_y + dy_from_centre * 0.8) - slot["y"],
                trait_label="Organises line" if has_trait(p, "Organises Defence") else None,
            ))

        elif role == "MID":
            # Midfield screen in front of defence
            target_x = line_x - 10
            if has_trait(p, "Sits Between Lines", "Deep Playmaker"):
                target_x -= 12.0
            frame1_players.append(PlayerDelta(
                name=pname,
                dx=clamp_x(target_x) - slot["x"],
                dy=(centre_y + dy_from_centre * spread) - slot["y"],
                trait_label="Screens defence" if has_trait(p, "Deep Playmaker", "Ball Winner") else None,
            ))

        elif role == "FWD":
            # Forwards track back based on press trigger and transition
            if transition == "counter immediately":
                # Stay high — ready for the counter
                frame1_players.append(PlayerDelta(
                    name=pname, dx=0, dy=0,
                    trait_label="Stays high — counter threat",
                ))
            elif press_trigger in ["on back pass", "on goalkeeper"]:
                # Forwards press high up
                target_x = line_x + 20
                frame1_players.append(PlayerDelta(
                    name=pname,
                    dx=clamp_x(target_x) - slot["x"], dy=0,
                    trait_label="Press trigger ready" if has_trait(p, "Presses High") else None,
                ))
            else:
                # Forwards drop to midfield line
                frame1_players.append(PlayerDelta(
                    name=pname,
                    dx=clamp_x(line_x + 5) - slot["x"],
                    dy=mirror_dy(slot["y"], -5.0),
                ))

    # Opposition in possession — advanced position
    frame1_opp = []
    for i, s in enumerate(opp_slots):
        if s["role"] == "FWD":
            frame1_opp.append(OppDelta(slot_index=i, dx=-15.0, dy=0, reaction="hold"))
        elif s["role"] == "MID":
            frame1_opp.append(OppDelta(slot_index=i, dx=-8.0, dy=0, reaction="hold"))
        else:
            frame1_opp.append(OppDelta(slot_index=i, dx=0, dy=0, reaction="hold"))

    frames.append(SimFrame(
        frame=1, duration_ms=1000,
        ball=BallState(x=float(opp_slots[0]["x"] - 20), y=float(PH / 2)),
        ball_carrier=None,
        action=f"Shape set — {block} block, {compactness} shape",
        players=frame1_players, opp_players=frame1_opp,
        note=f"{'High' if block == 'high' else 'Mid' if block == 'mid' else 'Deep'} block — {press_trigger} triggers press",
    ))

    # ── Frame 2: Press trigger fires ─────────────────────────────────────────
    frame2_players = []
    frame2_opp = []

    trigger_note = {
        "on back pass":   "Trigger — back pass to GK — forwards press immediately",
        "on goalkeeper":  "Trigger — GK has ball — press in swarms",
        "second ball":    "Trigger — second ball situation — win it in midfield",
        "never":          "Holding shape — no press, absorb and counter",
    }.get(press_trigger, "Press trigger fired")

    if press_trigger != "never":
        # Nearest players to the trigger point press aggressively
        for i, p in enumerate(xi):
            if i >= len(slots):
                continue
            slot = slots[i]
            role = slot["role"]
            pname = p.get("name", f"P{i}")

            if role == "FWD":
                # Press hard
                frame2_players.append(PlayerDelta(
                    name=pname, dx=15.0, dy=mirror_dy(slot["y"], -4.0),
                    trait_label="Pressing hard" if has_trait(p, "Presses High") else "Closes down",
                ))
            elif role == "MID" and has_trait(p, "Covers Ground", "Box To Box", "Counterpressing", "Aggressive Tackler"):
                frame2_players.append(PlayerDelta(
                    name=pname, dx=10.0, dy=0,
                    trait_label="Counterpresses",
                ))
            elif role == "DEF" and has_trait(p, "Aggressive Tackler", "Steps Into Midfield"):
                frame2_players.append(PlayerDelta(
                    name=pname, dx=8.0, dy=0,
                    trait_label="Steps out to press",
                ))

        # Opposition under pressure — tries to play out
        for i, s in enumerate(opp_slots):
            if s["role"] in ["GK", "DEF"]:
                frame2_opp.append(OppDelta(slot_index=i, dx=3.0, dy=0, reaction="hold"))
    else:
        # Hold — no press — compact lines
        for i, p in enumerate(xi):
            if i >= len(slots):
                continue
            frame2_players.append(PlayerDelta(
                name=p.get("name", ""), dx=0, dy=0,
            ))

    frames.append(SimFrame(
        frame=2, duration_ms=800,
        ball=BallState(x=float(PW - 30), y=float(PH / 2)),
        ball_carrier=None,
        action=trigger_note,
        players=frame2_players, opp_players=frame2_opp,
        note=f"Shape: {ds.get('shape_label') or 'Defensive block'}",
    ))

    # ── Frame 3: Ball won / absorbed — transition decision ────────────────────
    frame3_players = []

    if transition == "counter immediately":
        # Counter — forwards burst, defenders hold
        for i, p in enumerate(xi):
            if i >= len(slots):
                continue
            role = slots[i]["role"]
            pname = p.get("name", "")
            if role == "FWD":
                frame3_players.append(PlayerDelta(
                    name=pname, dx=20.0, dy=0,
                    trait_label="Counter — burst forward",
                ))
            elif role == "DEF":
                frame3_players.append(PlayerDelta(name=pname, dx=0, dy=0))
        note = "Ball won — counter immediately"

    elif transition == "build slowly":
        for i, p in enumerate(xi):
            if i >= len(slots):
                continue
            role = slots[i]["role"]
            frame3_players.append(PlayerDelta(
                name=p.get("name", ""), dx=4.0 if role != "GK" else 0, dy=0,
            ))
        note = "Ball won — recycle and build patiently"

    else:
        # Hold shape — reset
        for i, p in enumerate(xi):
            if i >= len(slots):
                continue
            frame3_players.append(PlayerDelta(name=p.get("name", ""), dx=2.0, dy=0))
        note = "Ball cleared — reset shape"

    frames.append(SimFrame(
        frame=3, duration_ms=750,
        ball=BallState(x=clamp_x(line_x - 5), y=float(PH / 2)),
        ball_carrier=None,
        action=f"Ball won — {transition}",
        players=frame3_players, opp_players=[],
        note=note,
    ))

    return [f.to_dict() for f in frames]

