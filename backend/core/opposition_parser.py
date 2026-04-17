import re


FORMATION_PATTERNS = [
    r"\b(4-4-2)\b", r"\b(4-3-3)\b", r"\b(4-2-3-1)\b",
    r"\b(4-5-1)\b", r"\b(5-4-1)\b", r"\b(5-3-2)\b",
    r"\b(3-5-2)\b", r"\b(3-4-3)\b", r"\b(4-1-4-1)\b",
]

PRESS_STYLE_KEYWORDS = {
    "high": ["high press", "press high", "aggressive press", "press aggressively", "gegenpressing"],
    "mid":  ["mid block", "medium block", "mid press", "moderate press"],
    "low":  ["low block", "sit deep", "deep block", "park the bus", "very defensive", "defensive"],
}

DEFENSIVE_LINE_KEYWORDS = {
    "high": ["high line", "push high", "high defensive line"],
    "deep": ["deep", "sit back", "low block", "park the bus", "defend deep"],
    "medium": ["medium line", "mid line", "compact"],
}

PLAYING_STYLE_KEYWORDS = {
    "direct":     ["direct", "long ball", "bypass midfield", "route one"],
    "possession": ["possession", "pass and move", "tiki taka", "build from back", "patient"],
    "counter":    ["counter", "on the break", "transition", "quick breaks"],
    "physical":   ["physical", "aggressive", "aerial", "set pieces", "crosses"],
}

SET_PIECE_KEYWORDS = {
    "high":   ["dangerous at set pieces", "strong from corners", "set piece threat",
                "good at set pieces", "corners are dangerous", "dangerous corners"],
    "medium": ["decent set pieces", "okay at set pieces", "some threat from set pieces"],
    "low":    ["weak at set pieces", "poor from corners", "no set piece threat"],
}

ATTRIBUTE_PATTERNS = [
    # pace / speed
    (r"\b(pacey|quick|fast|rapid)\s+([\w\s]+?)(?:\.|,|$)", "pace", "high"),
    (r"\b(slow|lacks pace|not quick)\s+([\w\s]+?)(?:\.|,|$)", "pace", "low"),
    # aerial
    (r"\b(strong in the air|good in the air|aerial threat|wins headers)\b", "aerial", "strong"),
    (r"\b(poor in the air|weak aerially|loses headers)\b", "aerial", "weak"),
    # technical
    (r"\b(technically strong|good on the ball|good feet|skilful)\b", "technical", "strong"),
    (r"\b(poor touch|heavy touch|not technical)\b", "technical", "weak"),
    # experience
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
        return {
            "likely_formation":  self._extract_formation(text),
            "press_style":       self._extract_keyword(text, PRESS_STYLE_KEYWORDS),
            "defensive_line":    self._extract_keyword(text, DEFENSIVE_LINE_KEYWORDS),
            "playing_style":     self._extract_keyword(text, PLAYING_STYLE_KEYWORDS),
            "set_piece_threat":  self._extract_keyword(text, SET_PIECE_KEYWORDS),
            "attributes":        self._extract_attributes(text),
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

    def _extract_attributes(self, text: str) -> dict:
        attributes = {}

        # Extract position-specific mentions
        # e.g. "left back is slow" → {"left_back": "slow"}
        position_attr_pattern = r"(left back|right back|centre back|center back|striker|winger|goalkeeper|keeper|midfielder|fullback|full back)\s+(?:is|are|looks?|seems?)\s+([\w\s]+?)(?:\.|,|and|but|$)"
        for match in re.finditer(position_attr_pattern, text):
            position = match.group(1).strip().replace(" ", "_")
            attribute = match.group(2).strip()
            attributes[position] = attribute

        # Extract general attributes
        for pattern, attr_key, attr_value in ATTRIBUTE_PATTERNS:
            if re.search(pattern, text):
                if attr_key not in attributes:
                    attributes[attr_key] = attr_value

        return attributes