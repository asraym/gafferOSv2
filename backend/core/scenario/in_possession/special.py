# core/scenario/in_possession/special.py
#
# Simulates the engine's featured tactical scenario.
# Driven by tactical_focus + matchup_exploits + opposition attributes.
#
# Cases handled:
#   Wide Attacking Play   — FB/Winger overlap, cut inside
#   High Press & Dominate — collective press from front
#   Possession & Build-Up — triangles, recycling, patience
#   Counter-Attacking     — fast vertical (delegates to transition for frame detail)
#   Exploit: slow LB      — direct simulation of that specific channel
#   Exploit: weak CDM     — CAM drifts into space, overload centrally

from core.scenario.types import SimFrame, BallState, PlayerDelta, OppDelta
from core.scenario.helpers import (
    get_slots, mirror_slots, has_trait, find_player,
    player_slot_index, mirror_dy, clamp_x, clamp_y,
    get_linkup_players, PH, PW,
)

def metadata(
    tactical_focus: str,
    matchup_exploits: list[str],
    matchup_vulnerabilities: list[str],
    opposition: dict,
) -> dict:
    from core.scenario.types import ScenarioMeta
    focus = (tactical_focus or "").lower()
 
    slow_lb  = any("left back" in e.lower() and "slow" in e.lower() for e in matchup_exploits)
    slow_rb  = any("right back" in e.lower() and "slow" in e.lower() for e in matchup_exploits)
    weak_cdm = any("cdm" in e.lower() for e in matchup_exploits)
    aerial   = any("aerial" in e.lower() for e in matchup_exploits)
 
    if slow_lb or slow_rb:
        flank = "right" if slow_lb else "left"
        return ScenarioMeta(
            scenario="special",
            title=f"{'Right' if slow_lb else 'Left'}-side overload",
            phase="In possession",
            purpose=f"Isolate their slow {'left' if slow_lb else 'right'} back with pace and movement",
            takeaway=f"Get the ball into the {'right' if slow_lb else 'left'} channel early — their {'LB' if slow_lb else 'RB'} can't recover once beaten.",
        ).to_dict()
    elif weak_cdm:
        return ScenarioMeta(
            scenario="special",
            title="Central overload",
            phase="In possession",
            purpose="Draw the CDM wide and exploit the space with the CAM",
            takeaway="Their CDM follows the ball — the CAM must time the drift centrally to receive in space.",
        ).to_dict()
    elif aerial:
        return ScenarioMeta(
            scenario="special",
            title="Aerial dominance",
            phase="In possession",
            purpose="Use the aerial advantage to win second balls and create",
            takeaway="Long ball to the target man — runners attack second ball. Their defence is weak in the air.",
        ).to_dict()
    elif "wide" in focus or "wing" in focus:
        return ScenarioMeta(
            scenario="special",
            title="Wing play",
            phase="In possession",
            purpose="Overlap and cutback combination down the flank",
            takeaway="FB overlaps, winger cuts inside — creates a 2v1 on the fullback and opens cutback lanes.",
        ).to_dict()
    elif "press" in focus:
        return ScenarioMeta(
            scenario="special",
            title="High press trigger",
            phase="In possession",
            purpose="Win the ball high up the pitch through coordinated press",
            takeaway="Forwards trigger on the back pass — midfield covers the second ball. Forces long ball from keeper.",
        ).to_dict()
    else:
        return ScenarioMeta(
            scenario="special",
            title="Possession build-up",
            phase="In possession",
            purpose="Patient triangles to draw opposition and find the killer pass",
            takeaway="Recycle until the CDM gap opens — combination play between midfield and forward creates the chance.",
        ).to_dict()


def build(
    xi: list[dict],
    formation: str,
    linkup_pairs: list[dict],
    opposition: dict,
    tactical_focus: str,
    matchup_exploits: list[str],
    matchup_vulnerabilities: list[str],
) -> list[dict]:
    slots = get_slots(formation)
    opp_slots = mirror_slots(get_slots(opposition.get("likely_formation") or "4-3-3"))
    opp_attrs = opposition.get("attributes") or {}
    focus = (tactical_focus or "").lower()

    # Detect scenario type
    slow_lb      = any("left back" in e.lower() and ("slow" in e.lower() or "pace" in e.lower()) for e in matchup_exploits)
    slow_rb      = any("right back" in e.lower() and ("slow" in e.lower() or "pace" in e.lower()) for e in matchup_exploits)
    weak_cdm     = any("cdm" in e.lower() or ("central" in e.lower() and "weak" in e.lower()) for e in matchup_exploits)
    aerial_vuln  = any("aerial" in e.lower() for e in matchup_exploits)

    # Route to sub-builder
    if slow_lb or slow_rb:
        return _exploit_slow_fullback(xi, slots, opp_slots, linkup_pairs, slow_lb)
    elif weak_cdm:
        return _exploit_weak_cdm(xi, slots, opp_slots, linkup_pairs)
    elif aerial_vuln:
        return _exploit_aerial(xi, slots, opp_slots)
    elif "wide" in focus or "wing" in focus:
        return _wing_play(xi, slots, opp_slots, linkup_pairs)
    elif "press" in focus or "high" in focus:
        return _high_press(xi, slots, opp_slots, opposition)
    elif "possession" in focus or "build" in focus:
        return _possession_build(xi, slots, opp_slots, linkup_pairs)
    else:
        # Default — wing play as the most visual scenario
        return _wing_play(xi, slots, opp_slots, linkup_pairs)


# ── Wing Play ──────────────────────────────────────────────────────────────────

def _wing_play(
    xi: list[dict],
    slots: list[dict],
    opp_slots: list[dict],
    linkup_pairs: list[dict],
) -> list[dict]:
    frames: list[SimFrame] = []

    # Key players
    off_fb      = find_player(xi, "Overlapping Full-Back", "Offensive Full-Back")
    winger      = find_player(xi, "Holds Width", "Cuts Inside", "Drifts Central")
    cam         = find_player(xi, "Through Ball", "Combination Play", "Drifts Into Channels")
    stays_back  = find_player(xi, "Stays Back", "Defensive Full-Back")
    if stays_back and stays_back == winger:
        stays_back = None
    fb_winger_a, fb_winger_b = get_linkup_players(xi, linkup_pairs, "fb_winger_overlap")

    # Determine which flank the overlap is on
    off_fb_idx  = player_slot_index(xi, off_fb.get("name", "")) if off_fb else 1
    off_fb_slot = slots[off_fb_idx] if off_fb_idx < len(slots) else {"x": 52, "y": 20}
    top_half    = off_fb_slot["y"] < PH / 2

    # ── Frame 1: Shape — FB pushes, winger checks inside ─────────────────────
    frame1_players = []

    if off_fb:
        frame1_players.append(PlayerDelta(
            name=off_fb.get("name", ""),
            dx=18.0, dy=mirror_dy(off_fb_slot["y"], -8.0),
            trait_label="Overlapping run",
        ))

    if winger:
        w_idx  = player_slot_index(xi, winger.get("name", ""))
        w_slot = slots[w_idx] if w_idx < len(slots) else {"x": 158, "y": 20}
        frame1_players.append(PlayerDelta(
            name=winger.get("name", ""),
            dx=5.0, dy=mirror_dy(w_slot["y"], 10.0),   # drift inside
            trait_label="Drifts inside to create space",
        ))

    if stays_back:
        sb_idx  = player_slot_index(xi, stays_back.get("name", ""))
        sb_slot = slots[sb_idx] if sb_idx < len(slots) else {"x": 52, "y": 110}
        frame1_players.append(PlayerDelta(
            name=stays_back.get("name", ""),
            dx=-4.0, dy=0,
            trait_label="Stays back — balance",
        ))

    # Opp: LB/RB tracks the overlap
    for i, opp_slot in enumerate(opp_slots):
        if opp_slot["role"] == "DEF":
            pass  # holds for now

    frames.append(SimFrame(
        frame=1,
        duration_ms=900,
        ball=BallState(x=float(off_fb_slot["x"] - 10), y=float(off_fb_slot["y"])),
        ball_carrier=None,
        action="FB overlaps — winger drifts inside to create space",
        players=frame1_players,
        opp_players=[],
        note="Width created — triangle forming on the flank",
    ))

    # ── Frame 2: FB receives wide — winger creates inside channel ─────────────
    frame2_players = []
    frame2_opp = []

    if off_fb:
        frame2_players.append(PlayerDelta(
            name=off_fb.get("name", ""),
            dx=0, dy=0,
            is_ball_carrier=True,
            trait_label="Ball at feet — crossing option",
        ))

    if cam:
        cam_idx  = player_slot_index(xi, cam.get("name", ""))
        cam_slot = slots[cam_idx] if cam_idx < len(slots) else {"x": 158, "y": 65}
        frame2_players.append(PlayerDelta(
            name=cam.get("name", ""),
            dx=12.0, dy=mirror_dy(cam_slot["y"], -10.0),
            trait_label="Drifts into channel" if has_trait(cam, "Drifts Into Channels") else None,
        ))

    # ST makes near-post run
    for i, p in enumerate(xi):
        role = (p.get("slot_broad") or p.get("broad_position") or "")
        if role == "FWD" and i < len(slots):
            fwd_slot = slots[i]
            frame2_players.append(PlayerDelta(
                name=p.get("name", "ST"),
                dx=12.0, dy=mirror_dy(fwd_slot["y"], -15.0),
                trait_label="Near post run" if has_trait(p, "Target Man") else None,
            ))

    # Opp fullback has to choose — track FB or hold shape
    for i, opp_slot in enumerate(opp_slots):
        if opp_slot["role"] == "DEF":
            dy_shift = mirror_dy(opp_slot["y"], -8.0) if top_half else mirror_dy(opp_slot["y"], 8.0)
            frame2_opp.append(OppDelta(slot_index=i, dx=-5.0, dy=dy_shift, reaction="tracking"))
            break

    ball_x = clamp_x(float(off_fb_slot["x"] + 18))
    ball_y = clamp_y(float(off_fb_slot["y"] + mirror_dy(off_fb_slot["y"], -8.0)))

    frames.append(SimFrame(
        frame=2,
        duration_ms=850,
        ball=BallState(x=ball_x, y=ball_y),
        ball_carrier=off_fb.get("name") if off_fb else None,
        action="FB drives to byline — cross or cutback option",
        players=frame2_players,
        opp_players=frame2_opp,
        note="Cross or cutback — runners attacking the box",
    ))

    # ── Frame 3: Delivery — attackers attack the box ──────────────────────────
    frame3_players = []
    frame3_opp = []

    for i, p in enumerate(xi):
        role = (p.get("slot_broad") or p.get("broad_position") or "")
        if role == "FWD" and i < len(slots):
            fwd_slot = slots[i]
            frame3_players.append(PlayerDelta(
                name=p.get("name", "ST"),
                dx=clamp_x(PW - 18 - fwd_slot["x"]),
                dy=mirror_dy(fwd_slot["y"], -10.0),
                trait_label="Attacks delivery" if has_trait(p, "Target Man", "Strong In Air") else None,
            ))
        elif role == "MID" and has_trait(p, "Box To Box", "Late Run Into Box"):
            frame3_players.append(PlayerDelta(
                name=p.get("name", ""),
                dx=25.0, dy=mirror_dy(slots[i]["y"], -12.0),
                trait_label="Late run",
            ))

    for i, opp_slot in enumerate(opp_slots):
        if opp_slot["role"] == "DEF":
            frame3_opp.append(OppDelta(slot_index=i, dx=0, dy=0, reaction="marking"))

    frames.append(SimFrame(
        frame=3,
        duration_ms=800,
        ball=BallState(x=clamp_x(PW - 15), y=clamp_y(PH / 2 + (20 if top_half else -20))),
        ball_carrier=None,
        action="Cross into the box — runners attacking",
        players=frame3_players,
        opp_players=frame3_opp,
        note="Quality of delivery and movement decides the chance",
    ))

    return [f.to_dict() for f in frames]


# ── Exploit: Slow Fullback ─────────────────────────────────────────────────────

def _exploit_slow_fullback(
    xi: list[dict],
    slots: list[dict],
    opp_slots: list[dict],
    linkup_pairs: list[dict],
    exploit_left: bool,   # True = their LB is slow = attack on right
) -> list[dict]:
    frames: list[SimFrame] = []

    # Find our fast winger / FB on the exploiting side
    pace_player = find_player(xi, "Counterattacking Runner", "Runs In Behind", "Offensive Full-Back", "Overlapping Full-Back")
    cm = find_player(xi, "Progressive Passer", "Through Ball", "Box To Box")

    target_slot_y = 20.0 if exploit_left else 110.0  # attack the correct flank
    pace_idx  = player_slot_index(xi, pace_player.get("name", "")) if pace_player else -1
    pace_slot = slots[pace_idx] if pace_idx >= 0 and pace_idx < len(slots) else {"x": 130, "y": target_slot_y}
    cm_idx    = player_slot_index(xi, cm.get("name", "")) if cm else -1
    cm_slot   = slots[cm_idx] if cm_idx >= 0 and cm_idx < len(slots) else {"x": 100, "y": 65}

    # Find the slow opp FB slot index
    slow_fb_opp_idx = None
    for i, s in enumerate(opp_slots):
        if s["role"] == "DEF":
            if exploit_left and s["y"] > PH / 2:     # their LB = bottom of mirrored
                slow_fb_opp_idx = i; break
            elif not exploit_left and s["y"] < PH / 2:
                slow_fb_opp_idx = i; break

    # Frame 1: CM plays into the channel — pace player accelerates
    frame1_players = []
    if cm:
        frame1_players.append(PlayerDelta(
            name=cm.get("name", ""), dx=5.0, dy=0,
            is_ball_carrier=True, trait_label="Plays into channel",
        ))
    if pace_player:
        frame1_players.append(PlayerDelta(
            name=pace_player.get("name", ""),
            dx=30.0, dy=mirror_dy(pace_slot["y"], -8.0),
            is_ball_target=True,
            trait_label="Exploiting slow fullback",
        ))

    frame1_opp = []
    if slow_fb_opp_idx is not None:
        frame1_opp.append(OppDelta(
            slot_index=slow_fb_opp_idx, dx=-5.0, dy=0,
            reaction="tracking",  # slow — can't keep up
        ))

    frames.append(SimFrame(
        frame=1, duration_ms=800,
        ball=BallState(x=float(cm_slot["x"] + 5), y=float(cm_slot["y"])),
        ball_carrier=cm.get("name") if cm else None,
        action=f"Ball played into channel — {'right' if exploit_left else 'left'} flank exploit",
        players=frame1_players, opp_players=frame1_opp,
        note=f"Their {'left' if exploit_left else 'right'} back is slow — exploit the space",
    ))

    # Frame 2: Pace player in behind — 1v1 or cross
    frame2_players = []
    if pace_player:
        frame2_players.append(PlayerDelta(
            name=pace_player.get("name", ""),
            dx=18.0, dy=mirror_dy(pace_slot["y"], -5.0),
            is_ball_carrier=True,
            trait_label="In behind — 1v1",
        ))

    # ST makes run to near post
    for i, p in enumerate(xi):
        role = p.get("slot_broad") or p.get("broad_position") or ""
        if role == "FWD" and p != pace_player and i < len(slots):
            fwd_slot = slots[i]
            frame2_players.append(PlayerDelta(
                name=p.get("name", "ST"),
                dx=clamp_x(PW - 18 - fwd_slot["x"]),
                dy=mirror_dy(fwd_slot["y"], -10.0),
                trait_label="Near post" if has_trait(p, "Target Man") else None,
            ))

    if slow_fb_opp_idx is not None:
        frame2_opp = [OppDelta(slot_index=slow_fb_opp_idx, dx=-8.0, dy=0, reaction="retreating")]
    else:
        frame2_opp = []

    ball_x = clamp_x(float(pace_slot["x"] + 50))
    ball_y = clamp_y(float(target_slot_y))

    frames.append(SimFrame(
        frame=2, duration_ms=750,
        ball=BallState(x=ball_x, y=ball_y),
        ball_carrier=pace_player.get("name") if pace_player else None,
        action="In behind — cross or shoot",
        players=frame2_players, opp_players=frame2_opp,
        note="Slow fullback beaten — quality finish needed",
    ))

    return [f.to_dict() for f in frames]


# ── Exploit: Weak CDM ──────────────────────────────────────────────────────────

def _exploit_weak_cdm(
    xi: list[dict],
    slots: list[dict],
    opp_slots: list[dict],
    linkup_pairs: list[dict],
) -> list[dict]:
    frames: list[SimFrame] = []

    cam   = find_player(xi, "Through Ball", "Drifts Into Channels", "Creative Flair", "Combination Play")
    cm    = find_player(xi, "Progressive Passer", "Box To Box", "Deep Playmaker")
    fwd   = next((p for p in xi if (p.get("slot_broad") or p.get("broad_position")) == "FWD"), None)

    cam_idx  = player_slot_index(xi, cam.get("name", "")) if cam else -1
    cam_slot = slots[cam_idx] if cam_idx >= 0 and cam_idx < len(slots) else {"x": 158, "y": 65}
    cm_idx   = player_slot_index(xi, cm.get("name", "")) if cm else -1
    cm_slot  = slots[cm_idx] if cm_idx >= 0 and cm_idx < len(slots) else {"x": 100, "y": 65}

    # Find opp CDM (mid closest to centre of pitch)
    opp_cdm_idx = None
    for i, s in enumerate(opp_slots):
        if s["role"] == "MID" and abs(s["y"] - PH / 2) < 20:
            opp_cdm_idx = i; break

    # Frame 1: CM draws CDM out — CAM drifts into vacated space
    frame1_players = []
    if cm:
        frame1_players.append(PlayerDelta(
            name=cm.get("name", ""), dx=8.0, dy=mirror_dy(cm_slot["y"], 10.0),
            is_ball_carrier=True, trait_label="Draws CDM out",
        ))
    if cam:
        frame1_players.append(PlayerDelta(
            name=cam.get("name", ""), dx=10.0, dy=mirror_dy(cam_slot["y"], -12.0),
            trait_label="Drifts into CDM space",
        ))

    frame1_opp = []
    if opp_cdm_idx is not None:
        frame1_opp.append(OppDelta(
            slot_index=opp_cdm_idx, dx=mirror_dy(opp_slots[opp_cdm_idx]["y"], 10.0), dy=0,
            reaction="tracking",
        ))

    frames.append(SimFrame(
        frame=1, duration_ms=900,
        ball=BallState(x=float(cm_slot["x"] + 8), y=float(cm_slot["y"])),
        ball_carrier=cm.get("name") if cm else None,
        action="Drawing the CDM wide — CAM finds the space",
        players=frame1_players, opp_players=frame1_opp,
        note="Weak CDM pulled out — central channel opens",
    ))

    # Frame 2: CAM in the hole — plays through to striker
    frame2_players = []
    if cam:
        frame2_players.append(PlayerDelta(
            name=cam.get("name", ""),
            dx=15.0, dy=0,
            is_ball_carrier=True,
            trait_label="In the hole — through ball",
        ))
    if fwd:
        fwd_idx  = player_slot_index(xi, fwd.get("name", ""))
        fwd_slot = slots[fwd_idx] if fwd_idx < len(slots) else {"x": 190, "y": 65}
        frame2_players.append(PlayerDelta(
            name=fwd.get("name", "ST"),
            dx=12.0, dy=mirror_dy(fwd_slot["y"], -8.0),
            is_ball_target=True,
            trait_label="Runs onto through ball",
        ))

    frames.append(SimFrame(
        frame=2, duration_ms=800,
        ball=BallState(x=clamp_x(float(cam_slot["x"] + 25)), y=clamp_y(float(cam_slot["y"]))),
        ball_carrier=cam.get("name") if cam else None,
        action="CAM threads through ball — striker runs on",
        players=frame2_players, opp_players=[],
        note="Central overload — defence exposed",
    ))

    return [f.to_dict() for f in frames]


# ── Exploit: Aerial ───────────────────────────────────────────────────────────

def _exploit_aerial(
    xi: list[dict],
    slots: list[dict],
    opp_slots: list[dict],
) -> list[dict]:
    frames: list[SimFrame] = []

    aerial_player = find_player(xi, "Target Man", "Strong In Air", "Physical Dominant")
    cm = find_player(xi, "Progressive Passer", "Box To Box")

    aerial_idx  = player_slot_index(xi, aerial_player.get("name", "")) if aerial_player else -1
    aerial_slot = slots[aerial_idx] if aerial_idx >= 0 and aerial_idx < len(slots) else {"x": 190, "y": 65}

    # Frame 1: Long diagonal played to aerial player
    frame1_players = []
    if aerial_player:
        frame1_players.append(PlayerDelta(
            name=aerial_player.get("name", ""),
            dx=8.0, dy=0,
            is_ball_target=True,
            trait_label="Aerial dominance — wins the header",
        ))
    if cm:
        frame1_players.append(PlayerDelta(
            name=cm.get("name", ""), dx=5.0, dy=0,
            is_ball_carrier=True, trait_label="Long ball",
        ))

    # Runners attack second ball
    for i, p in enumerate(xi):
        role = p.get("slot_broad") or p.get("broad_position") or ""
        if role == "MID" and p != cm and i < len(slots):
            frame1_players.append(PlayerDelta(
                name=p.get("name", ""), dx=15.0, dy=mirror_dy(slots[i]["y"], -10.0),
                trait_label="Second ball" if has_trait(p, "Box To Box") else None,
            ))

    frames.append(SimFrame(
        frame=1, duration_ms=900,
        ball=BallState(x=float(aerial_slot["x"]), y=float(aerial_slot["y"])),
        ball_carrier=None,
        action="Long ball to aerial threat — attack second ball",
        players=frame1_players, opp_players=[],
        note="Aerial dominance — opposition weak in the air",
    ))

    return [f.to_dict() for f in frames]


# ── High Press ────────────────────────────────────────────────────────────────

def _high_press(
    xi: list[dict],
    slots: list[dict],
    opp_slots: list[dict],
    opposition: dict,
) -> list[dict]:
    frames: list[SimFrame] = []

    press_trigger = find_player(xi, "Presses High", "Counterattacking Runner", "Target Man")
    cm_press      = find_player(xi, "Box To Box", "Covers Ground", "Counterpressing")
    opp_gk_slot   = opp_slots[0] if opp_slots else {"x": PW - 14, "y": 65}

    # Frame 1: Press trigger — forwards close GK/CBs
    frame1_players = []
    for i, p in enumerate(xi):
        role = (p.get("slot_broad") or p.get("broad_position") or "")
        if role == "FWD" and i < len(slots):
            fwd_slot = slots[i]
            press_dx = clamp_x(PW - 30 - fwd_slot["x"])
            frame1_players.append(PlayerDelta(
                name=p.get("name", "FWD"),
                dx=press_dx, dy=mirror_dy(fwd_slot["y"], -5.0),
                trait_label="Press trigger" if has_trait(p, "Presses High") else "Closes down",
            ))
        elif role == "MID" and has_trait(p, "Box To Box", "Covers Ground", "Counterpressing"):
            frame1_players.append(PlayerDelta(
                name=p.get("name", "MID"),
                dx=15.0, dy=0,
                trait_label="Counterpresses",
            ))

    # Opposition scrambles under pressure
    frame1_opp = []
    for i, s in enumerate(opp_slots[:6]):
        if s["role"] in ["GK", "DEF"]:
            frame1_opp.append(OppDelta(slot_index=i, dx=0, dy=0, reaction="hold"))

    frames.append(SimFrame(
        frame=1, duration_ms=800,
        ball=BallState(x=float(PW - 35), y=float(PH / 2)),
        ball_carrier=None,
        action="High press triggered — forwards close down GK and CBs",
        players=frame1_players, opp_players=frame1_opp,
        note="Force the mistake high up the pitch",
    ))

    # Frame 2: Press wins the ball — immediate attack
    frame2_players = []
    if press_trigger:
        pt_idx  = player_slot_index(xi, press_trigger.get("name", ""))
        pt_slot = slots[pt_idx] if pt_idx < len(slots) else {"x": 175, "y": 65}
        frame2_players.append(PlayerDelta(
            name=press_trigger.get("name", ""),
            dx=0, dy=0,
            is_ball_carrier=True,
            trait_label="Wins it high — immediate threat",
        ))

    frames.append(SimFrame(
        frame=2, duration_ms=700,
        ball=BallState(x=float(PW - 30), y=float(PH / 2)),
        ball_carrier=press_trigger.get("name") if press_trigger else None,
        action="Press wins possession — shoot or square it",
        players=frame2_players, opp_players=[],
        note="High turnover — high chance",
    ))

    return [f.to_dict() for f in frames]


# ── Possession Build-Up ───────────────────────────────────────────────────────

def _possession_build(
    xi: list[dict],
    slots: list[dict],
    opp_slots: list[dict],
    linkup_pairs: list[dict],
) -> list[dict]:
    frames: list[SimFrame] = []

    deep_pm  = find_player(xi, "Deep Playmaker", "Sits Between Lines")
    cb_build = find_player(xi, "Ball Playing Defender", "Progressive Passer")
    cam      = find_player(xi, "Through Ball", "Combination Play", "Creative Flair")
    combo_a, combo_b = get_linkup_players(xi, linkup_pairs, "midfield_forward_combo")

    deep_pm_idx  = player_slot_index(xi, deep_pm.get("name", "")) if deep_pm else -1
    deep_pm_slot = slots[deep_pm_idx] if deep_pm_idx >= 0 and deep_pm_idx < len(slots) else {"x": 92, "y": 65}
    cb_idx       = player_slot_index(xi, cb_build.get("name", "")) if cb_build else 2
    cb_slot      = slots[cb_idx] if cb_idx < len(slots) else {"x": 52, "y": 48}

    # Frame 1: Triangles — CB → CDM → back → switch
    frame1_players = []
    if cb_build:
        frame1_players.append(PlayerDelta(
            name=cb_build.get("name", ""), dx=5.0, dy=0,
            is_ball_carrier=True, trait_label="Progressive pass",
        ))
    if deep_pm:
        frame1_players.append(PlayerDelta(
            name=deep_pm.get("name", ""), dx=3.0, dy=mirror_dy(deep_pm_slot["y"], 8.0),
            is_ball_target=True, trait_label="Receives — recycling",
        ))

    # All MIDs spread to offer options
    for i, p in enumerate(xi):
        role = (p.get("slot_broad") or p.get("broad_position") or "")
        if role == "MID" and p != deep_pm and i < len(slots):
            mid_slot = slots[i]
            frame1_players.append(PlayerDelta(
                name=p.get("name", "MID"),
                dx=8.0, dy=mirror_dy(mid_slot["y"], 6.0 if i % 2 == 0 else -6.0),
            ))

    # Opposition holds mid-block — doesn't press
    frame1_opp = []
    for i, s in enumerate(opp_slots):
        if s["role"] == "MID":
            frame1_opp.append(OppDelta(slot_index=i, dx=-4.0, dy=0, reaction="hold"))

    frames.append(SimFrame(
        frame=1, duration_ms=1000,
        ball=BallState(x=float(cb_slot["x"] + 5), y=float(cb_slot["y"])),
        ball_carrier=cb_build.get("name") if cb_build else None,
        action="Patient build — triangles in midfield, probing for openings",
        players=frame1_players, opp_players=frame1_opp,
        note="Possession — wait for the right moment",
    ))

    # Frame 2: Midfield combo — combination play into final third
    frame2_players = []
    if combo_a and combo_b:
        ca_idx  = player_slot_index(xi, combo_a.get("name", ""))
        cb2_idx = player_slot_index(xi, combo_b.get("name", ""))
        ca_slot = slots[ca_idx] if ca_idx < len(slots) else {"x": 138, "y": 65}
        cb2_slot = slots[cb2_idx] if cb2_idx < len(slots) else {"x": 175, "y": 65}

        frame2_players.append(PlayerDelta(
            name=combo_a.get("name", ""), dx=10.0, dy=0,
            is_ball_carrier=True, trait_label="One-two",
        ))
        frame2_players.append(PlayerDelta(
            name=combo_b.get("name", ""), dx=12.0, dy=mirror_dy(cb2_slot["y"], -8.0),
            is_ball_target=True, trait_label="Combination",
        ))
        action = f"One-two — {combo_a.get('name','').split()[0]} and {combo_b.get('name','').split()[0]}"
    else:
        # CAM drives forward
        if cam:
            cam_idx  = player_slot_index(xi, cam.get("name", ""))
            cam_slot = slots[cam_idx] if cam_idx < len(slots) else {"x": 158, "y": 65}
            frame2_players.append(PlayerDelta(
                name=cam.get("name", ""), dx=15.0, dy=0,
                is_ball_carrier=True, trait_label="Drives into space",
            ))
        action = "Breaking into final third — look for the killer pass"

    frame2_opp = []
    for i, s in enumerate(opp_slots):
        if s["role"] == "DEF":
            frame2_opp.append(OppDelta(slot_index=i, dx=0, dy=0, reaction="hold"))

    frames.append(SimFrame(
        frame=2, duration_ms=900,
        ball=BallState(x=clamp_x(160.0), y=clamp_y(PH / 2)),
        ball_carrier=None,
        action=action,
        players=frame2_players, opp_players=frame2_opp,
        note="Final third — find the decisive pass",
    ))

    return [f.to_dict() for f in frames]