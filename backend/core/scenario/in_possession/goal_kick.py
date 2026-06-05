# core/scenario/in_possession/goal_kick.py — v2

from core.scenario.types import (
    SimFrame, BallState, PlayerDelta, OppDelta,
    BallIntent, Callout, ScenarioMeta,
)
from core.scenario.helpers import (
    get_slots, mirror_slots, has_trait, find_player,
    player_slot_index, mirror_dy, clamp_x, clamp_y,
    get_linkup_players, get_slot_key, get_opp_slot_key, PH,
)


def metadata(opposition: dict, matchup_exploits: list[str]) -> dict:
    press = opposition.get("press_style") or "medium"
    opp   = opposition.get("opponent_name") or "the opposition"
    weak_side = next(
        ("right" if "left back" in e.lower() else "left"
         for e in matchup_exploits if "back" in e.lower()), None
    )
    return ScenarioMeta(
        scenario="goal_kick",
        title="Build from the back",
        phase="In possession",
        purpose=(
            f"Play through {press} press and advance into midfield"
            if press == "high"
            else "Establish possession from goalkeeper and build structured attack"
        ),
        takeaway=(
            f"Quick recycling required — {opp} press high and look to win the ball early. "
            f"{'Switch to the ' + weak_side + ' side early to escape pressure.' if weak_side else 'CBs must be decisive on the ball.'}"
            if press == "high"
            else
            f"Patient build — use the width. "
            f"{'Switch to the ' + weak_side + ' side to exploit their slow fullback.' if weak_side else 'Find the deep playmaker to progress.'}"
        ),
    ).to_dict()


def build(
    xi: list[dict],
    formation: str,
    linkup_pairs: list[dict],
    opposition: dict,
    defensive_shape: dict,
    matchup_exploits: list[str] = [],
) -> list[dict]:
    slots      = get_slots(formation)
    opp_slots  = mirror_slots(get_slots(opposition.get("likely_formation") or "4-3-3"))
    press_style = opposition.get("press_style") or "medium"
    opp_attrs   = opposition.get("attributes") or {}
    block       = (defensive_shape or {}).get("block") or "mid"
    is_high     = press_style == "high"
    cb_push     = {"high": 12, "mid": 6, "low": 2, "deep": 0}.get(block, 6)

    gk              = xi[0] if xi else None
    ball_playing_cb = find_player(xi, "Ball Playing Defender", "Progressive Passer")
    deep_playmaker  = find_player(xi, "Deep Playmaker", "Sits Between Lines")
    sweeper_gk      = has_trait(gk or {}, "Sweeper Keeper", "Calm On Ball")
    outlet_a, outlet_b = get_linkup_players(xi, linkup_pairs, "outlet_from_back")
    opp_cdm_weak    = any(
        "weak" in str(v).lower() or "slow" in str(v).lower()
        for k, v in opp_attrs.items() if "cdm" in k.lower() or "midfield" in k.lower()
    )

    frames: list[SimFrame] = []

    # ── Frame 1 ───────────────────────────────────────────────────────────────
    gk_slot  = slots[0] if slots else {"x": 14, "y": 65}
    players1 = []

    if gk:
        players1.append(PlayerDelta(
            name=gk.get("name", "GK"),
            dx=6.0 if sweeper_gk else 0.0, dy=0,
            slot_key=get_slot_key(xi, slots, gk.get("name", "")),
            player_id=gk.get("player_id"),
            is_ball_carrier=True,
            trait_label="Plays out from back" if sweeper_gk else None,
        ))

    for idx in range(1, min(5, len(xi))):
        cb = xi[idx]
        is_bpd   = has_trait(cb, "Ball Playing Defender", "Progressive Passer")
        dy_spread = [-10, -5, 5, 10][idx - 1]
        players1.append(PlayerDelta(
            name=cb.get("name", f"CB{idx}"),
            dx=float(cb_push), dy=float(dy_spread),
            slot_key=get_slot_key(xi, slots, cb.get("name", "")),
            player_id=cb.get("player_id"),
            trait_label="Builds from back" if is_bpd else None,
        ))

    if deep_playmaker:
        dm_idx  = player_slot_index(xi, deep_playmaker.get("name", ""))
        dm_slot = slots[dm_idx] if dm_idx < len(slots) else {"x": 92, "y": 65}
        players1.append(PlayerDelta(
            name=deep_playmaker.get("name", "CDM"),
            dx=-14.0, dy=mirror_dy(dm_slot["y"], 0),
            slot_key=get_slot_key(xi, slots, deep_playmaker.get("name", "")),
            player_id=deep_playmaker.get("player_id"),
            trait_label="Drops between CBs",
        ))

    opp1 = []
    for i, s in enumerate(opp_slots):
        sk = s.get("slot_key", s["role"])
        if s["role"] == "FWD":
            opp1.append(OppDelta(slot_index=i, dx=-22.0 if is_high else -8.0, dy=0,
                                  slot_key=sk, reaction="pressing" if is_high else "hold"))
        elif s["role"] == "MID" and is_high:
            opp1.append(OppDelta(slot_index=i, dx=-10.0, dy=0, slot_key=sk, reaction="pressing"))

    frames.append(SimFrame(
        frame=1, duration_ms=900,
        ball=BallState(x=float(gk_slot["x"]), y=float(gk_slot["y"])),
        ball_carrier=gk.get("name") if gk else None,
        action="GK plays short — CBs split to create passing angles",
        players=players1, opp_players=opp1,
        note="Under pressure — be quick" if is_high else "Building from the back",
        ball_intent=BallIntent(type="pass", from_slot="GK", to_slot="RCB", lane="short_pass"),
        callouts=[
            Callout(type="zone", zone="defensive_third",
                    text="Press incoming" if is_high else "Space to build",
                    severity="danger" if is_high else "neutral"),
        ],
    ))

    # ── Frame 2 ───────────────────────────────────────────────────────────────
    target_cb     = ball_playing_cb or (xi[1] if len(xi) > 1 else None)
    tc_idx        = player_slot_index(xi, target_cb.get("name", "")) if target_cb else 1
    tc_slot       = slots[tc_idx] if tc_idx < len(slots) else {"x": 52, "y": 20}

    players2 = []
    if target_cb:
        players2.append(PlayerDelta(
            name=target_cb.get("name", "CB"),
            dx=0, dy=0,
            slot_key=get_slot_key(xi, slots, target_cb.get("name", "")),
            player_id=target_cb.get("player_id"),
            is_ball_target=True,
            trait_label="Receives — Ball Playing CB" if has_trait(target_cb, "Ball Playing Defender") else None,
        ))

    if deep_playmaker:
        players2.append(PlayerDelta(
            name=deep_playmaker.get("name", "CDM"),
            dx=-2.0, dy=0,
            slot_key=get_slot_key(xi, slots, deep_playmaker.get("name", "")),
            player_id=deep_playmaker.get("player_id"),
            trait_label="Short option",
        ))

    for i in range(1, min(5, len(xi))):
        fb = xi[i]
        if fb == target_cb:
            continue
        fb_dx = 8.0 if has_trait(fb, "Overlapping Full-Back", "Offensive Full-Back") else 4.0
        players2.append(PlayerDelta(
            name=fb.get("name", "FB"), dx=fb_dx, dy=0,
            slot_key=get_slot_key(xi, slots, fb.get("name", "")),
            player_id=fb.get("player_id"),
            trait_label="Pushes forward" if has_trait(fb, "Overlapping Full-Back", "Offensive Full-Back") else None,
        ))

    opp2 = []
    if is_high:
        for i, s in enumerate(opp_slots):
            sk = s.get("slot_key", "FWD")
            if s["role"] == "FWD":
                dx = (tc_slot["x"] - s["x"]) * 0.6
                dy = (tc_slot["y"] - s["y"]) * 0.6
                opp2.append(OppDelta(slot_index=i, dx=dx, dy=dy, slot_key=sk, reaction="pressing"))
                break

    frames.append(SimFrame(
        frame=2, duration_ms=800,
        ball=BallState(x=clamp_x(float(tc_slot["x"] + cb_push)), y=float(tc_slot["y"])),
        ball_carrier=target_cb.get("name") if target_cb else None,
        action=f"Ball to {target_cb.get('name','CB').split()[0]} — carries forward",
        players=players2, opp_players=opp2,
        note="Ball playing CB receives — midfield must offer angles",
        ball_intent=BallIntent(type="carry", from_slot=get_slot_key(xi, slots, target_cb.get("name","")) or "CB"),
        callouts=[
            Callout(type="player", target=target_cb.get("name", "CB"),
                    text="On the ball — look for switch",
                    severity="opportunity"),
        ] if not is_high else [
            Callout(type="player",
                    target=next((s.get("slot_key","FWD") for s in opp_slots if s["role"]=="FWD"), "Opp FWD"),
                    text="Pressing hard — be quick",
                    severity="danger"),
        ],
    ))

    # ── Frame 3 ───────────────────────────────────────────────────────────────
    players3 = []
    opp3     = []

    if opp_cdm_weak and deep_playmaker:
        dm_idx  = player_slot_index(xi, deep_playmaker.get("name", ""))
        dm_slot = slots[dm_idx] if dm_idx < len(slots) else {"x": 90, "y": 65}
        players3.append(PlayerDelta(
            name=deep_playmaker.get("name", "CDM"),
            dx=10.0, dy=0,
            slot_key=get_slot_key(xi, slots, deep_playmaker.get("name", "")),
            player_id=deep_playmaker.get("player_id"),
            is_ball_target=True,
            trait_label="Exploits CDM gap",
        ))
        for i, p in enumerate(xi):
            role = (p.get("slot_broad") or p.get("broad_position") or "")
            if role == "MID" and p.get("name") != deep_playmaker.get("name") and i < len(slots):
                players3.append(PlayerDelta(
                    name=p.get("name", "MID"), dx=12.0, dy=0,
                    slot_key=get_slot_key(xi, slots, p.get("name", "")),
                    player_id=p.get("player_id"),
                ))
        ball_x = clamp_x(float(dm_slot["x"] + 10))
        ball_y = clamp_y(float(dm_slot["y"]))
        action = f"Through {deep_playmaker.get('name','CDM').split()[0]} — CDM gap exploited"
        intent = BallIntent(type="through_ball", from_slot=get_slot_key(xi,slots,target_cb.get("name","")) or "CB",
                            to_slot="CDM", lane="through_ball")
        callouts3 = [
            Callout(type="zone", zone="central_channel",
                    text="Opp CDM dragged — space central", severity="opportunity"),
            Callout(type="player",
                    target=next((s.get("slot_key","CDM") for s in opp_slots if s["role"]=="MID"), "Opp CDM"),
                    text="Dragged out", severity="opportunity"),
        ]
    else:
        far_fb = None; far_fb_slot = None
        for i, p in enumerate(xi[1:5], start=1):
            if i < len(slots):
                s = slots[i]
                if far_fb is None or abs(s["y"] - tc_slot["y"]) > abs((far_fb_slot or {"y":0})["y"] - tc_slot["y"]):
                    far_fb = p; far_fb_slot = s
        if far_fb and far_fb_slot:
            players3.append(PlayerDelta(
                name=far_fb.get("name","FB"), dx=10.0, dy=0,
                slot_key=get_slot_key(xi, slots, far_fb.get("name","")),
                player_id=far_fb.get("player_id"),
                is_ball_target=True,
                trait_label="Receives switch" if has_trait(far_fb, "Overlapping Full-Back") else None,
            ))
            ball_x = clamp_x(float(far_fb_slot["x"] + 10))
            ball_y = clamp_y(float(far_fb_slot["y"]))
            action = f"Switch to {far_fb.get('name','FB').split()[0]} — opens up weak side"
            far_side = "left" if far_fb_slot["y"] > PH / 2 else "right"
            intent = BallIntent(type="switch", from_slot=get_slot_key(xi,slots,target_cb.get("name","")) or "CB",
                                to_slot=far_fb_slot.get("slot_key","FB"), lane="cross_field")
            callouts3 = [
                Callout(type="zone",
                        zone="left_channel" if far_side == "left" else "right_channel",
                        text="Switch opens space", severity="opportunity"),
            ]
            for i, s in enumerate(opp_slots):
                if s["role"] == "MID":
                    opp3.append(OppDelta(slot_index=i, dx=0, dy=(ball_y - s["y"]) * 0.3,
                                         slot_key=s.get("slot_key","MID"), reaction="tracking"))
        else:
            ball_x = clamp_x(float(tc_slot["x"] + 25)); ball_y = float(tc_slot["y"])
            action = "Carries forward into midfield"
            intent = BallIntent(type="carry")
            callouts3 = []

    for i, p in enumerate(xi):
        role = p.get("slot_broad") or p.get("broad_position") or ""
        if role == "FWD" and i < len(slots):
            fvd_slot = slots[i]
            run_dx = 15.0 if has_trait(p, "Runs In Behind", "Counterattacking Runner") else 8.0
            run_dy = mirror_dy(fvd_slot["y"], -8.0 if i % 2 == 0 else 8.0)
            players3.append(PlayerDelta(
                name=p.get("name","FWD"), dx=run_dx, dy=run_dy,
                slot_key=get_slot_key(xi, slots, p.get("name","")),
                player_id=p.get("player_id"),
                trait_label="Makes run" if has_trait(p, "Runs In Behind") else None,
            ))

    frames.append(SimFrame(
        frame=3, duration_ms=900,
        ball=BallState(x=ball_x, y=ball_y),
        ball_carrier=None, action=action,
        players=players3, opp_players=opp3,
        note="Switch of play — exploit weak side" if not opp_cdm_weak else "Central overload",
        ball_intent=intent, callouts=callouts3,
    ))

    # ── Frame 4 ───────────────────────────────────────────────────────────────
    players4 = []; opp4 = []
    if outlet_a and outlet_b:
        pa_idx  = player_slot_index(xi, outlet_a.get("name",""))
        pb_idx  = player_slot_index(xi, outlet_b.get("name",""))
        pb_slot = slots[pb_idx] if pb_idx < len(slots) else {"x":110,"y":65}
        players4.append(PlayerDelta(
            name=outlet_a.get("name",""), dx=8.0, dy=0,
            slot_key=get_slot_key(xi,slots,outlet_a.get("name","")),
            player_id=outlet_a.get("player_id"), is_ball_carrier=True,
            trait_label="Outlet from back",
        ))
        players4.append(PlayerDelta(
            name=outlet_b.get("name",""), dx=6.0, dy=0,
            slot_key=get_slot_key(xi,slots,outlet_b.get("name","")),
            player_id=outlet_b.get("player_id"), is_ball_target=True,
        ))
        ball_x = clamp_x(float(pb_slot["x"] + 6)); ball_y = clamp_y(float(pb_slot["y"]))
        action4 = f"{outlet_a.get('name','').split()[0]} finds {outlet_b.get('name','').split()[0]}"
        intent4 = BallIntent(type="pass",
                             from_slot=get_slot_key(xi,slots,outlet_a.get("name","")) or "CB",
                             to_slot=get_slot_key(xi,slots,outlet_b.get("name","")) or "CDM",
                             lane="short_pass")
    else:
        ball_x = clamp_x(ball_x + 20); ball_y = clamp_y(ball_y)
        action4 = "Midfield advance — final pass incoming"
        intent4 = BallIntent(type="carry")

    for i, p in enumerate(xi):
        role = p.get("slot_broad") or p.get("broad_position") or ""
        if role == "FWD" and i < len(slots):
            fwd_slot = slots[i]
            if has_trait(p, "Target Man", "Holds Up Play"):
                players4.append(PlayerDelta(
                    name=p.get("name","ST"), dx=2.0, dy=0,
                    slot_key=get_slot_key(xi,slots,p.get("name","")),
                    player_id=p.get("player_id"), trait_label="Holds up play",
                ))
            elif has_trait(p, "Runs In Behind"):
                players4.append(PlayerDelta(
                    name=p.get("name","ST"), dx=20.0,
                    dy=mirror_dy(fwd_slot["y"], -10.0),
                    slot_key=get_slot_key(xi,slots,p.get("name","")),
                    player_id=p.get("player_id"), trait_label="Run in behind",
                ))

    for i, s in enumerate(opp_slots):
        if s["role"] == "DEF":
            opp4.append(OppDelta(slot_index=i, dx=0, dy=0,
                                  slot_key=s.get("slot_key","DEF"), reaction="hold"))

    frames.append(SimFrame(
        frame=4, duration_ms=850,
        ball=BallState(x=ball_x, y=ball_y),
        ball_carrier=outlet_b.get("name") if outlet_b else None,
        action=action4,
        players=players4, opp_players=opp4,
        note="In the final third — create and finish",
        ball_intent=intent4,
        callouts=[
            Callout(type="zone", zone="attacking_third",
                    text="Final ball needed", severity="opportunity"),
        ],
    ))

    return [f.to_dict() for f in frames]