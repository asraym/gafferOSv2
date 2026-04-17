import csv
import io
from typing import List, Dict


VALID_BROAD = ["GK", "DEF", "MID", "FWD"]
VALID_SPECIFIC = [
    "GK", "CB", "RB", "LB", "RWB", "LWB",
    "CDM", "CM", "CAM", "RM", "LM",
    "RW", "LW", "ST", "CF", "SS"
]

REQUIRED_COLUMNS = ["name", "broad_position", "specific_position"]
OPTIONAL_COLUMNS = ["secondary_position", "jersey_number", "nationality", "date_of_birth"]


class CSVImporter:

    def parse(self, file_bytes: bytes) -> Dict:
        """
        Parses CSV bytes into a list of validated player dicts.
        Returns: { "valid": [...], "errors": [...] }
        """
        try:
            content = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return {
                "valid": [],
                "errors": ["File encoding error — please save your CSV as UTF-8."]
            }

        reader = csv.DictReader(io.StringIO(content))

        # Check required columns exist
        if not reader.fieldnames:
            return {"valid": [], "errors": ["CSV file is empty."]}

        fieldnames = [f.strip().lower() for f in reader.fieldnames]
        missing = [col for col in REQUIRED_COLUMNS if col not in fieldnames]
        if missing:
            return {
                "valid": [],
                "errors": [f"Missing required columns: {missing}. Required: {REQUIRED_COLUMNS}"]
            }

        valid = []
        errors = []

        for i, row in enumerate(reader, start=2):  # start=2 because row 1 is header
            # Normalise keys
            row = {k.strip().lower(): v.strip() for k, v in row.items() if k}

            row_errors = self._validate_row(row, i)
            if row_errors:
                errors.extend(row_errors)
                continue

            valid.append({
                "name":               row.get("name"),
                "broad_position":     row.get("broad_position", "").upper(),
                "specific_position":  row.get("specific_position", "").upper(),
                "secondary_position": row.get("secondary_position", "").upper() or None,
                "jersey_number":      self._parse_int(row.get("jersey_number")),
                "nationality":        row.get("nationality") or None,
                "date_of_birth":      row.get("date_of_birth") or None,
            })

        return {"valid": valid, "errors": errors}

    def _validate_row(self, row: dict, line: int) -> List[str]:
        errors = []
        name = row.get("name", "").strip()
        if not name:
            errors.append(f"Row {line}: name is missing.")

        broad = row.get("broad_position", "").upper()
        if broad not in VALID_BROAD:
            errors.append(f"Row {line} ({name}): invalid broad_position '{broad}'. Must be one of {VALID_BROAD}.")

        specific = row.get("specific_position", "").upper()
        if specific not in VALID_SPECIFIC:
            errors.append(f"Row {line} ({name}): invalid specific_position '{specific}'. Must be one of {VALID_SPECIFIC}.")

        dob = row.get("date_of_birth", "").strip()
        if dob:
            from datetime import date
            try:
                date.fromisoformat(dob)
            except ValueError:
                errors.append(f"Row {line} ({name}): invalid date_of_birth '{dob}'. Use YYYY-MM-DD.")

        return errors

    def _parse_int(self, value):
        if not value:
            return None
        try:
            return int(value)
        except ValueError:
            return None