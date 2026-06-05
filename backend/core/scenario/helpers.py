# core/scenario/helpers.py — v2
# Added: slot_key resolution, opp slot_key map, callout helpers

from typing import Optional

PW = 220.0
PH = 130.0

FORMATION_SLOTS: dict[str, list[dict]] = {
    "4-3-3": [
        {"x": 14, "y": 65, "role": "GK",  "slot_key": "GK"},
        {"x": 52, "y": 20, "role": "DEF", "slot_key": "RB"},
        {"x": 52, "y": 45, "role": "DEF", "slot_key": "RCB"},
        {"x": 52, "y": 85, "role": "DEF", "slot_key": "LCB"},
        {"x": 52, "y": 110,"role": "DEF", "slot_key": "LB"},
        {"x": 100,"y": 32, "role": "MID", "slot_key": "RCM"},
        {"x": 100,"y": 65, "role": "MID", "slot_key": "CM"},
        {"x": 100,"y": 98, "role": "MID", "slot_key": "LCM"},
        {"x": 175,"y": 20, "role": "FWD", "slot_key": "RW"},
        {"x": 175,"y": 65, "role": "FWD", "slot_key": "ST"},
        {"x": 175,"y": 110,"role": "FWD", "slot_key": "LW"},
    ],
    "4-4-2": [
        {"x": 14, "y": 65, "role": "GK",  "slot_key": "GK"},
        {"x": 52, "y": 20, "role": "DEF", "slot_key": "RB"},
        {"x": 52, "y": 48, "role": "DEF", "slot_key": "RCB"},
        {"x": 52, "y": 82, "role": "DEF", "slot_key": "LCB"},
        {"x": 52, "y": 110,"role": "DEF", "slot_key": "LB"},
        {"x": 108,"y": 20, "role": "MID", "slot_key": "RM"},
        {"x": 108,"y": 48, "role": "MID", "slot_key": "RCM"},
        {"x": 108,"y": 82, "role": "MID", "slot_key": "LCM"},
        {"x": 108,"y": 110,"role": "MID", "slot_key": "LM"},
        {"x": 178,"y": 42, "role": "FWD", "slot_key": "RST"},
        {"x": 178,"y": 88, "role": "FWD", "slot_key": "LST"},
    ],
    "4-2-3-1": [
        {"x": 14, "y": 65, "role": "GK",  "slot_key": "GK"},
        {"x": 52, "y": 20, "role": "DEF", "slot_key": "RB"},
        {"x": 52, "y": 48, "role": "DEF", "slot_key": "RCB"},
        {"x": 52, "y": 82, "role": "DEF", "slot_key": "LCB"},
        {"x": 52, "y": 110,"role": "DEF", "slot_key": "LB"},
        {"x": 92, "y": 44, "role": "MID", "slot_key": "RDM"},
        {"x": 92, "y": 86, "role": "MID", "slot_key": "LDM"},
        {"x": 138,"y": 20, "role": "MID", "slot_key": "RAM"},
        {"x": 138,"y": 65, "role": "MID", "slot_key": "CAM"},
        {"x": 138,"y": 110,"role": "MID", "slot_key": "LAM"},
        {"x": 190,"y": 65, "role": "FWD", "slot_key": "ST"},
    ],
    "4-4-1-1": [
        {"x": 14, "y": 65, "role": "GK",  "slot_key": "GK"},
        {"x": 52, "y": 20, "role": "DEF", "slot_key": "RB"},
        {"x": 52, "y": 48, "role": "DEF", "slot_key": "RCB"},
        {"x": 52, "y": 82, "role": "DEF", "slot_key": "LCB"},
        {"x": 52, "y": 110,"role": "DEF", "slot_key": "LB"},
        {"x": 108,"y": 20, "role": "MID", "slot_key": "RM"},
        {"x": 108,"y": 48, "role": "MID", "slot_key": "RCM"},
        {"x": 108,"y": 82, "role": "MID", "slot_key": "LCM"},
        {"x": 108,"y": 110,"role": "MID", "slot_key": "LM"},
        {"x": 158,"y": 65, "role": "FWD", "slot_key": "SS"},
        {"x": 190,"y": 65, "role": "FWD", "slot_key": "ST"},
    ],
    "4-1-4-1": [
        {"x": 14, "y": 65, "role": "GK",  "slot_key": "GK"},
        {"x": 52, "y": 20, "role": "DEF", "slot_key": "RB"},
        {"x": 52, "y": 48, "role": "DEF", "slot_key": "RCB"},
        {"x": 52, "y": 82, "role": "DEF", "slot_key": "LCB"},
        {"x": 52, "y": 110,"role": "DEF", "slot_key": "LB"},
        {"x": 88, "y": 65, "role": "MID", "slot_key": "CDM"},
        {"x": 130,"y": 15, "role": "MID", "slot_key": "RM"},
        {"x": 130,"y": 45, "role": "MID", "slot_key": "RCM"},
        {"x": 130,"y": 85, "role": "MID", "slot_key": "LCM"},
        {"x": 130,"y": 115,"role": "MID", "slot_key": "LM"},
        {"x": 190,"y": 65, "role": "FWD", "slot_key": "ST"},
    ],
    "5-4-1": [
        {"x": 14, "y": 65, "role": "GK",  "slot_key": "GK"},
        {"x": 52, "y": 12, "role": "DEF", "slot_key": "RWB"},
        {"x": 52, "y": 36, "role": "DEF", "slot_key": "RCB"},
        {"x": 52, "y": 65, "role": "DEF", "slot_key": "CB"},
        {"x": 52, "y": 94, "role": "DEF", "slot_key": "LCB"},
        {"x": 52, "y": 118,"role": "DEF", "slot_key": "LWB"},
        {"x": 110,"y": 24, "role": "MID", "slot_key": "RM"},
        {"x": 110,"y": 52, "role": "MID", "slot_key": "RCM"},
        {"x": 110,"y": 78, "role": "MID", "slot_key": "LCM"},
        {"x": 110,"y": 106,"role": "MID", "slot_key": "LM"},
        {"x": 190,"y": 65, "role": "FWD", "slot_key": "ST"},
    ],
    "4-5-1": [
        {"x": 14, "y": 65, "role": "GK",  "slot_key": "GK"},
        {"x": 52, "y": 20, "role": "DEF", "slot_key": "RB"},
        {"x": 52, "y": 48, "role": "DEF", "slot_key": "RCB"},
        {"x": 52, "y": 82, "role": "DEF", "slot_key": "LCB"},
        {"x": 52, "y": 110,"role": "DEF", "slot_key": "LB"},
        {"x": 108,"y": 12, "role": "MID", "slot_key": "RM"},
        {"x": 108,"y": 36, "role": "MID", "slot_key": "RCM"},
        {"x": 108,"y": 65, "role": "MID", "slot_key": "CM"},
        {"x": 108,"y": 94, "role": "MID", "slot_key": "LCM"},
        {"x": 108,"y": 118,"role": "MID", "slot_key": "LM"},
        {"x": 190,"y": 65, "role": "FWD", "slot_key": "ST"},
    ],
    "3-5-2": [
        {"x": 14, "y": 65, "role": "GK",  "slot_key": "GK"},
        {"x": 52, "y": 32, "role": "DEF", "slot_key": "RCB"},
        {"x": 52, "y": 65, "role": "DEF", "slot_key": "CB"},
        {"x": 52, "y": 98, "role": "DEF", "slot_key": "LCB"},
        {"x": 100,"y": 12, "role": "MID", "slot_key": "RWB"},
        {"x": 100,"y": 38, "role": "MID", "slot_key": "RCM"},
        {"x": 100,"y": 65, "role": "MID", "slot_key": "CM"},
        {"x": 100,"y": 92, "role": "MID", "slot_key": "LCM"},
        {"x": 100,"y": 118,"role": "MID", "slot_key": "LWB"},
        {"x": 178,"y": 42, "role": "FWD", "slot_key": "RST"},
        {"x": 178,"y": 88, "role": "FWD", "slot_key": "LST"},
    ],
    "4-3-1-2": [
        {"x": 14, "y": 65, "role": "GK",  "slot_key": "GK"},
        {"x": 52, "y": 20, "role": "DEF", "slot_key": "RB"},
        {"x": 52, "y": 48, "role": "DEF", "slot_key": "RCB"},
        {"x": 52, "y": 82, "role": "DEF", "slot_key": "LCB"},
        {"x": 52, "y": 110,"role": "DEF", "slot_key": "LB"},
        {"x": 95, "y": 28, "role": "MID", "slot_key": "RCM"},
        {"x": 95, "y": 65, "role": "MID", "slot_key": "CM"},
        {"x": 95, "y": 102,"role": "MID", "slot_key": "LCM"},
        {"x": 145,"y": 65, "role": "MID", "slot_key": "CAM"},
        {"x": 185,"y": 42, "role": "FWD", "slot_key": "RST"},
        {"x": 185,"y": 88, "role": "FWD", "slot_key": "LST"},
    ],
}

# Opp slot_key map by role + index within role
OPP_SLOT_KEYS = {
    "GK":  ["GK"],
    "DEF": ["RB", "RCB", "LCB", "LB", "CB"],
    "MID": ["RM", "RCM", "CM", "LCM", "LM", "CDM", "CAM"],
    "FWD": ["RST", "ST", "LST", "RW", "LW"],
}

def get_opp_slot_key(slots: list[dict], idx: int) -> str:
    if idx < len(slots):
        return slots[idx].get("slot_key", slots[idx]["role"])
    return "?"

def get_slots(formation: str) -> list[dict]:
    return FORMATION_SLOTS.get(formation, FORMATION_SLOTS["4-3-3"])

def mirror_slots(slots: list[dict]) -> list[dict]:
    return [{"x": PW - s["x"], "y": s["y"], "role": s["role"],
             "slot_key": "Opp " + s.get("slot_key", s["role"])} for s in slots]

def has_trait(player: dict, *traits: str) -> bool:
    return any(t in (player.get("traits") or []) for t in traits)

def find_player(xi: list[dict], *traits: str) -> Optional[dict]:
    for p in xi:
        if has_trait(p, *traits):
            return p
    return None

def find_player_by_position(xi: list[dict], *positions: str) -> Optional[dict]:
    for p in xi:
        pos = p.get("specific_position") or p.get("broad_position") or p.get("position") or ""
        if pos in positions:
            return p
    return None

def get_slot_for_player(xi: list[dict], slots: list[dict], player_name: str) -> Optional[dict]:
    for i, p in enumerate(xi):
        if p.get("name") == player_name and i < len(slots):
            return slots[i]
    return None

def player_slot_index(xi: list[dict], player_name: str) -> int:
    for i, p in enumerate(xi):
        if p.get("name") == player_name:
            return i
    return -1

def get_slot_key(xi: list[dict], slots: list[dict], player_name: str) -> Optional[str]:
    idx = player_slot_index(xi, player_name)
    if idx >= 0 and idx < len(slots):
        return slots[idx].get("slot_key")
    return None

def mirror_dy(base_y: float, dy: float) -> float:
    return dy if base_y <= PH / 2 else -dy

def clamp_x(x: float) -> float:
    return max(8.0, min(PW - 8, x))

def clamp_y(y: float) -> float:
    return max(8.0, min(PH - 8, y))

def get_linkup_players(
    xi: list[dict],
    linkup_pairs: list[dict],
    pair_id: str,
) -> tuple[Optional[dict], Optional[dict]]:
    for pair in linkup_pairs:
        if pair.get("id") == pair_id:
            pa = next((p for p in xi if p.get("name") == pair.get("player_a")), None)
            pb = next((p for p in xi if p.get("name") == pair.get("player_b")), None)
            return pa, pb
    return None, None