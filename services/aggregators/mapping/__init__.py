"""
Zentrales Parameter-Registry für alle REDCap-Felder.

Jeder Eintrag ist ein REDCap-Feldname → FieldDef mit:
  source:     Logischer Quellenname (wird über SOURCE_MAPPING aufgelöst)
  category:   Regex-Pattern für die category-Spalte im DataFrame
  pattern:    Regex-Pattern für die parameter-Spalte im DataFrame
  validation: REDCap-Validierungstyp für die CSV-Formatierung

Pre-Assessment-Registries werden aus gemeinsamen Pattern-Dicts generiert –
dadurch existiert jedes Extraction-Pattern genau einmal, und die
REDCap-Keys (mit/ohne _i-Suffix) entstehen automatisch.

Nicht-extrahierbare Felder (Flags, Checkbox-Arrays, berechnete Werte)
bleiben Custom-Code in den Aggregatoren und erscheinen ggf. nur in den
manuellen Extras am Ende von REDCAP_VALIDATION_TYPES.
"""

from typing import Dict

from ._base import FieldDef
from .lab import LAB_REGISTRY
from .hemodynamics import (
    HEMODYNAMICS_REGISTRY,
    HEMODYNAMICS_MEDICATION_MAP,
    TRANSFUSION_REGISTRY,
    VASOACTIVE_SPEC_MAP,
    VENT_SPEC_MAP,
    ANTICOAGULANT_MAP,
    ANTIPLATELET_MAP,
    ANTIBIOTIC_MAP,
    MEDICATION_SPEC_MAP,
    NARCOTICS_SPEC_MAP,
)
from .pump import PUMP_REGISTRY, IMPELLA_REGISTRY
from .demography import DEMOGRAPHY_REGISTRY
from .pre_assessment import (
    PRE_IMPELLA_BGA_REGISTRY,
    PRE_IMPELLA_VENT_REGISTRY,
    PRE_IMPELLA_VENT_SPEC_REGISTRY,
    PRE_IMPELLA_HEMO_REGISTRY,
    PRE_IMPELLA_GCS_REGISTRY,
    PRE_IMPELLA_LAB_REGISTRY,
    PRE_VAECLS_BGA_REGISTRY,
    PRE_VAECLS_VENT_REGISTRY,
    PRE_VAECLS_VENT_SPEC_REGISTRY,
    PRE_VAECLS_HEMO_REGISTRY,
    PRE_VAECLS_GCS_REGISTRY,
    PRE_VAECLS_LAB_REGISTRY,
)
from .sources import SOURCE_MAPPING


# =============================================================================
# REDCAP_VALIDATION_TYPES  (auto-generiert + manuelle Extras)
#
# Alle Registries tragen automatisch bei. Felder ohne Registry-Eintrag
# (berechnete Werte, Katecholamin-Raten, etc.) werden manuell ergänzt.
# =============================================================================
_ALL_REGISTRIES = [
    LAB_REGISTRY,
    HEMODYNAMICS_REGISTRY,
    PUMP_REGISTRY,
    IMPELLA_REGISTRY,
    DEMOGRAPHY_REGISTRY,
    TRANSFUSION_REGISTRY,
    PRE_IMPELLA_BGA_REGISTRY,
    PRE_IMPELLA_VENT_REGISTRY,
    PRE_IMPELLA_VENT_SPEC_REGISTRY,
    PRE_IMPELLA_HEMO_REGISTRY,
    PRE_IMPELLA_GCS_REGISTRY,
    PRE_IMPELLA_LAB_REGISTRY,
    PRE_VAECLS_BGA_REGISTRY,
    PRE_VAECLS_VENT_REGISTRY,
    PRE_VAECLS_VENT_SPEC_REGISTRY,
    PRE_VAECLS_HEMO_REGISTRY,
    PRE_VAECLS_GCS_REGISTRY,
    PRE_VAECLS_LAB_REGISTRY,
]

REDCAP_VALIDATION_TYPES: Dict[str, str] = {
    field: spec.validation
    for registry in _ALL_REGISTRIES
    for field, spec in registry.items()
}

REDCAP_FIELD_DEFS: Dict[str, FieldDef] = {
    field: spec
    for registry in _ALL_REGISTRIES
    for field, spec in registry.items()
}

# Manuelle Ergänzungen: Felder ohne eigenen Registry-Eintrag
REDCAP_VALIDATION_TYPES.update({
    # Hämodynamik – nur Formatierung, keine direkte Extraktion
    "hfv_rate":           "number",
    "vent_map":           "number",
    "urine":              "number",
    "output_renal_repl":  "number",
    "fluid_balance_numb": "number",
    "nirs_left_f":        "number",
    "nirs_right_f":       "number",
    # Impella – nicht extrahiert via Registry
    "imp_level":          "number",
    "imp_rpm":            "number_2dp_comma_decimal",
    # Katecholamin-Raten (täglich + pre-assessment)
    **{k: "number_2dp_comma_decimal" for k in HEMODYNAMICS_MEDICATION_MAP},
    **{f"pre_{k}":   "number_2dp_comma_decimal" for k in HEMODYNAMICS_MEDICATION_MAP},
    **{f"pre_{k}_i": "number_2dp_comma_decimal" for k in HEMODYNAMICS_MEDICATION_MAP},
    # Ausnahme: pre_vasopressin_i ist in REDCap 1dp (nicht 2dp)
    "pre_vasopressin_i": "number_1dp_comma_decimal",
})


__all__ = [
    "FieldDef",
    "LAB_REGISTRY",
    "HEMODYNAMICS_REGISTRY",
    "HEMODYNAMICS_MEDICATION_MAP",
    "TRANSFUSION_REGISTRY",
    "VASOACTIVE_SPEC_MAP",
    "VENT_SPEC_MAP",
    "ANTICOAGULANT_MAP",
    "ANTIPLATELET_MAP",
    "ANTIBIOTIC_MAP",
    "MEDICATION_SPEC_MAP",
    "NARCOTICS_SPEC_MAP",
    "PUMP_REGISTRY",
    "IMPELLA_REGISTRY",
    "DEMOGRAPHY_REGISTRY",
    "PRE_IMPELLA_BGA_REGISTRY",
    "PRE_IMPELLA_VENT_REGISTRY",
    "PRE_IMPELLA_VENT_SPEC_REGISTRY",
    "PRE_IMPELLA_HEMO_REGISTRY",
    "PRE_IMPELLA_GCS_REGISTRY",
    "PRE_IMPELLA_LAB_REGISTRY",
    "PRE_VAECLS_BGA_REGISTRY",
    "PRE_VAECLS_VENT_REGISTRY",
    "PRE_VAECLS_VENT_SPEC_REGISTRY",
    "PRE_VAECLS_HEMO_REGISTRY",
    "PRE_VAECLS_GCS_REGISTRY",
    "PRE_VAECLS_LAB_REGISTRY",
    "SOURCE_MAPPING",
    "REDCAP_VALIDATION_TYPES",
    "REDCAP_FIELD_DEFS",
]
