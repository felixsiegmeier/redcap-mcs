from typing import Dict

from ._base import FieldDef


# =============================================================================
# DEMOGRAPHIE  (instrument: demography, nicht repeating, baseline_arm_2)
# =============================================================================
DEMOGRAPHY_REGISTRY: Dict[str, FieldDef] = {
    "birthdate": FieldDef("patient_info", ".*", r"^Geburtsdatum", "date_dmy"),  # String → _parse_date()
    "weight":    FieldDef("patient_info", ".*", r"^Gewicht",      "number"),
    "height":    FieldDef("patient_info", ".*", r"^Grö(?:ss|ß)e", "number"),
}
