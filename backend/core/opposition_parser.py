import re


FORMATION_PATTERNS = [
    r"\b(4-4-2)\b", r"\b(4-3-3)\b", r"\b(4-2-3-1)\b",
    r"\b(4-5-1)\b", r"\b(5-4-1)\b", r"\b(5-3-2)\b",
    r"\b(3-5-2)\b", r"\b(3-4-3)\b", r"\b(4-1-4-1)\b",
    r"\b(4-3-1-2)\b",
]

PRESS_STYLE_KEYWORDS = {
    "high": ["high press", "press high", "aggressive press",
             "press aggressively", "gegenpressing"],
    "mid":  ["mid block", "medium block", "mid press", "moderate press"],
    "low":  ["low block", "sit deep", "deep block", "park the bus",
             "very defensive", "defensive"],
}

DEFENSIVE_LINE_KEYWORDS = {
    "high":   ["high line", "push high", "high defensive line"],
    "deep":   ["deep", "sit back", "low block", "park the bus", "defend deep"],
    "medium": ["medium line", "mid line", "compact"],
}

PLAYING_STYLE_KEYWORDS = {
    "direct":     ["direct", "long ball", "bypass midfield", "route one"],
    "possession": ["possession", "pass and move", "tiki taka",
                   "build from back", "patient"],
    "counter":    ["counter", "on the break", "transition", "quick breaks"],
    "physical":   ["physical", "aggressive", "aerial", "set pieces", "crosses"],
}

SET_PIECE_KEYWORDS = {
    "high":   ["dangerous at set pieces", "strong from corners",
               "set piece threat", "good at set pieces",
               "corners are dangerous", "dangerous corners"],
    "medium": ["decent set pieces", "okay at set pieces",
               "some threat from set pieces"],
    "low":    ["weak at set pieces", "poor from corners",
               "no set piece threat"],
}

# Opponent strength buzzwords
OPPONENT_STRENGTH_KEYWORDS = {
    "high": [
        "top of the table", "top of the league", "league leaders",
        "first in the table", "1st in the table", "title contenders",
        "title challengers", "unbeaten", "best team", "strong side",
        "strongest team", "top side", "top team", "in form side",
        "on a winning run", "best in the league", "top 3",
        "top three", "promotion candidates", "champions",
        "defending champions", "favourites",
    ],
    "medium": [
        "mid table", "middle of the table", "average side",
        "decent team", "solid side", "competitive",
        "evenly matched", "similar level",
    ],
    "low": [
        "bottom of the table", "bottom half", "relegation",
        "struggling", "weak side", "poor form",
        "winless", "without a win", "bottom 3", "bottom three",
        "weakest team", "easy game", "should win",
        "inferior", "lower league",
    ],
}

# League position extraction
# Matches "1st", "2nd", "3rd", "top 3", "bottom 5" etc
LEAGUE_POSITION_PATTERNS = [
    # Exact position: "1st in the table", "3rd place"
    (r"\b([1-9]|1[0-9]|20)(?:st|nd|rd|th)\s+(?:in\s+the\s+(?:table|league)|place)\b",
     "exact"),
    # Top N: "top 3", "top three"
    (r"\btop\s+([1-9]|three|four|five|six)\b",
     "top_n"),
    # Bottom N: "bottom 3", "bottom half"
    (r"\bbottom\s+([1-9]|three|four|five|half)\b",
     "bottom_n"),
]

WORD_TO_NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "half": 10,
}

ATTRIBUTE_PATTERNS = [
    (r"\b(pacey|quick|fast|rapid)\s+([\w\s]+?)(?:\.|,|$)",  "pace", "high"),
    (r"\b(slow|lacks pace|not quick)\s+([\w\s]+?)(?:\.|,|$)", "pace", "low"),
    (r"\b(strong in the air|good in the air|aerial threat|wins headers)\b",
     "aerial", "strong"),
    (r"\b(poor in the air|weak aerially|loses headers)\b", "aerial", "weak"),
    (r"\b(technically strong|good on the ball|good feet|skilful)\b",
     "technical", "strong"),
    (r"\b(poor touch|heavy touch|not technical)\b", "technical", "weak"),
    (r"\b(experienced|veteran|captain|leader)\b", "experience", "high"),
    (r"\b(young|inexperienced|raw talent)\b", "experience", "low"),
]

POSITION_KEYWORDS = [
    "goalkeeper", "keeper", "gk",
    "centre back", "center back", "cb", "defender",
    "left back", "right back", "fullback", "full back",
    "midfielder", "midfield", "cm", "cdm", "cam",
    "winger", "wide", "left wing", "right wing",
    "striker", "forward", "centre forward", "cf", "st",
]


class OppositionParser:

    def parse(self, notes: str) -> dict:
        text = notes.lower().strip()
        strength, position = self._extract_strength(text)
        return {
            "likely_formation":   self._extract_formation(text),
            "press_style":        self._extract_keyword(text, PRESS_STYLE_KEYWORDS),
            "defensive_line":     self._extract_keyword(text, DEFENSIVE_LINE_KEYWORDS),
            "playing_style":      self._extract_keyword(text, PLAYING_STYLE_KEYWORDS),
            "set_piece_threat":   self._extract_keyword(text, SET_PIECE_KEYWORDS),
            "attributes":         self._extract_attributes(text),
            "opponent_strength":  strength,    # high / medium / low / None
            "league_position":    position,    # int or None
            "raw_scouting_notes": notes,
        }

    def _extract_formation(self, text: str):
        for pattern in FORMATION_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None

    def _extract_keyword(self, text: str, keyword_map: dict):
        for value, keywords in keyword_map.items():
            for kw in keywords:
                if kw in text:
                    return value
        return None

    def _extract_strength(self, text: str) -> tuple:
        """
        Returns (strength_label, league_position).
        strength_label: "high" / "medium" / "low" / None
        league_position: int (1-20) or None
        """
        # Try exact league position first — most precise signal
        league_position = None
        for pattern, kind in LEAGUE_POSITION_PATTERNS:
            match = re.search(pattern, text)
            if match:
                val = match.group(1)
                if kind == "exact":
                    try:
                        league_position = int(val)
                    except ValueError:
                        pass
                elif kind == "top_n":
                    n = WORD_TO_NUM.get(val, None) or (int(val) if val.isdigit() else None)
                    if n:
                        league_position = n  # store as max position in top N
                elif kind == "bottom_n":
                    n = WORD_TO_NUM.get(val, None) or (int(val) if val.isdigit() else None)
                    if n:
                        league_position = 20 - n + 1  # approximate bottom position
                break

        # Derive strength from position if found
        if league_position is not None:
            if league_position <= 3:
                return "high", league_position
            elif league_position <= 8:
                return "medium", league_position
            else:
                return "low", league_position

        # Fall back to buzzword matching
        strength = self._extract_keyword(text, OPPONENT_STRENGTH_KEYWORDS)
        return strength, None

    def _extract_attributes(self, text: str) -> dict:
        attributes = {}

        position_attr_pattern = (
            r"(left back|right back|centre back|center back|striker|winger|"
            r"goalkeeper|keeper|midfielder|fullback|full back)"
            r"\s+(?:is|are|looks?|seems?)\s+([\w\s]+?)(?:\.|,|and|but|$)"
        )
        for match in re.finditer(position_attr_pattern, text):
            position  = match.group(1).strip().replace(" ", "_")
            attribute = match.group(2).strip()
            attributes[position] = attribute

        for pattern, attr_key, attr_value in ATTRIBUTE_PATTERNS:
            if re.search(pattern, text):
                if attr_key not in attributes:
                    attributes[attr_key] = attr_value

        return attributes