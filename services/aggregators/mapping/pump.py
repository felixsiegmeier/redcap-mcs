from typing import Dict

from ._base import FieldDef


# =============================================================================
# PUMP / ECMO  (instrument: pump, repeating, nur ecls_arm_2)
# =============================================================================
PUMP_REGISTRY: Dict[str, FieldDef] = {
    "ecls_rpm":  FieldDef("ecmo", ".*", r"^Drehzahl", "number", "0", "10000"),
    "ecls_pf":   FieldDef("ecmo", ".*", r"^Blutfluss arteriell|^Blutfluss.*l/min", "number_1dp_comma_decimal", "0,5", "12,0"),
    "ecls_gf":   FieldDef("ecmo", ".*", r"^Gasfluss", "number_1dp_comma_decimal", "0,5", "10,0"),
    "ecls_fi02": FieldDef("ecmo", ".*", r"^FiO2", "number", "0", "100"),
}


# =============================================================================
# IMPELLA  (instrument: impellaassessment_and_complications, repeating, nur impella_arm_2)
# =============================================================================
IMPELLA_REGISTRY: Dict[str, FieldDef] = {
    "imp_flow":          FieldDef("impella", ".*", r"^HZV", "number_1dp_comma_decimal", "0,5", "6,0"),
    "imp_purge_flow":    FieldDef("impella", ".*", r"Purgefluß|Purgefluss|Purge.*ml/h", "number_1dp_comma_decimal", "0,1", "20,0"),
    "imp_purge_pressure":FieldDef("impella", ".*", r"Purgedruck", "number", "1", "1000"),
}
