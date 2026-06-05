# core/scenario/in_possession/goal_kick.py
#
# Simulates playing out from the back — from GK to structured build-up.
#
# Depends on:
#   xi                    — starting XI with traits + slot positions
#   formation             — determines base slot coords
#   linkup_pairs          — outlet_from_back pair drives the main passing sequence
#   opposition.press_style — high = shorter time on ball, go earlier
#   opposition.attributes — if CDM marked weak → route avoids central channel
#   defensive_shape.block — how high CBs can push to receive

from core.scenario.types import SimFrame, BallState, PlayerDelta, OppDelta
from core.scenario.helpers import (
    get_slots, mirror_slots, has_trait, find_player,
    find_player_by_position, get_slot_for_player, player_slot_index,
    mirror_dy, clamp_x, clamp_y, get_linkup_players, PH,
)

def metadata(opposition: dict, tactical_focus: str, matchup_exploits: list[str]) -> dict:
    from core.scenario.types import ScenarioMeta
    press  = opposition.get("press_style") or "medium"
    focus  = (tactical_focus or "").lower()
    pace_exploit = next((e for e in matchup_exploits if "pace" in e.lower() or "slow" in e.lower()), None)
    return ScenarioMeta(
        scenario="transition",
        title="Win the ball — counter",
        phase="In possession",
        purpose=(
            "Exploit pace against their slow fullback on the break"
            if pace_exploit else
            "Rapid vertical transition after winning possession"
        ),
        takeaway=(
            f"Get the ball wide immediately — {pace_exploit.split('—')[0].strip() if pace_exploit else 'use the pace'} before they recover shape."
            if pace_exploit else
            f"Quick vertical pass — {'press is high so space opens behind their line' if press == 'high' else 'runners burst before defence sets'}."
        ),
    ).to_dict()

def build(
    xi: list[dict],
    formation: str,
    linkup_pairs: list[dict],
    opposition: dict,
    defensive_shape: dict,
) -> list[dict]:
    """
    Returns a list of SimFrame dicts for the goal kick / build-up scenario.
    """
    slots = get_slots(formation)
    opp_slots = mirror_slots(get_slots(opposition.get("likely_formation") or "4-3-3"))
    press_style = opposition.get("press_style") or "medium"
    opp_attrs = opposition.get("attributes") or {}
    block = (defensive_shape or {}).get("block") or "mid"

    # Identify key players by trait
    gk = xi[0] if xi else None
    ball_playing_cb = find_player(xi, "Ball Playing Defender", "Progressive Passer")
    deep_playmaker  = find_player(xi, "Deep Playmaker", "Sits Between Lines")
    sweeper_gk      = has_trait(gk or {}, "Sweeper Keeper", "Calm On Ball") if gk else False
    outlet_pair_a, outlet_pair_b = get_linkup_players(xi, linkup_pairs, "outlet_from_back")

    # Weak CDM in opposition → avoid central early, go wide first
    opp_cdm_weak = any(
        "weak" in str(v).lower() or "slow" in str(v).lower()
        for k, v in opp_attrs.items()
        if "cdm" in k.lower() or "midfield" in k.lower()
    )

    # High press → opposition pushes up, go longer sooner
    is_high_press = press_style == "high"

    # CB push-up delta based on block height
    cb_push = {"high": 12, "mid": 6, "low": 2, "deep": 0}.get(block, 6)

    frames: list[SimFrame] = []

    # ── Frame 1: GK has ball, CBs split wide ──────────────────────────────────
    gk_slot = slots[0] if slots else {"x": 14, "y": 65}
    cb1_slot = slots[1] if len(slots) > 1 else {"x": 52, "y": 20}
    cb2_slot = slots[2] if len(slots) > 2 else {"x": 52, "y": 48}
    cb3_slot = slots[3] if len(slots) > 3 else {"x": 52, "y": 82}
    cb4_slot = slots[4] if len(slots) > 4 else {"x": 52, "y": 110}

    frame1_players = []

    # GK steps out slightly if sweeper keeper
    if gk:
        gk_dx = 6.0 if sweeper_gk else 0.0
        frame1_players.append(PlayerDelta(
            name=gk.get("name", "GK"),
            dx=gk_dx, dy=0,
            is_ball_carrier=True,
            trait_label="Plays out from back" if sweeper_gk else None,
        ))

    # CBs spread to give passing angles — push forward by block amount
    for idx, (cb_slot, label) in enumerate([
        (cb1_slot, "Spreads wide"),
        (cb2_slot, None),
        (cb3_slot, None),
        (cb4_slot, "Spreads wide"),
    ]):
        if idx + 1 < len(xi):
            cb = xi[idx + 1]
            is_bpd = has_trait(cb, "Ball Playing Defender", "Progressive Passer")
            dy_spread = [-10, -5, 5, 10][idx]
            frame1_players.append(PlayerDelta(
                name=cb.get("name", f"CB{idx}"),
                dx=float(cb_push),
                dy=float(dy_spread),
                trait_label="Builds from back" if is_bpd else None,
            ))

    # Deep playmaker drops between CBs
    if deep_playmaker:
        dm_idx = player_slot_index(xi, deep_playmaker.get("name", ""))
        if dm_idx >= 0 and dm_idx < len(slots):
            dm_slot = slots[dm_idx]
            frame1_players.append(PlayerDelta(
                name=deep_playmaker.get("name", "CDM"),
                dx=-14.0,
                dy=mirror_dy(dm_slot["y"], 0),
                trait_label="Drops between CBs",
            ))

    # Opposition: high press = forwards surge forward
    frame1_opp = []
    for i, opp_slot in enumerate(opp_slots):
        if opp_slot["role"] == "FWD":
            dx = -22.0 if is_high_press else -8.0
            frame1_opp.append(OppDelta(
                slot_index=i,
                dx=dx, dy=0,
                reaction="pressing" if is_high_press else "hold",
            ))
        elif opp_slot["role"] == "MID" and is_high_press:
            frame1_opp.append(OppDelta(slot_index=i, dx=-10.0, dy=0, reaction="pressing"))

    frames.append(SimFrame(
        frame=1,
        duration_ms=900,
        ball=BallState(x=gk_slot["x"], y=gk_slot["y"]),
        ball_carrier=gk.get("name") if gk else None,
        action="GK plays short — CBs split to create passing angles",
        players=frame1_players,
        opp_players=frame1_opp,
        note="Building from the back" if not is_high_press else "Under pressure — quick decision needed",
    ))

    # ── Frame 2: Ball to ball-playing CB (or wide CB if opp CDM weak) ─────────
    target_cb = ball_playing_cb
    if not target_cb:
        # Fall back to first available CB
        target_cb = xi[1] if len(xi) > 1 else None

    target_cb_idx = player_slot_index(xi, target_cb.get("name", "")) if target_cb else 1
    target_cb_slot = slots[target_cb_idx] if target_cb_idx < len(slots) else cb2_slot

    frame2_players = []
    if target_cb:
        frame2_players.append(PlayerDelta(
            name=target_cb.get("name", "CB"),
            dx=0, dy=0,
            is_ball_target=True,
            trait_label="Receives — Ball Playing Defender" if has_trait(target_cb, "Ball Playing Defender") else None,
        ))

    # Deep playmaker offers short option
    if deep_playmaker:
        frame2_players.append(PlayerDelta(
            name=deep_playmaker.get("name", "CDM"),
            dx=-2.0, dy=0,
            trait_label="Short option",
        ))

    # FBs push slightly higher
    fb_indices = [i for i, p in enumerate(xi) if (p.get("slot_broad") or p.get("broad_position")) == "DEF"
                  and i not in [target_cb_idx]]
    for fb_i in fb_indices[:2]:
        if fb_i < len(xi) and fb_i < len(slots):
            fb = xi[fb_i]
            fb_slot = slots[fb_i]
            fb_dx = 8.0 if has_trait(fb, "Overlapping Full-Back", "Offensive Full-Back") else 4.0
            frame2_players.append(PlayerDelta(
                name=fb.get("name", "FB"),
                dx=fb_dx, dy=0,
                trait_label="Pushes forward" if has_trait(fb, "Overlapping Full-Back", "Offensive Full-Back") else None,
            ))

    # Opposition: if high press, one FWD closes the CB
    frame2_opp = []
    for i, opp_slot in enumerate(opp_slots):
        if opp_slot["role"] == "FWD" and is_high_press:
            # Closest FWD to target CB presses
            dx = target_cb_slot["x"] - opp_slot["x"]
            dy = target_cb_slot["y"] - opp_slot["y"]
            dist = (dx ** 2 + dy ** 2) ** 0.5
            if dist > 0:
                frame2_opp.append(OppDelta(
                    slot_index=i,
                    dx=dx * 0.6, dy=dy * 0.6,
                    reaction="pressing",
                ))
            break

    frames.append(SimFrame(
        frame=2,
        duration_ms=800,
        ball=BallState(
            x=float(target_cb_slot["x"] + cb_push),
            y=float(target_cb_slot["y"]),
        ),
        ball_carrier=target_cb.get("name") if target_cb else None,
        action=f"Ball to {target_cb.get('name', 'CB').split()[0]} — carries forward",
        players=frame2_players,
        opp_players=frame2_opp,
        note="Ball playing CB receives — midfield must offer angles",
    ))

    # ── Frame 3: Switch of play OR outlet to deep playmaker ───────────────────
    # If opp CDM weak → exploit central with deep playmaker
    # Otherwise → switch to far side FB for width

    frame3_players = []
    frame3_opp = []

    if opp_cdm_weak and deep_playmaker:
        # Route through CDM gap
        dm_idx = player_slot_index(xi, deep_playmaker.get("name", ""))
        dm_slot = slots[dm_idx] if dm_idx < len(slots) else {"x": 90, "y": 65}

        frame3_players.append(PlayerDelta(
            name=deep_playmaker.get("name", "CDM"),
            dx=10.0, dy=0,
            is_ball_target=True,
            trait_label="Exploits CDM gap",
        ))

        # Attacking MIDs push forward
        for i, p in enumerate(xi):
            role = (p.get("slot_broad") or p.get("broad_position") or "")
            if role == "MID" and p.get("name") != deep_playmaker.get("name") and i < len(slots):
                frame3_players.append(PlayerDelta(
                    name=p.get("name", "MID"),
                    dx=12.0, dy=0,
                ))

        ball_x = float(dm_slot["x"] + 10)
        ball_y = float(dm_slot["y"])
        action = f"Through {deep_playmaker.get('name', 'CDM').split()[0]} — opponent CDM pulled wide"
        note = "Exploiting weak CDM — central overload"

    else:
        # Switch to far FB
        far_fb = None
        far_fb_slot = None
        for i, p in enumerate(xi[1:5], start=1):
            if i < len(slots):
                s = slots[i]
                # Pick the FB furthest from the ball-playing CB
                if far_fb is None or abs(s["y"] - target_cb_slot["y"]) > abs(
                    (far_fb_slot or {"y": 0})["y"] - target_cb_slot["y"]
                ):
                    far_fb = p
                    far_fb_slot = s

        if far_fb and far_fb_slot:
            frame3_players.append(PlayerDelta(
                name=far_fb.get("name", "FB"),
                dx=10.0, dy=0,
                is_ball_target=True,
                trait_label="Receives switch" if has_trait(far_fb, "Overlapping Full-Back") else None,
            ))
            ball_x = float(far_fb_slot["x"] + 10)
            ball_y = float(far_fb_slot["y"])
            action = f"Switch of play to {far_fb.get('name', 'FB').split()[0]} — opens up wide"
        else:
            ball_x = float(target_cb_slot["x"] + 25)
            ball_y = float(target_cb_slot["y"])
            action = "Carries forward into midfield"

        note = "Switch of play — exploit weak side" if not opp_cdm_weak else None

        # Opposition shifts to cover the switch
        for i, opp_slot in enumerate(opp_slots):
            if opp_slot["role"] == "MID":
                frame3_opp.append(OppDelta(
                    slot_index=i,
                    dx=0,
                    dy=(ball_y - opp_slot["y"]) * 0.3,
                    reaction="tracking",
                ))

    # FWDs make runs to stretch defence
    for i, p in enumerate(xi):
        role = p.get("slot_broad") or p.get("broad_position") or ""
        if role == "FWD" and i < len(slots):
            fwd_slot = slots[i]
            run_dx = 15.0 if has_trait(p, "Runs In Behind", "Counterattacking Runner") else 8.0
            run_dy = mirror_dy(fwd_slot["y"], -8.0 if i % 2 == 0 else 8.0)
            frame3_players.append(PlayerDelta(
                name=p.get("name", "FWD"),
                dx=run_dx, dy=run_dy,
                trait_label="Makes run" if has_trait(p, "Runs In Behind") else None,
            ))

    frames.append(SimFrame(
        frame=3,
        duration_ms=900,
        ball=BallState(x=clamp_x(ball_x), y=clamp_y(ball_y)),
        ball_carrier=None,
        action=action,
        players=frame3_players,
        opp_players=frame3_opp,
        note=note,
    ))

    # ── Frame 4: Advance into midfield — outlet pair combination ─────────────
    frame4_players = []
    frame4_opp = []

    if outlet_pair_a and outlet_pair_b:
        # Linkup pair does their combination
        pa_idx = player_slot_index(xi, outlet_pair_a.get("name", ""))
        pb_idx = player_slot_index(xi, outlet_pair_b.get("name", ""))
        pa_slot = slots[pa_idx] if pa_idx < len(slots) else {"x": 90, "y": 65}
        pb_slot = slots[pb_idx] if pb_idx < len(slots) else {"x": 110, "y": 65}

        frame4_players.append(PlayerDelta(
            name=outlet_pair_a.get("name", ""),
            dx=8.0, dy=0,
            is_ball_carrier=True,
            trait_label="Outlet from back",
        ))
        frame4_players.append(PlayerDelta(
            name=outlet_pair_b.get("name", ""),
            dx=6.0, dy=0,
            is_ball_target=True,
        ))
        ball_x = clamp_x(float(pb_slot["x"] + 6))
        ball_y = clamp_y(float(pb_slot["y"]))
        action = f"{outlet_pair_a.get('name','').split()[0]} finds {outlet_pair_b.get('name','').split()[0]} — advancing"
    else:
        # Generic midfield advance
        ball_x = clamp_x(ball_x + 20)
        ball_y = clamp_y(ball_y)
        action = "Midfield advance — looking for final pass"

    # FWDs hold or run depending on traits
    for i, p in enumerate(xi):
        role = p.get("slot_broad") or p.get("broad_position") or ""
        if role == "FWD" and i < len(slots):
            fwd_slot = slots[i]
            if has_trait(p, "Target Man", "Holds Up Play"):
                frame4_players.append(PlayerDelta(
                    name=p.get("name", "ST"),
                    dx=2.0, dy=0,
                    trait_label="Holds up play",
                ))
            elif has_trait(p, "Runs In Behind"):
                frame4_players.append(PlayerDelta(
                    name=p.get("name", "ST"),
                    dx=20.0, dy=mirror_dy(fwd_slot["y"], -10.0),
                    trait_label="Run in behind",
                ))

    # Opposition defensive line holds depth
    for i, opp_slot in enumerate(opp_slots):
        if opp_slot["role"] == "DEF":
            frame4_opp.append(OppDelta(slot_index=i, dx=0, dy=0, reaction="hold"))

    frames.append(SimFrame(
        frame=4,
        duration_ms=850,
        ball=BallState(x=ball_x, y=ball_y),
        ball_carrier=outlet_pair_b.get("name") if outlet_pair_b else None,
        action=action,
        players=frame4_players,
        opp_players=frame4_opp,
        note="In the final third — create and finish",
    ))

    return [f.to_dict() for f in frames]

