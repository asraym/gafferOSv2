"""
Player trait system for GafferOS v2.
Traits capture playing style and behavioural tendencies that CV stats cannot measure.
Coach selects any number of applicable traits per player per position.
Mutually exclusive traits are enforced — contradictory traits cannot coexist.
"""

# ─────────────────────────────────────────────
# TRAIT BANK — all traits per position group
# ─────────────────────────────────────────────

TRAIT_BANK = {

    "GK": [
        "Takes Risks Often",
        "Comfortable With Feet",
        "Long Thrower",
        "Commands Area",
        "Sweeper Keeper",
        "Stays On Line",
        "Organises Defence",
        "Punches Rather Than Catches",
        "Rushes Out Often",
        "Conservative Distributor",
    ],

    "CB": [
        "Ball Playing Defender",
        "Brings Ball Out Of Defence",
        "Long Pass Specialist",
        "Aggressive Tackler",
        "Conservative Tackler",
        "Strong In Air",
        "Steps Into Midfield",
        "Holds Defensive Line",
        "Sweeper Tendencies",
        "Blocks Shots Often",
        "Physical Defender",
        "Calm Under Pressure",
        "Press Resistant",
        "Organises Defence",
        "Tight Marker",
        "Fast Recovery Runner",
        "Clears Danger Early",
        "Progressive Passer",
    ],

    "FB": [
        "Gets Forward Often",
        "Stays Back At All Times",
        "Inverts Into Midfield",
        "Overlaps Winger",
        "Underlaps Winger",
        "Crosses Early",
        "Crosses From Byline",
        "Plays Short Simple Passes",
        "Switches Play Often",
        "Runs With Ball Often",
        "Carries Ball Into Final Third",
        "Aggressive Presser",
        "Tucks Inside In Possession",
        "Holds Width",
        "Marks Tightly",
        "Conservative Defender",
        "Attacks Far Post",
        "Supports Build-Up",
        "Progressive Carrier",
    ],

    "WB": [
        "Extremely Attacking",
        "Constant Overlaps",
        "High Defensive Workrate",
        "High Crossing Volume",
        "Arrives Late Into Box",
        "Drives Into Space",
        "Wide Playmaker",
        "Inverts Into Midfield",
        "Counterattacking Runner",
        "Recovers Quickly",
        "Press Resistant",
        "Creates Width",
        "Direct Runner",
        "Aggressive Ball Carrier",
        "Early Crosser",
        "Combination Player",
    ],

    "CDM": [
        "Dictates Tempo",
        "Shields Defence",
        "Drops Between Centre Backs",
        "Breaks Up Play",
        "Aggressive Presser",
        "Holds Position",
        "Progressive Passer",
        "Switches Play",
        "Carries Ball Forward",
        "Long Shot Threat",
        "Press Resistant",
        "Covers Wide Areas",
        "Recycles Possession",
        "Tackles Hard",
        "Conservative In Possession",
        "Deep Playmaker",
        "Screens Passing Lanes",
        "Retains Possession",
        "High Defensive Awareness",
    ],

    "CM": [
        "Box To Box Runner",
        "Late Runs Into Box",
        "Dictates Tempo",
        "Progressive Carrier",
        "Progressive Passer",
        "Creative Playmaker",
        "Keeps Possession",
        "Direct Passer",
        "High Workrate",
        "Press Resistant",
        "Counterpresses Aggressively",
        "Roams From Position",
        "Shoots From Distance",
        "Combination Play Specialist",
        "Switches Play",
        "Ball Winner",
        "Vertical Runner",
        "Intelligent Positioning",
        "Attacks Half Spaces",
    ],

    "CAM": [
        "Tries Killer Balls Often",
        "Roams From Position",
        "Finds Space Between Lines",
        "High Creativity",
        "Flair Player",
        "Dribbles Often",
        "Shoots From Distance",
        "Arrives In Box",
        "Combination Play Specialist",
        "Press Resistant",
        "Chance Creator",
        "Through Ball Specialist",
        "Free Role",
        "Moves Into Channels",
        "Quick Decision Maker",
        "Counterattacking Threat",
        "Supports Striker",
        "Half Space Operator",
    ],

    "WINGER": [
        "Holds Width",
        "Cuts Inside",
        "Attacks Byline",
        "Direct Dribbler",
        "High Crossing Volume",
        "Shoots Frequently",
        "Counterattacking Runner",
        "Tracks Back Defensively",
        "Wide Playmaker",
        "Combination Player",
        "Runs In Behind",
        "Isolates Defenders",
        "Moves Into Half Spaces",
        "Presses Aggressively",
        "Creative Dribbler",
        "High Flair",
        "Switches Wings",
        "Carries Ball Into Box",
        "Early Crosser",
    ],

    "ST": [
        "Likes To Beat Offside Trap",
        "Drops Deep To Link Play",
        "Holds Up Ball",
        "Presses Defenders Aggressively",
        "Clinical Finisher",
        "Shoots First Time",
        "Moves Into Channels",
        "Attacks Near Post",
        "Attacks Far Post",
        "Aerial Threat",
        "Physical Forward",
        "Creative Forward",
        "Poacher Movement",
        "Combination Play",
        "Counterattacking Threat",
        "Dribbles At Defenders",
        "Long Shot Threat",
        "Penalty Box Specialist",
        "False Nine Tendencies",
        "Target Man Play",
    ],
}

# Map specific positions to trait groups
POSITION_TO_GROUP = {
    "GK":  "GK",
    "CB":  "CB",
    "RB":  "FB",
    "LB":  "FB",
    "RWB": "WB",
    "LWB": "WB",
    "CDM": "CDM",
    "CM":  "CM",
    "CAM": "CAM",
    "RM":  "WINGER",
    "LM":  "WINGER",
    "RW":  "WINGER",
    "LW":  "WINGER",
    "ST":  "ST",
    "CF":  "ST",
    "SS":  "CAM",
}

# ─────────────────────────────────────────────
# CONFLICT MAP — mutually exclusive trait pairs
# If trait A is selected, trait B cannot be and vice versa
# ─────────────────────────────────────────────

CONFLICT_MAP = {

    # GK
    "Takes Risks Often":              ["Conservative Distributor", "Stays On Line"],
    "Stays On Line":                  ["Takes Risks Often", "Sweeper Keeper", "Rushes Out Often", "Commands Area"],
    "Sweeper Keeper":                 ["Stays On Line", "Punches Rather Than Catches"],
    "Rushes Out Often":               ["Stays On Line"],
    "Conservative Distributor":       ["Takes Risks Often", "Comfortable With Feet", "Long Thrower"],
    "Punches Rather Than Catches":    ["Sweeper Keeper"],

    # CB
    "Aggressive Tackler":             ["Conservative Tackler"],
    "Conservative Tackler":           ["Aggressive Tackler"],
    "Steps Into Midfield":            ["Holds Defensive Line", "Clears Danger Early"],
    "Holds Defensive Line":           ["Steps Into Midfield", "Sweeper Tendencies"],
    "Sweeper Tendencies":             ["Holds Defensive Line", "Tight Marker"],
    "Tight Marker":                   ["Sweeper Tendencies"],
    "Brings Ball Out Of Defence":     ["Clears Danger Early"],
    "Clears Danger Early":            ["Brings Ball Out Of Defence", "Steps Into Midfield", "Progressive Passer"],
    "Progressive Passer":             ["Clears Danger Early"],
    "Ball Playing Defender":          ["Clears Danger Early"],

    # FB
    "Gets Forward Often":             ["Stays Back At All Times", "Conservative Defender"],
    "Stays Back At All Times":        ["Gets Forward Often", "Attacks Far Post", "Carries Ball Into Final Third",
                                       "Aggressive Presser", "Overlaps Winger", "Underlaps Winger"],
    "Inverts Into Midfield":          ["Holds Width", "Overlaps Winger"],
    "Overlaps Winger":                ["Underlaps Winger", "Inverts Into Midfield", "Stays Back At All Times"],
    "Underlaps Winger":               ["Overlaps Winger", "Holds Width"],
    "Crosses Early":                  ["Crosses From Byline"],
    "Crosses From Byline":            ["Crosses Early"],
    "Holds Width":                    ["Inverts Into Midfield", "Tucks Inside In Possession", "Underlaps Winger"],
    "Tucks Inside In Possession":     ["Holds Width"],
    "Aggressive Presser":             ["Conservative Defender", "Stays Back At All Times"],
    "Conservative Defender":          ["Aggressive Presser", "Gets Forward Often", "Carries Ball Into Final Third"],

    # WB
    "Extremely Attacking":            ["High Defensive Workrate"],
    "High Defensive Workrate":        ["Extremely Attacking"],
    "Inverts Into Midfield":          ["Creates Width", "Early Crosser"],
    "Creates Width":                  ["Inverts Into Midfield"],
    "Early Crosser":                  ["Drives Into Space", "Inverts Into Midfield"],
    "Drives Into Space":              ["Early Crosser"],

    # CDM
    "Aggressive Presser":             ["Holds Position", "Conservative In Possession"],
    "Holds Position":                 ["Aggressive Presser", "Carries Ball Forward", "Covers Wide Areas"],
    "Carries Ball Forward":           ["Holds Position", "Shields Defence"],
    "Shields Defence":                ["Carries Ball Forward"],
    "Conservative In Possession":     ["Aggressive Presser", "Progressive Passer", "Carries Ball Forward"],
    "Progressive Passer":             ["Conservative In Possession"],
    "Drops Between Centre Backs":     ["Covers Wide Areas"],
    "Covers Wide Areas":              ["Drops Between Centre Backs", "Holds Position"],
    "Deep Playmaker":                 ["Aggressive Presser"],

    # CM
    "Keeps Possession":               ["Direct Passer"],
    "Direct Passer":                  ["Keeps Possession"],
    "Roams From Position":            ["Intelligent Positioning"],
    "Intelligent Positioning":        ["Roams From Position"],
    "Ball Winner":                    ["Creative Playmaker"],
    "Creative Playmaker":             ["Ball Winner"],

    # CAM
    "Roams From Position":            ["Finds Space Between Lines"],
    "Finds Space Between Lines":      ["Roams From Position"],
    "Free Role":                      ["Supports Striker"],
    "Supports Striker":               ["Free Role"],

    # WINGER
    "Holds Width":                    ["Cuts Inside", "Moves Into Half Spaces"],
    "Cuts Inside":                    ["Holds Width", "Attacks Byline", "High Crossing Volume", "Early Crosser"],
    "Attacks Byline":                 ["Cuts Inside"],
    "Early Crosser":                  ["Carries Ball Into Box", "Cuts Inside"],
    "Carries Ball Into Box":          ["Early Crosser"],
    "Tracks Back Defensively":        ["Counterattacking Runner"],
    "Counterattacking Runner":        ["Tracks Back Defensively"],
    "Moves Into Half Spaces":         ["Holds Width"],
    "High Crossing Volume":           ["Cuts Inside"],

    # ST
    "Drops Deep To Link Play":        ["Likes To Beat Offside Trap", "Poacher Movement"],
    "Likes To Beat Offside Trap":     ["Drops Deep To Link Play", "Holds Up Ball", "Target Man Play"],
    "Holds Up Ball":                  ["Likes To Beat Offside Trap", "Counterattacking Threat"],
    "Counterattacking Threat":        ["Holds Up Ball", "Target Man Play"],
    "Target Man Play":                ["False Nine Tendencies", "Likes To Beat Offside Trap",
                                       "Counterattacking Threat"],
    "False Nine Tendencies":          ["Target Man Play", "Aerial Threat", "Physical Forward"],
    "Aerial Threat":                  ["False Nine Tendencies"],
    "Physical Forward":               ["False Nine Tendencies"],
    "Attacks Near Post":              ["Attacks Far Post"],
    "Attacks Far Post":               ["Attacks Near Post"],
    "Poacher Movement":               ["Drops Deep To Link Play", "Creative Forward"],
    "Creative Forward":               ["Poacher Movement"],
}


# ─────────────────────────────────────────────
# TACTICAL TRAIT GROUPS
# Used by formation selector and tactical engine
# to derive tactical implications from traits
# ─────────────────────────────────────────────

# Traits that indicate a player suits an offensive role
OFFENSIVE_TRAITS = {
    "Gets Forward Often", "Inverts Into Midfield", "Overlaps Winger",
    "Carries Ball Into Final Third", "Extremely Attacking", "Constant Overlaps",
    "Arrives Late Into Box", "Box To Box Runner", "Late Runs Into Box",
    "Attacks Half Spaces", "Arrives In Box", "Counterattacking Threat",
    "Likes To Beat Offside Trap", "Drops Deep To Link Play", "False Nine Tendencies",
    "Runs In Behind", "Moves Into Channels", "Cuts Inside", "Shoots Frequently",
    "Long Shot Threat", "Shoots From Distance",
}

# Traits that indicate a player suits a defensive/holding role
DEFENSIVE_TRAITS = {
    "Stays Back At All Times", "Conservative Defender", "Shields Defence",
    "Holds Position", "Holds Defensive Line", "High Defensive Workrate",
    "Tracks Back Defensively", "Marks Tightly", "Screens Passing Lanes",
    "High Defensive Awareness", "Tight Marker", "Blocks Shots Often",
}

# Traits that indicate a player is a ball carrier / progressive
PROGRESSIVE_TRAITS = {
    "Progressive Carrier", "Carries Ball Forward", "Runs With Ball Often",
    "Direct Dribbler", "Drives Into Space", "Dribbles Often", "Dribbles At Defenders",
    "Aggressive Ball Carrier", "Creative Dribbler", "Progressive Passer",
    "Brings Ball Out Of Defence", "Ball Playing Defender",
}

# Traits that indicate a player suits a high press system
PRESS_TRAITS = {
    "Aggressive Presser", "Counterpresses Aggressively", "Presses Aggressively",
    "Presses Defenders Aggressively", "Breaks Up Play", "Tackles Hard",
}

# Traits that indicate a player is a creator / playmaker
CREATOR_TRAITS = {
    "Dictates Tempo", "Creative Playmaker", "Wide Playmaker", "Deep Playmaker",
    "Through Ball Specialist", "Tries Killer Balls Often", "Chance Creator",
    "High Creativity", "Switches Play", "Switches Play Often",
}

# Traits that indicate aerial/physical dominance
AERIAL_TRAITS = {
    "Strong In Air", "Aerial Threat", "Target Man Play",
    "Physical Defender", "Physical Forward", "Attacks Far Post", "Attacks Near Post",
}


# ─────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────

def get_traits_for_position(specific_position: str) -> list:
    """Returns valid traits for a given specific position."""
    group = POSITION_TO_GROUP.get(specific_position)
    if not group:
        return []
    return TRAIT_BANK.get(group, [])


def get_conflicts(trait: str) -> list:
    """Returns list of traits that conflict with the given trait."""
    return CONFLICT_MAP.get(trait, [])


def validate_traits(specific_position: str, selected_traits: list) -> dict:
    """
    Validates a set of selected traits for a position.
    Returns:
        {
            "valid": bool,
            "errors": list of conflict descriptions,
            "invalid_traits": list of traits not valid for this position
        }
    """
    valid_traits = get_traits_for_position(specific_position)
    errors = []
    invalid = []

    for trait in selected_traits:
        if trait not in valid_traits:
            invalid.append(trait)

    for i, trait in enumerate(selected_traits):
        conflicts = get_conflicts(trait)
        for other in selected_traits[i + 1:]:
            if other in conflicts:
                errors.append(f"'{trait}' and '{other}' cannot be selected together.")

    return {
        "valid":          len(errors) == 0 and len(invalid) == 0,
        "errors":         errors,
        "invalid_traits": invalid,
    }


def get_tactical_profile(traits: list) -> dict:
    """
    Derives a tactical profile from a player's traits.
    Returns scores for each tactical dimension — used by formation selector.
    All scores 0.0 to 1.0.
    """
    trait_set = set(traits)
    total     = max(len(trait_set), 1)

    return {
        "offensive_tendency":  len(trait_set & OFFENSIVE_TRAITS)  / total,
        "defensive_tendency":  len(trait_set & DEFENSIVE_TRAITS)  / total,
        "progressive_tendency": len(trait_set & PROGRESSIVE_TRAITS) / total,
        "press_tendency":      len(trait_set & PRESS_TRAITS)       / total,
        "creator_tendency":    len(trait_set & CREATOR_TRAITS)     / total,
        "aerial_tendency":     len(trait_set & AERIAL_TRAITS)      / total,
    }