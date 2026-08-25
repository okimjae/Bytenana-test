import re
from typing import Any, Optional


class ZoningClassifier:
    """Strict zoning classifier adhering to the Take-Home specification."""

    # Rule: starts with 'R' or 'Residential' (case-insensitive)
    RESIDENTIAL_PATTERN = re.compile(r"^(R|Residential)", re.IGNORECASE)

    @classmethod
    def is_residential(cls, zone_code: Any, zone_name: Any = None) -> bool:
        """Evaluates whether a zoning designation is residential.

        Rules:
        - Must start with 'R' or 'Residential' (e.g. R-1, RM, R-2, Residential - Single Family).
        - Non-matching: Commercial (C-1), Business (B-1), Industrial (I-1), Agriculture (AG), NaN/None.
        """
        if zone_code is not None and not (isinstance(zone_code, float) and str(zone_code) == "nan"):
            code_str = str(zone_code).strip()
            if code_str and code_str.lower() != "nan" and cls.RESIDENTIAL_PATTERN.match(code_str):
                return True

        if zone_name is not None and not (isinstance(zone_name, float) and str(zone_name) == "nan"):
            name_str = str(zone_name).strip()
            if name_str and name_str.lower() != "nan" and cls.RESIDENTIAL_PATTERN.match(name_str):
                return True

        return False


zoning_classifier = ZoningClassifier()
