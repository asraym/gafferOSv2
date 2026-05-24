"""
Run this script to submit traits for all FC Bangalore players.
From backend directory:
    python submit_traits.py
"""

import requests

BASE = "http://localhost:8000"
SEASON_ID = 1

# player_id → (specific_position, traits)
PLAYER_TRAITS = {
    2: ("GK", [
        "Commands Area",
        "Sweeper Keeper",
        "Comfortable With Feet",
        "Organises Defence",
    ]),
    5: ("RB", [
        "Gets Forward Often",
        "Overlaps Winger",
        "Aggressive Presser",
        "Supports Build-Up",
        "Progressive Carrier",
    ]),
    6: ("LB", [
        "Stays Back At All Times",
        "Conservative Defender",
        "Marks Tightly",
        "Plays Short Simple Passes",
        "Holds Width",
    ]),
    3: ("CB", [
        "Holds Defensive Line",
        "Aggressive Tackler",
        "Strong In Air",
        "Organises Defence",
        "Clears Danger Early",
    ]),
    1: ("CB", [
        "Ball Playing Defender",
        "Progressive Passer",
        "Brings Ball Out Of Defence",
        "Calm Under Pressure",
        "Steps Into Midfield",
    ]),
    7: ("CDM", [
        "Shields Defence",
        "Breaks Up Play",
        "Deep Playmaker",
        "Recycles Possession",
        "Screens Passing Lanes",
        "Dictates Tempo",
    ]),
    10: ("CAM", [
        "Tries Killer Balls Often",
        "Through Ball Specialist",
        "Finds Space Between Lines",
        "Chance Creator",
        "Arrives In Box",
        "Quick Decision Maker",
    ]),
    8: ("CM", [
        "Box To Box Runner",
        "Late Runs Into Box",
        "Progressive Passer",
        "High Workrate",
        "Counterpresses Aggressively",
        "Vertical Runner",
    ]),
    12: ("ST", [
        "Target Man Play",
        "Aerial Threat",
        "Holds Up Ball",
        "Physical Forward",
        "Attacks Far Post",
        "Presses Defenders Aggressively",
    ]),
    9: ("CM", [
        "Dictates Tempo",
        "Creative Playmaker",
        "Progressive Carrier",
        "Combination Play Specialist",
        "Keeps Possession",
        "Roams From Position",
    ]),
    11: ("LW", [
        "Cuts Inside",
        "Shoots Frequently",
        "Counterattacking Runner",
        "Runs In Behind",
        "Direct Dribbler",
    ]),
    4: ("CB", [
        "Physical Defender",
        "Strong In Air",
        "Tight Marker",
        "Aggressive Tackler",
        "Fast Recovery Runner",
    ]),
}

results = {"ok": [], "failed": []}

for player_id, (position, traits) in PLAYER_TRAITS.items():
    resp = requests.post(
        f"{BASE}/api/players/{player_id}/traits",
        json={
            "season_id":         SEASON_ID,
            "specific_position": position,
            "traits":            traits,
        }
    )
    if resp.status_code == 200:
        results["ok"].append(f"Player {player_id} ({position}) — {len(traits)} traits")
    else:
        results["failed"].append(f"Player {player_id} — {resp.status_code}: {resp.text}")

print("\n✅ Submitted:")
for r in results["ok"]:
    print(f"  {r}")

if results["failed"]:
    print("\n❌ Failed:")
    for r in results["failed"]:
        print(f"  {r}")

print(f"\nDone. {len(results['ok'])} ok, {len(results['failed'])} failed.")