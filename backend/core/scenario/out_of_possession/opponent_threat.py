# core/scenario/out_of_possession/opponent_threat.py
#
# Simulates opposition attacking threats and your team's defensive reaction.
#
# Depends on:
#   opposition.playing_style    — direct / possession / counter / physical
#   opposition.set_piece_threat — high / medium / low
#   opposition.attributes       — fast winger, aerial threat, skilful player etc
#   matchup_vulnerabilities     — slow FB vs fast winger, weak CB vs aerial etc
#   matchup_general_notes       — set piece danger note
#   xi traits                   — Strong In Air, Tight Marker, Defensive Full-Back,
#                                   Sweeper CB, Tracks Runners, Aggressive Tackler

from core.scenario.types import SimFrame, BallState, PlayerDelta, OppDelta
from core.scenario.helpers import (
    get_slots, mirror_slots, has_trait, find_player,
    find_player_by_position, player_slot_index,
    mirror_dy, clamp_x, clamp_y, PH, PW,
)


def metadata(opposition: dict, matchup_vulnerabilities: list[str]) -> dict:
    from core.scenario.types import ScenarioMeta
    style     = (opposition.get("playing_style") or "direct").lower()
    set_piece = (opposition.get("set_piece_threat") or "low").lower()
    opp_attrs = opposition.get("attributes") or {}
 
    fast_w  = any("fast" in str(v).lower() or "pace" in str(v).lower() for v in opp_attrs.values())
    aerial  = any("aerial" in str(v).lower() for v in opp_attrs.values())
    exposed = len(matchup_vulnerabilities) > 0
 
    if set_piece == "high":
        title    = "Set piece danger"
        purpose  = "Defend the corner and deal with aerial threat in box"
        takeaway = "Assign markers early — GK commands the cross. Clear with conviction, no second ball."
    elif fast_w:
        title    = "Pace threat on the flank"
        purpose  = "Track the fast winger and prevent isolation of the fullback"
        takeaway = f"{'⚠ Fullback is exposed — cover CB must step across.' if exposed else 'Force inside — do not let them reach the byline.'}"
    elif aerial or "direct" in style:
        title    = "Direct aerial threat"
        purpose  = "Win the first ball and clear the second"
        takeaway = "Hold the line — don't jump early. CBs must win headers, midfield attacks second ball."
    elif "counter" in style:
        title    = "Counter-attack threat"
        purpose  = "Track runners and maintain numbers behind the ball"
        takeaway = "Don't commit — stay compact. One turnover and they're in behind."
    else:
        title    = "Possession under pressure"
        purpose  = "Stay compact and force the turnover"
        takeaway = f"{'⚠ Our passing under press is a risk — CDM must stay simple.' if exposed else 'Hold shape — patience wins the ball.'}"
 
    return ScenarioMeta(
        scenario="opponent_threat",
        title=title,
        phase="Out of possession",
        purpose=purpose,
        takeaway=takeaway,
    ).to_dict()


def build(
    xi: list[dict],
    formation: str,
    defensive_formation: str,
    defensive_shape: dict,
    opposition: dict,
    matchup_vulnerabilities: list[str],
    matchup_general_notes: list[str],
) -> list[dict]:
    ds           = defensive_shape or {}
    block        = ds.get("block") or "mid"
    def_form     = defensive_formation or formation
    slots        = get_slots(def_form)
    opp_form     = opposition.get("likely_formation") or "4-3-3"
    opp_slots    = mirror_slots(get_slots(opp_form))
    playing_style = (opposition.get("playing_style") or "direct").lower()
    set_piece     = (opposition.get("set_piece_threat") or "low").lower()
    opp_attrs     = opposition.get("attributes") or {}

    # Parse threat types from opposition attributes
    fast_winger     = any("fast" in str(v).lower() or "pace" in str(v).lower() or "quick" in str(v).lower()
                         for k, v in opp_attrs.items() if "wing" in k.lower() or "forward" in k.lower())
    aerial_threat   = any("aerial" in str(v).lower() or "strong in air" in str(v).lower() or "header" in str(v).lower()
                         for k, v in opp_attrs.items()) or "aerial" in playing_style
    skilful_winger  = any("skilful" in str(v).lower() or "technical" in str(v).lower() or "dribble" in str(v).lower()
                         for k, v in opp_attrs.items())
    direct_threat   = "direct" in playing_style or "long ball" in playing_style
    counter_threat  = "counter" in playing_style

    # Parse which side the threat comes from
    threat_left = any(
        "left" in k.lower() and ("fast" in str(v).lower() or "pace" in str(v).lower() or "skilful" in str(v).lower())
        for k, v in opp_attrs.items()
    )
    threat_right = any(
        "right" in k.lower() and ("fast" in str(v).lower() or "pace" in str(v).lower() or "skilful" in str(v).lower())
        for k, v in opp_attrs.items()
    )

    # Check vulnerabilities
    slow_fb_exposed = any("pace" in v.lower() and ("fullback" in v.lower() or "fb" in v.lower() or "back" in v.lower())
                         for v in matchup_vulnerabilities)
    aerial_exposed  = any("aerial" in v.lower() or "heading" in v.lower()
                         for v in matchup_vulnerabilities)
    press_exposed   = any("press" in v.lower() and "passing" in v.lower()
                         for v in matchup_vulnerabilities)

    # Route to the right threat scenario
    if set_piece == "high":
        return _set_piece_threat(xi, slots, opp_slots, opp_attrs)
    elif fast_winger or threat_left or threat_right:
        flank = "left" if threat_left else "right" if threat_right else "left"
        return _fast_winger_threat(xi, slots, opp_slots, flank, slow_fb_exposed)
    elif aerial_threat or direct_threat:
        return _aerial_direct_threat(xi, slots, opp_slots, aerial_exposed)
    elif counter_threat:
        return _counter_threat(xi, slots, opp_slots)
    else:
        return _possession_threat(xi, slots, opp_slots, press_exposed)


# ── Fast winger threat ────────────────────────────────────────────────────────

def _fast_winger_threat(
    xi: list[dict],
    slots: list[dict],
    opp_slots: list[dict],
    threat_flank: str,
    slow_fb_exposed: bool,
) -> list[dict]:
    frames: list[SimFrame] = []

    # Your FB on the exposed flank
    # Top half = right FB (slot index 1), bottom half = left FB (slot index 4)
    at_risk_fb_idx = 1 if threat_flank == "right" else 4
    at_risk_fb = xi[at_risk_fb_idx] if at_risk_fb_idx < len(xi) else None
    at_risk_fb_slot = slots[at_risk_fb_idx] if at_risk_fb_idx < len(slots) else {"x": 52, "y": 20}

    # Your cover — sweeper CB or nearest CB
    cover_cb = find_player(xi, "Sweeper CB", "Covers Ground", "Tracks Runners")
    cover_idx = player_slot_index(xi, cover_cb.get("name", "")) if cover_cb else 2
    cover_slot = slots[cover_idx] if cover_idx < len(slots) else {"x": 52, "y": 45}

    # Find opp fast winger slot — will be on the relevant flank
    opp_winger_idx = None
    for i, s in enumerate(opp_slots):
        if s["role"] == "FWD":
            if threat_flank == "right" and s["y"] < PH / 2:
                opp_winger_idx = i; break
            elif threat_flank == "left" and s["y"] > PH / 2:
                opp_winger_idx = i; break
    if opp_winger_idx is None:
        opp_winger_idx = next((i for i, s in enumerate(opp_slots) if s["role"] == "FWD"), 8)

    opp_winger_slot = opp_slots[opp_winger_idx]

    # ── Frame 1: Winger receives ball wide — your FB tracks ──────────────────
    frame1_players = []
    frame1_opp = []

    if at_risk_fb:
        fb_dx = 10.0
        fb_label = None
        if slow_fb_exposed:
            fb_dx = 6.0   # slower to react
            fb_label = "⚠ Exposed — slow to track"
        elif has_trait(at_risk_fb, "Tight Marker", "Tracks Runners"):
            fb_dx = 14.0
            fb_label = "Tight marking"
        elif has_trait(at_risk_fb, "Defensive Full-Back", "Stays Back"):
            fb_dx = 12.0
            fb_label = "Holds defensive shape"

        frame1_players.append(PlayerDelta(
            name=at_risk_fb.get("name", "FB"),
            dx=fb_dx, dy=mirror_dy(at_risk_fb_slot["y"], -8.0),
            trait_label=fb_label,
        ))

    # Cover CB shifts across to provide cover
    if cover_cb:
        frame1_players.append(PlayerDelta(
            name=cover_cb.get("name", "CB"),
            dx=8.0, dy=mirror_dy(cover_slot["y"], -10.0),
            trait_label="Cover — sweeps wide" if has_trait(cover_cb, "Sweeper CB") else "Covers the channel",
        ))

    # Opp winger drives at the FB
    frame1_opp.append(OppDelta(
        slot_index=opp_winger_idx,
        dx=-25.0, dy=mirror_dy(opp_winger_slot["y"], 5.0),
        reaction="pressing",
    ))

    # Rest of opp midfield supports
    for i, s in enumerate(opp_slots):
        if s["role"] == "MID":
            frame1_opp.append(OppDelta(slot_index=i, dx=-10.0, dy=0, reaction="supporting"))

    ball_x = clamp_x(opp_winger_slot["x"] - 25)
    ball_y = clamp_y(opp_winger_slot["y"])

    frames.append(SimFrame(
        frame=1, duration_ms=850,
        ball=BallState(x=ball_x, y=ball_y),
        ball_carrier=None,
        action=f"Fast winger drives at your {'right' if threat_flank == 'right' else 'left'} back",
        players=frame1_players, opp_players=frame1_opp,
        note="⚠ Exposed — slow FB vs pace" if slow_fb_exposed else "Winger threat — FB must hold shape",
    ))

    # ── Frame 2: 1v1 situation — your response ───────────────────────────────
    frame2_players = []
    frame2_opp = []

    if at_risk_fb:
        if slow_fb_exposed:
            # Can't keep up — cover CB must step in
            frame2_players.append(PlayerDelta(
                name=at_risk_fb.get("name", "FB"),
                dx=0, dy=0,
                trait_label="⚠ Beaten for pace",
            ))
            if cover_cb:
                frame2_players.append(PlayerDelta(
                    name=cover_cb.get("name", "CB"),
                    dx=15.0, dy=mirror_dy(cover_slot["y"], -15.0),
                    trait_label="Sweeper steps in — critical cover",
                ))
        else:
            frame2_players.append(PlayerDelta(
                name=at_risk_fb.get("name", "FB"),
                dx=14.0, dy=mirror_dy(at_risk_fb_slot["y"], -10.0),
                trait_label="Jockeys — forces inside",
            ))

    # MID tracks back to help
    for i, p in enumerate(xi):
        role = (slots[i]["role"] if i < len(slots) else "")
        if role == "MID" and has_trait(p, "Tracks Back Defensively", "Covers Ground"):
            frame2_players.append(PlayerDelta(
                name=p.get("name", "MID"),
                dx=10.0, dy=mirror_dy(slots[i]["y"], -8.0),
                trait_label="Tracks back",
            ))
            break

    frame2_opp.append(OppDelta(
        slot_index=opp_winger_idx,
        dx=-15.0, dy=mirror_dy(opp_winger_slot["y"], 8.0),
        reaction="dribbling",
    ))

    frames.append(SimFrame(
        frame=2, duration_ms=800,
        ball=BallState(x=clamp_x(ball_x - 15), y=clamp_y(ball_y)),
        ball_carrier=None,
        action="1v1 on the flank — hold shape, force inside",
        players=frame2_players, opp_players=frame2_opp,
        note="Force the cross — don't let them cut inside" if not slow_fb_exposed else "⚠ Cover needed — FB exposed",
    ))

    return [f.to_dict() for f in frames]


# ── Aerial / direct threat ────────────────────────────────────────────────────

def _aerial_direct_threat(
    xi: list[dict],
    slots: list[dict],
    opp_slots: list[dict],
    aerial_exposed: bool,
) -> list[dict]:
    frames: list[SimFrame] = []

    # Your best aerial defenders
    aerial_cb1 = find_player(xi, "Strong In Air", "Wins Headers")
    aerial_cb2 = None
    for p in xi:
        if p != aerial_cb1 and has_trait(p, "Strong In Air", "Aggressive Tackler"):
            aerial_cb2 = p; break

    organiser = find_player(xi, "Organises Defence")

    # Opp striker — biggest aerial threat
    opp_st_idx = next((i for i, s in enumerate(opp_slots) if s["role"] == "FWD"), 10)
    opp_st_slot = opp_slots[opp_st_idx] if opp_st_idx < len(opp_slots) else {"x": PW - 50, "y": 65}

    # ── Frame 1: Long ball pumped forward — CBs hold position ────────────────
    frame1_players = []
    frame1_opp = []

    for i, p in enumerate(xi):
        if i >= len(slots):
            continue
        role = slots[i]["role"]
        pname = p.get("name", "")
        p_slot = slots[i]

        if role == "DEF":
            if has_trait(p, "Strong In Air", "Wins Headers"):
                frame1_players.append(PlayerDelta(
                    name=pname, dx=5.0, dy=0,
                    trait_label="Wins header — aerial dominance",
                ))
            elif has_trait(p, "Sweeper CB"):
                frame1_players.append(PlayerDelta(
                    name=pname, dx=0, dy=0,
                    trait_label="Sweeper — covers second ball",
                ))
            else:
                frame1_players.append(PlayerDelta(name=pname, dx=0, dy=0))

        elif role == "MID":
            # Midfield screens — positions for second ball
            frame1_players.append(PlayerDelta(
                name=pname, dx=-2.0, dy=mirror_dy(p_slot["y"], 5.0),
                trait_label="Second ball" if has_trait(p, "Box To Box", "Ball Winner") else None,
            ))

        elif role == "GK":
            frame1_players.append(PlayerDelta(
                name=pname, dx=8.0, dy=0,
                trait_label="Claims it" if has_trait(p, "Command Of Area") else None,
            ))

    # Opp — long ball pumped forward
    for i, s in enumerate(opp_slots):
        if s["role"] == "FWD":
            frame1_opp.append(OppDelta(slot_index=i, dx=-15.0, dy=0, reaction="attacking"))
        elif s["role"] == "MID":
            frame1_opp.append(OppDelta(slot_index=i, dx=-10.0, dy=0, reaction="supporting"))

    frames.append(SimFrame(
        frame=1, duration_ms=900,
        ball=BallState(x=clamp_x(opp_st_slot["x"] - 10), y=float(PH / 2)),
        ball_carrier=None,
        action="Long ball pumped forward — aerial duel",
        players=frame1_players, opp_players=frame1_opp,
        note="⚠ Aerial weakness — CBs must win first ball" if aerial_exposed else "Aerial battle — hold the line",
    ))

    # ── Frame 2: Header won — clear or second ball ────────────────────────────
    frame2_players = []

    if aerial_cb1:
        frame2_players.append(PlayerDelta(
            name=aerial_cb1.get("name", "CB"),
            dx=0, dy=0,
            trait_label="Wins the header — clears",
        ))

    if organiser:
        frame2_players.append(PlayerDelta(
            name=organiser.get("name", "CB"),
            dx=0, dy=0,
            trait_label="Organises — holds line",
        ))

    # MIDs win second ball
    for i, p in enumerate(xi):
        role = (slots[i]["role"] if i < len(slots) else "")
        if role == "MID" and has_trait(p, "Ball Winner", "Box To Box", "Aggressive Tackler"):
            frame2_players.append(PlayerDelta(
                name=p.get("name", "MID"),
                dx=3.0, dy=0,
                trait_label="Second ball — wins it",
            ))
            break

    frames.append(SimFrame(
        frame=2, duration_ms=750,
        ball=BallState(x=clamp_x(100.0), y=float(PH / 2)),
        ball_carrier=None,
        action="Header cleared — second ball battle",
        players=frame2_players, opp_players=[],
        note="Win the second ball — keep pressure off defence",
    ))

    return [f.to_dict() for f in frames]


# ── Set piece threat ──────────────────────────────────────────────────────────

def _set_piece_threat(
    xi: list[dict],
    slots: list[dict],
    opp_slots: list[dict],
    opp_attrs: dict,
) -> list[dict]:
    frames: list[SimFrame] = []

    # Assign marking duties based on traits
    aerial_defenders = [p for p in xi if has_trait(p, "Strong In Air", "Wins Headers", "Aggressive Tackler")]
    organiser = find_player(xi, "Organises Defence")
    gk = xi[0] if xi else None

    # Opp aerial threats — corner delivery
    opp_aerial_threats = []
    for i, s in enumerate(opp_slots):
        if s["role"] in ["DEF", "FWD"]:
            opp_aerial_threats.append(i)

    # ── Frame 1: Corner — defensive setup ─────────────────────────────────────
    frame1_players = []
    frame1_opp = []

    # GK claims the cross
    if gk:
        frame1_players.append(PlayerDelta(
            name=gk.get("name", "GK"),
            dx=10.0, dy=0,
            trait_label="Commands area — calls for it" if has_trait(gk, "Command Of Area") else "Positioning for cross",
        ))

    # Aerial defenders mark zone or man
    corner_positions = [
        {"x": 22, "y": 40},   # near post
        {"x": 22, "y": 65},   # centre box
        {"x": 22, "y": 90},   # far post
    ]
    for j, defender in enumerate(aerial_defenders[:3]):
        target = corner_positions[j]
        def_idx = player_slot_index(xi, defender.get("name", ""))
        def_slot = slots[def_idx] if def_idx < len(slots) else {"x": 52, "y": 65}
        frame1_players.append(PlayerDelta(
            name=defender.get("name", "CB"),
            dx=clamp_x(target["x"]) - def_slot["x"],
            dy=target["y"] - def_slot["y"],
            trait_label="Man marking" if has_trait(defender, "Tight Marker") else "Zonal — attacks ball",
        ))

    # Organiser sets the shape
    if organiser:
        org_idx  = player_slot_index(xi, organiser.get("name", ""))
        org_slot = slots[org_idx] if org_idx < len(slots) else {"x": 52, "y": 65}
        frame1_players.append(PlayerDelta(
            name=organiser.get("name", "CB"),
            dx=5.0, dy=0,
            trait_label="Sets the wall — organises",
        ))

    # Remaining players on post or edge of box
    for i, p in enumerate(xi):
        pname = p.get("name", "")
        already = [pd.name for pd in frame1_players]
        if pname in already or i >= len(slots):
            continue
        p_slot = slots[i]
        role = p_slot["role"]
        if role in ["MID", "FWD"]:
            # Edge of box — prevent second ball / counter
            frame1_players.append(PlayerDelta(
                name=pname, dx=clamp_x(30.0) - p_slot["x"], dy=0,
            ))

    # Opp deliver — aerial threats move to box
    for i in opp_aerial_threats[:4]:
        opp_slot = opp_slots[i]
        frame1_opp.append(OppDelta(
            slot_index=i,
            dx=-(opp_slot["x"] - 22),
            dy=mirror_dy(opp_slot["y"], -10.0),
            reaction="attacking",
        ))
    # Remaining opp on edge of box / counter positions
    for i, s in enumerate(opp_slots):
        if i not in opp_aerial_threats[:4] and s["role"] == "MID":
            frame1_opp.append(OppDelta(slot_index=i, dx=-20.0, dy=0, reaction="supporting"))

    frames.append(SimFrame(
        frame=1, duration_ms=1000,
        ball=BallState(x=4.0, y=4.0),   # corner flag position
        ball_carrier=None,
        action="Corner — defensive setup: mark the runners, attack the ball",
        players=frame1_players, opp_players=frame1_opp,
        note="⚠ High set piece threat — clear assignments essential",
    ))

    # ── Frame 2: Ball delivered — contest in the box ──────────────────────────
    frame2_players = []
    frame2_opp = []

    if gk:
        frame2_players.append(PlayerDelta(
            name=gk.get("name", "GK"),
            dx=3.0, dy=0,
            is_ball_carrier=True,
            trait_label="Claims it — punch or catch",
        ))

    for defender in aerial_defenders[:2]:
        frame2_players.append(PlayerDelta(
            name=defender.get("name", "CB"),
            dx=0, dy=0,
            trait_label="Wins header — clears",
        ))

    for i in opp_aerial_threats[:3]:
        frame2_opp.append(OppDelta(slot_index=i, dx=0, dy=0, reaction="attacking"))

    frames.append(SimFrame(
        frame=2, duration_ms=800,
        ball=BallState(x=22.0, y=float(PH / 2)),
        ball_carrier=gk.get("name") if gk else None,
        action="Ball into the box — aerial contest",
        players=frame2_players, opp_players=frame2_opp,
        note="Win the first ball — clear with conviction",
    ))

    return [f.to_dict() for f in frames]


# ── Counter threat ────────────────────────────────────────────────────────────

def _counter_threat(
    xi: list[dict],
    slots: list[dict],
    opp_slots: list[dict],
) -> list[dict]:
    frames: list[SimFrame] = []

    # Find our players who track back
    trackers = [p for p in xi if has_trait(p, "Tracks Back Defensively", "Stays Back", "Defensive Full-Back")]
    cdm = find_player(xi, "Deep Playmaker", "Ball Winner", "Sits Between Lines")

    # Opp countering players
    opp_runners = [(i, s) for i, s in enumerate(opp_slots) if s["role"] == "FWD"]

    # ── Frame 1: Opp wins ball high — countering ──────────────────────────────
    frame1_players = []
    frame1_opp = []

    for p in trackers[:3]:
        p_idx  = player_slot_index(xi, p.get("name", ""))
        p_slot = slots[p_idx] if p_idx < len(slots) else {"x": 100, "y": 65}
        frame1_players.append(PlayerDelta(
            name=p.get("name", ""),
            dx=-20.0, dy=0,
            trait_label="Tracks back — blocks the run",
        ))

    if cdm:
        cdm_idx  = player_slot_index(xi, cdm.get("name", ""))
        cdm_slot = slots[cdm_idx] if cdm_idx < len(slots) else {"x": 92, "y": 65}
        frame1_players.append(PlayerDelta(
            name=cdm.get("name", "CDM"),
            dx=-5.0, dy=0,
            trait_label="Holds midfield — blocks passing lane",
        ))

    # Cover defenders drop in
    for i, p in enumerate(xi):
        role = (slots[i]["role"] if i < len(slots) else "")
        if role == "DEF" and i < len(slots):
            frame1_players.append(PlayerDelta(
                name=p.get("name", "DEF"),
                dx=-5.0, dy=0,
            ))

    # Opp runners burst
    for i, s in enumerate(opp_runners[:2]):
        idx, slot = s
        frame1_opp.append(OppDelta(
            slot_index=idx,
            dx=-30.0, dy=mirror_dy(slot["y"], -5.0),
            reaction="counter",
        ))

    frames.append(SimFrame(
        frame=1, duration_ms=800,
        ball=BallState(x=clamp_x(PW - 50), y=float(PH / 2)),
        ball_carrier=None,
        action="Opp counter — runners in behind — track and cover",
        players=frame1_players, opp_players=frame1_opp,
        note="⚠ Counter threat — numbers behind ball critical",
    ))

    # ── Frame 2: Shape recovered — opp option closed ──────────────────────────
    frame2_players = []

    for p in trackers[:2]:
        frame2_players.append(PlayerDelta(
            name=p.get("name", ""), dx=0, dy=0,
            trait_label="Position recovered",
        ))
    if cdm:
        frame2_players.append(PlayerDelta(
            name=cdm.get("name", "CDM"), dx=0, dy=0,
            trait_label="Midfield screened",
        ))

    frames.append(SimFrame(
        frame=2, duration_ms=750,
        ball=BallState(x=clamp_x(PW - 35), y=float(PH / 2)),
        ball_carrier=None,
        action="Shape recovered — counter threat neutralised",
        players=frame2_players, opp_players=[],
        note="Counter stopped — reset defensive shape",
    ))

    return [f.to_dict() for f in frames]


# ── Possession threat ─────────────────────────────────────────────────────────

def _possession_threat(
    xi: list[dict],
    slots: list[dict],
    opp_slots: list[dict],
    press_exposed: bool,
) -> list[dict]:
    frames: list[SimFrame] = []

    cdm = find_player(xi, "Ball Winner", "Deep Playmaker", "Aggressive Tackler")
    organiser = find_player(xi, "Organises Defence")

    # ── Frame 1: Opp build-up — team holds compact shape ─────────────────────
    frame1_players = []
    frame1_opp = []

    for i, p in enumerate(xi):
        if i >= len(slots):
            continue
        role = slots[i]["role"]
        pname = p.get("name", "")
        p_slot = slots[i]

        if role == "MID":
            if press_exposed:
                # Don't press — stay compact
                frame1_players.append(PlayerDelta(
                    name=pname, dx=-3.0, dy=0,
                    trait_label="⚠ Under pressure — stays compact" if has_trait(p, "Deep Playmaker") else None,
                ))
            else:
                frame1_players.append(PlayerDelta(
                    name=pname, dx=2.0, dy=mirror_dy(p_slot["y"], 4.0),
                ))
        elif role == "DEF":
            frame1_players.append(PlayerDelta(name=pname, dx=0, dy=0))
        elif role == "FWD":
            frame1_players.append(PlayerDelta(
                name=pname, dx=-5.0, dy=0,
                trait_label="Press triggers ready" if has_trait(p, "Presses High") else None,
            ))

    # Opp probing with possession
    for i, s in enumerate(opp_slots):
        if s["role"] == "MID":
            frame1_opp.append(OppDelta(slot_index=i, dx=-5.0, dy=mirror_dy(s["y"], 5.0), reaction="probing"))

    frames.append(SimFrame(
        frame=1, duration_ms=1000,
        ball=BallState(x=clamp_x(PW - 60), y=float(PH / 2)),
        ball_carrier=None,
        action="Opp in possession — hold shape, stay compact",
        players=frame1_players, opp_players=frame1_opp,
        note="⚠ Press risk — stay patient, don't dive in" if press_exposed else "Stay organised — wait for the turnover",
    ))

    # ── Frame 2: Interception — win the ball ──────────────────────────────────
    frame2_players = []

    if cdm:
        frame2_players.append(PlayerDelta(
            name=cdm.get("name", "CDM"),
            dx=5.0, dy=0,
            is_ball_carrier=True,
            trait_label="Intercepts — wins it",
        ))

    frames.append(SimFrame(
        frame=2, duration_ms=750,
        ball=BallState(x=clamp_x(PW - 55), y=float(PH / 2)),
        ball_carrier=cdm.get("name") if cdm else None,
        action="Interception — ball won in midfield",
        players=frame2_players, opp_players=[],
        note="Turnover — quick transition opportunity",
    ))

    return [f.to_dict() for f in frames]

