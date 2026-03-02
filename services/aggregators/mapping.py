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

from typing import Any, Dict, NamedTuple, Optional


class FieldDef(NamedTuple):
    source:     str            # Logischer Quellenname (via SOURCE_MAPPING)
    category:   str            # Regex für category-Spalte (".*" = beliebig)
    pattern:    str            # Regex für parameter-Spalte
    validation: str = "number" # REDCap-Validierungstyp (Default: number)


# =============================================================================
# LABOR  (instrument: labor, repeating)
# =============================================================================
LAB_REGISTRY: Dict[str, FieldDef] = {
    # Blutgase arteriell
    "pc02":    FieldDef("lab", "Blutgase arteriell", r"^PCO2",                        "number_1dp_comma_decimal"),
    "p02":     FieldDef("lab", "Blutgase arteriell", r"^PO2",                         "number_1dp_comma_decimal"),
    "ph":      FieldDef("lab", "Blutgase arteriell", r"^PH$|^PH ",                    "number_2dp_comma_decimal"),
    "hco3":    FieldDef("lab", "Blutgase arteriell", r"^HCO3",                        "number_1dp_comma_decimal"),
    "be":      FieldDef("lab", "Blutgase arteriell", r"^ABEc",                        "number_1dp_comma_decimal"),
    "sa02":    FieldDef("lab", "Blutgase arteriell", r"^O2-SAETTIGUNG",               "number_1dp_comma_decimal"),
    "k":       FieldDef("lab", "Blutgase arteriell", r"^KALIUM",                      "number_1dp_comma_decimal"),
    "na":      FieldDef("lab", "Blutgase arteriell", r"^NATRIUM",                     "number"),
    "gluc":    FieldDef("lab", "Blutgase arteriell", r"^GLUCOSE",                     "number"),
    "lactate": FieldDef("lab", "Blutgase arteriell", r"^LACTAT",                      "number"),
    # Blutgase venös (inkl. gemischt-venös)
    "sv02":    FieldDef("lab", r"Blutgase venös|Blutgase gv", r"^O2-SAETTIGUNG",      "number_1dp_comma_decimal"),
    # Hämatologie / Blutbild
    "wbc":     FieldDef("lab", "Blutbild", r"^WBC",                                   "number_1dp_comma_decimal"),
    "hb":      FieldDef("lab", "Blutbild", r"^HB \(HGB\)|^HB\b",                     "number_1dp_comma_decimal"),
    "hct":     FieldDef("lab", "Blutbild", r"^HCT",                                   "number_1dp_comma_decimal"),
    "mcv":     FieldDef("lab", "Blutbild", r"^MCV"),
    "mch":     FieldDef("lab", "Blutbild", r"^MCH"),
    "mchc":    FieldDef("lab", "Blutbild", r"^MCHC"),
    "rdw":     FieldDef("lab", "Blutbild", r"^RDW"),
    "ret":     FieldDef("lab", "Blutbild", r"^RETIKULOZYTEN"),
    "rpi":     FieldDef("lab", "Blutbild", r"^Reti-Produktionsindex"),
    "plt":     FieldDef("lab", "Blutbild", r"^PLT"),
    "fhb":     FieldDef("lab", r"Blutbild|Klinische Chemie", r"^FREIES HB",           "number_1dp_comma_decimal"),
    # Gerinnung
    "ptt":     FieldDef("lab", "Gerinnung", r"^PTT",                                  "number_1dp_comma_decimal"),
    "quick":   FieldDef("lab", "Gerinnung", r"^TPZ"),
    "inr":     FieldDef("lab", "Gerinnung", r"^INR",                                  "number_1dp_comma_decimal"),
    "act":     FieldDef("act", ".*",        r"^ACT"),
    # Enzyme
    "ck":      FieldDef("lab", "Enzyme", r"^CK \[|^CK$"),
    "ckmb":    FieldDef("lab", "Enzyme", r"^CK-MB"),
    "ggt":     FieldDef("lab", "Enzyme", r"^GGT"),
    "ldh":     FieldDef("lab", "Enzyme", r"^LDH"),
    "lipase":  FieldDef("lab", "Enzyme", r"^LIPASE",                                  "number_1dp_comma_decimal"),
    "got":     FieldDef("lab", "Enzyme", r"^GOT"),
    "alat":    FieldDef("lab", "Enzyme", r"^GPT"),
    "trop":    FieldDef("lab", r"Enzyme|Klinische Chemie", r"^Troponin|^HS-TROP"),
    # Klinische Chemie
    "pct":     FieldDef("lab", r"Klinische Chemie|Proteine", r"^PROCALCITONIN",       "number_2dp_comma_decimal"),
    "crp":     FieldDef("lab", r"Klinische Chemie|Proteine", r"^CRP",                 "number_1dp_comma_decimal"),
    "bili":    FieldDef("lab", "Klinische Chemie",           r"^BILI",                "number_2dp_comma_decimal"),
    "crea":    FieldDef("lab", r"Klinische Chemie|Retention", r"^KREATININ",          "number_1dp_comma_decimal"),
    "urea":    FieldDef("lab", r"Klinische Chemie|Retention", r"^HARNSTOFF",          "number_1dp_comma_decimal"),
    "cc":      FieldDef("lab", r"Klinische Chemie|Retention", r"^GFRKREA",            "number_2dp_comma_decimal"),
    "albumin": FieldDef("lab", r"Klinische Chemie|Proteine", r"^ALBUMIN",             "number_1dp_comma_decimal"),
    "hapto":   FieldDef("lab", r"Klinische Chemie|Proteine", r"^HAPTOGLOBIN",         "number_1dp_comma_decimal"),
}


# =============================================================================
# HÄMODYNAMIK & BEATMUNG  (instrument: hemodynamics_ventilation_medication, repeating)
# =============================================================================
HEMODYNAMICS_REGISTRY: Dict[str, FieldDef] = {
    # Vitals
    "hr":           FieldDef("vitals", ".*",          r"^HF\s*\["),
    "sys_bp":       FieldDef("vitals", ".*",          r"^ABPs\s*\[|^ARTs\s*\["),
    "dia_bp":       FieldDef("vitals", ".*",          r"^ABPd\s*\[|^ARTd\s*\["),
    "mean_bp":      FieldDef("vitals", ".*",          r"^ABPm\s*\[|^ARTm\s*\["),
    "cvp":          FieldDef("vitals", ".*",          r"^ZVDm\s*\["),
    "pcwp":         FieldDef("vitals", r"^Online.*",  r"^PCWP\s*\[|^PAWP\s*\["),
    "sys_pap":      FieldDef("vitals", r"^Online.*",  r"^PAPs\s*\["),
    "dia_pap":      FieldDef("vitals", r"^Online.*",  r"^PAPd\s*\["),
    "mean_pap":     FieldDef("vitals", r"^Online.*",  r"^PAPm\s*\["),
    "ci":           FieldDef("vitals", r"^Online.*",  r"^CCI\s*\[|^HZV",             "number_1dp_comma_decimal"),
    "nirs_left_c":  FieldDef("vitals", ".*",          r"NIRS Channel 1 RSO2|NIRS.*Channel.*1"),
    "nirs_right_c": FieldDef("vitals", ".*",          r"NIRS Channel 2 RSO2|NIRS.*Channel.*2"),
    "sp02":         FieldDef("vitals", ".*",          r"^SpO2\s*\[%\]"),
    # Beatmung (Hamilton + Standard-Geräte)
    "fi02":          FieldDef("respiratory", ".*", r"^FiO2\s*(\[%\]|in\s*%)"),
    "o2":            FieldDef("o2_supply",   ".*", r"^O2\s*l/min"),
    "vent_peep":     FieldDef("respiratory", ".*", r"^s?PEEP\s*\[|^Expirationsdruck\s*\(PEEP\)"),
    "vent_pip":      FieldDef("respiratory", ".*", r"^s?P[Ii][Pp]\s*\[|^Ppeak\s*\[|^s?Pin\s*\[|^insp.*Spitz"),
    "conv_vent_rate":FieldDef("respiratory", ".*", r"mand.*Atemfrequenz|mandator.*Atemfrequenz"),
    "vent_spec":     FieldDef("respiratory", ".*", r"^Modus$|^Beatmungsform"),  # String → _map_ventilation_spec()
    # Neurologie
    "rass": FieldDef("Richmond-Agitation-Sedation",      ".*", r"^Summe Richmond-Agitation-Sedation"),
    "gcs":  FieldDef("GCS (Jugendliche und Erwachsene)", ".*", r"^Summe GCS2"),
}

# Katecholamine/Vasopressoren: Raten-Berechnung (ml/h → µg/kg/min)
# Nicht in HEMODYNAMICS_REGISTRY, da sie separate Logik brauchen
HEMODYNAMICS_MEDICATION_MAP: Dict[str, str] = {
    "norepinephrine": r"(?<!o)Norepinephrin|^Arterenol",
    "epinephrine":    r"(?<!Nor)Epinephrin|^Suprarenin",
    "dobutamine":     r"Dobutamin",
    "milrinone":      r"Milrinone|Corotrop",
    "vasopressin":    r"Vasopressin|Empressin",
}


# =============================================================================
# PUMP / ECMO  (instrument: pump, repeating, nur ecls_arm_2)
# =============================================================================
PUMP_REGISTRY: Dict[str, FieldDef] = {
    "ecls_rpm":  FieldDef("ecmo", ".*", r"^Drehzahl"),
    "ecls_pf":   FieldDef("ecmo", ".*", r"^Blutfluss arteriell|^Blutfluss.*l/min",   "number_1dp_comma_decimal"),
    "ecls_gf":   FieldDef("ecmo", ".*", r"^Gasfluss",                                 "number_1dp_comma_decimal"),
    "ecls_fi02": FieldDef("ecmo", ".*", r"^FiO2"),
}


# =============================================================================
# IMPELLA  (instrument: impellaassessment_and_complications, repeating, nur impella_arm_2)
# =============================================================================
IMPELLA_REGISTRY: Dict[str, FieldDef] = {
    "imp_flow":          FieldDef("impella", ".*", r"^HZV",                           "number_1dp_comma_decimal"),
    "imp_purge_flow":    FieldDef("impella", ".*", r"Purgefluß|Purgefluss|Purge.*ml/h","number_1dp_comma_decimal"),
    "imp_purge_pressure":FieldDef("impella", ".*", r"Purgedruck"),
}


# =============================================================================
# DEMOGRAPHIE  (instrument: demography, nicht repeating, baseline_arm_2)
# =============================================================================
DEMOGRAPHY_REGISTRY: Dict[str, FieldDef] = {
    "birthdate": FieldDef("patient_info", ".*", r"^Geburtsdatum"),  # String → _parse_date()
    "weight":    FieldDef("patient_info", ".*", r"^Gewicht"),
    "height":    FieldDef("patient_info", ".*", r"^Grö(?:ss|ß)e"),
}


# =============================================================================
# TRANSFUSION  (Teil von Hämodynamik, zählt Einheiten statt aggregieren)
# =============================================================================
TRANSFUSION_REGISTRY: Dict[str, FieldDef] = {
    "thromb_t": FieldDef("medication", "Blutersatz", r"^TK"),
    "ery_t":    FieldDef("medication", "Blutersatz", r"^EK"),
    "ffp_t":    FieldDef("medication", "Blutersatz", r"^FFP"),
    "ppsb_t":   FieldDef("medication", ".*",         r"Prothromplex|Cofactor"),
    "fib_t":    FieldDef("medication", ".*",         r"Haemocomplettan"),
    "at3_t":    FieldDef("medication", ".*",         r"Antithrombin"),
    "fxiii_t":  FieldDef("medication", ".*",         r"Faktor XIII"),
}


# =============================================================================
# PRE-ASSESSMENT: Gemeinsame Pattern-Definitionen
#
# Konvention: Keys sind die "Stamm"-Namen ohne Prefix/Suffix.
# Daraus werden per Dict-Comprehension erzeugt:
#   PRE_IMPELLA_*_REGISTRY  → {f"pre_{k}_i": v}
#   PRE_VAECLS_*_REGISTRY   → {f"pre_{k}": v}
# =============================================================================

_PRE_BGA: Dict[str, FieldDef] = {
    "pco2":    FieldDef("lab", "Blutgase arteriell",          r"^PCO2",             "number_1dp_comma_decimal"),
    "p02":     FieldDef("lab", "Blutgase arteriell",          r"^PO2",              "number_1dp_comma_decimal"),
    "ph":      FieldDef("lab", "Blutgase arteriell",          r"^PH$|^PH ",         "number_2dp_comma_decimal"),
    "hco3":    FieldDef("lab", "Blutgase arteriell",          r"^HCO3",             "number_1dp_comma_decimal"),
    "be":      FieldDef("lab", "Blutgase arteriell",          r"^ABEc",             "number_1dp_comma_decimal"),
    "k":       FieldDef("lab", "Blutgase arteriell",          r"^KALIUM",           "number_1dp_comma_decimal"),
    "na":      FieldDef("lab", "Blutgase arteriell",          r"^NATRIUM"),
    "sa02":    FieldDef("lab", "Blutgase arteriell",          r"^O2-SAETTIGUNG",    "number_1dp_comma_decimal"),
    "gluc":    FieldDef("lab", "Blutgase arteriell",          r"^GLUCOSE"),
    "lactate": FieldDef("lab", "Blutgase arteriell",          r"^LACTAT"),
    "svo2":    FieldDef("lab", r"Blutgase venös|Blutgase gv", r"^O2-SAETTIGUNG",   "number_1dp_comma_decimal"),
}

_PRE_VENT: Dict[str, FieldDef] = {
    "fi02":          FieldDef("respiratory", ".*", r"^FiO2\s*(\[%\]|in\s*%)"),
    "vent_peep":     FieldDef("respiratory", ".*", r"^s?PEEP\s*\[|^Expirationsdruck\s*\(PEEP\)"),
    "vent_pip":      FieldDef("respiratory", ".*", r"^s?P[Ii][Pp]\s*\[|^Ppeak\s*\[|^s?Pin\s*\[|^insp.*Spitz"),
    "conv_vent_rate":FieldDef("respiratory", ".*", r"mand.*Atemfrequenz|mandator.*Atemfrequenz"),
    "02l":           FieldDef("o2_supply",   ".*", r"^O2\s*l/min"),  # → pre_02l_i / pre_02l
}

# Beatmungsmodus: String-Wert → _map_ventilation_spec() → Integer
_PRE_VENT_SPEC: Dict[str, FieldDef] = {
    "vent_spec": FieldDef("respiratory", ".*", r"^Modus$|^Beatmungsform"),
}

_PRE_HEMO: Dict[str, FieldDef] = {
    "hr":      FieldDef("vitals", ".*",         r"^HF\s*\["),
    "sys_bp":  FieldDef("vitals", ".*",         r"^ABPs\s*\[|^ARTs\s*\["),
    "dia_bp":  FieldDef("vitals", ".*",         r"^ABPd\s*\[|^ARTd\s*\["),
    "mean_bp": FieldDef("vitals", ".*",         r"^ABPm\s*\[|^ARTm\s*\["),
    "cvd":     FieldDef("vitals", ".*",         r"^ZVDm\s*\["),         # cvd, nicht cvp!
    "sp02":    FieldDef("vitals", ".*",         r"^SpO2\s*\[%\]"),
    "pcwp":    FieldDef("vitals", r"^Online.*", r"^PCWP\s*\[|^PAWP\s*\["),
    "sys_pap": FieldDef("vitals", r"^Online.*", r"^PAPs\s*\["),
    "dia_pap": FieldDef("vitals", r"^Online.*", r"^PAPd\s*\["),
    "mean_pap":FieldDef("vitals", r"^Online.*", r"^PAPm\s*\["),
    "ci":      FieldDef("vitals", r"^Online.*", r"^CCI\s*\[|^HZV",      "number_1dp_comma_decimal"),
}

_PRE_GCS: Dict[str, FieldDef] = {
    "gcs": FieldDef("GCS (Jugendliche und Erwachsene)", ".*", r"^Summe GCS2"),
}

_PRE_LAB: Dict[str, FieldDef] = {
    "wbc":    FieldDef("lab", "Blutbild",                    r"^WBC",                "number_1dp_comma_decimal"),
    "hb":     FieldDef("lab", "Blutbild",                    r"^HB \(HGB\)|^HB\b",  "number_1dp_comma_decimal"),
    "hct":    FieldDef("lab", "Blutbild",                    r"^HCT",                "number_1dp_comma_decimal"),
    "mcv":    FieldDef("lab", "Blutbild",                    r"^MCV"),
    "mch":    FieldDef("lab", "Blutbild",                    r"^MCH"),
    "mchc":   FieldDef("lab", "Blutbild",                    r"^MCHC"),
    "ret":    FieldDef("lab", "Blutbild",                    r"^RETIKULOZYTEN"),
    "rpi":    FieldDef("lab", "Blutbild",                    r"^Reti-Produktionsindex"),
    "rdw":    FieldDef("lab", "Blutbild",                    r"^RDW"),
    "plt":    FieldDef("lab", "Blutbild",                    r"^PLT"),
    "ptt":    FieldDef("lab", "Gerinnung",                   r"^PTT",                "number_1dp_comma_decimal"),
    "quick":  FieldDef("lab", "Gerinnung",                   r"^TPZ"),
    "inr":    FieldDef("lab", "Gerinnung",                   r"^INR",                "number_1dp_comma_decimal"),
    "ck":     FieldDef("lab", "Enzyme",                      r"^CK \[|^CK$"),
    "ckmb":   FieldDef("lab", "Enzyme",                      r"^CK-MB"),
    "got":    FieldDef("lab", "Enzyme",                      r"^GOT"),
    "ldh":    FieldDef("lab", "Enzyme",                      r"^LDH"),
    "lipase": FieldDef("lab", "Enzyme",                      r"^LIPASE",             "number_1dp_comma_decimal"),
    "crea":   FieldDef("lab", r"Klinische Chemie|Retention", r"^KREATININ",          "number_1dp_comma_decimal"),
    "urea":   FieldDef("lab", r"Klinische Chemie|Retention", r"^HARNSTOFF",          "number_1dp_comma_decimal"),
    "cc":     FieldDef("lab", r"Klinische Chemie|Retention", r"^GFRKREA",            "number_2dp_comma_decimal"),
    "alb":    FieldDef("lab", r"Klinische Chemie|Proteine",  r"^ALBUMIN",            "number_1dp_comma_decimal"),
    "crp":    FieldDef("lab", r"Klinische Chemie|Proteine",  r"^CRP",                "number_1dp_comma_decimal"),
    "pct":    FieldDef("lab", r"Klinische Chemie|Proteine",  r"^PROCALCITONIN",      "number_2dp_comma_decimal"),
    "act":    FieldDef("act", ".*",                          r"^ACT"),
    "fhb":    FieldDef("lab", r"Blutbild|Klinische Chemie",  r"^FREIES HB",          "number_1dp_comma_decimal"),
    "hapto":  FieldDef("lab", r"Klinische Chemie|Proteine",  r"^HAPTOGLOBIN",        "number_1dp_comma_decimal"),
    "bili":   FieldDef("lab", "Klinische Chemie",            r"^BILI",               "number_2dp_comma_decimal"),
    "trop":   FieldDef("lab", r"Enzyme|Klinische Chemie",    r"^Troponin|^HS-TROP"),
    "alat":   FieldDef("lab", "Enzyme",                      r"^GPT"),
}

# --- Generierte Registries: Pre-Impella (Suffix _i) ---
PRE_IMPELLA_BGA_REGISTRY:       Dict[str, FieldDef] = {f"pre_{k}_i": v for k, v in _PRE_BGA.items()}
PRE_IMPELLA_VENT_REGISTRY:      Dict[str, FieldDef] = {f"pre_{k}_i": v for k, v in _PRE_VENT.items()}
PRE_IMPELLA_VENT_SPEC_REGISTRY: Dict[str, FieldDef] = {f"pre_{k}_i": v for k, v in _PRE_VENT_SPEC.items()}
PRE_IMPELLA_HEMO_REGISTRY:      Dict[str, FieldDef] = {f"pre_{k}_i": v for k, v in _PRE_HEMO.items()}
PRE_IMPELLA_GCS_REGISTRY:       Dict[str, FieldDef] = {f"pre_{k}_i": v for k, v in _PRE_GCS.items()}
PRE_IMPELLA_LAB_REGISTRY:       Dict[str, FieldDef] = {f"pre_{k}_i": v for k, v in _PRE_LAB.items()}

# --- Generierte Registries: Pre-VAECLS (kein Suffix) ---
PRE_VAECLS_BGA_REGISTRY:       Dict[str, FieldDef] = {f"pre_{k}": v for k, v in _PRE_BGA.items()}
PRE_VAECLS_VENT_REGISTRY:      Dict[str, FieldDef] = {f"pre_{k}": v for k, v in _PRE_VENT.items()}
PRE_VAECLS_VENT_SPEC_REGISTRY: Dict[str, FieldDef] = {f"pre_{k}": v for k, v in _PRE_VENT_SPEC.items()}
PRE_VAECLS_HEMO_REGISTRY:      Dict[str, FieldDef] = {f"pre_{k}": v for k, v in _PRE_HEMO.items()}
PRE_VAECLS_GCS_REGISTRY:       Dict[str, FieldDef] = {f"pre_{k}": v for k, v in _PRE_GCS.items()}
PRE_VAECLS_LAB_REGISTRY:       Dict[str, FieldDef] = {f"pre_{k}": v for k, v in _PRE_LAB.items()}


# =============================================================================
# MEDIKAMENTEN-CHECKBOXEN & SPEZIAL-MAPPINGS
# (Nicht-extrahierbar: Presence-Checks, keine Regex-auf-Wert-Extraktion)
# =============================================================================

VASOACTIVE_SPEC_MAP: Dict[int, str] = {
    1:  r"Dobutamin",
    2:  r"Dopamin",
    3:  r"Enoximon",
    4:  r"(?<!Nor)Epinephrin|^Suprarenin",
    5:  r"Esmolol",
    6:  r"Levosimendan|Simdax",
    7:  r"Metaraminol|Aramino",
    8:  r"Metoprolol|Beloc",
    9:  r"Milrinone|Corotrop",
    10: r"Nicardipin",
    11: r"Nitroglycerin|Nitro",
    12: r"Nitroprussid",
    13: r"(?<!o)Norepinephrin|^Arterenol",
    14: r"Phenylephrin",
    15: r"Tolazolin",
    16: r"Vasopressin|Empressin",
}

VENT_SPEC_MAP: Dict[str, Optional[str]] = {
    "CPAP":        "SPN_CPAP_PS",
    "CPAP_PS":     "CPAP_PS",
    "SPN_CPAP":    "SPN_CPAP_PS",
    "SPN_CPAP_PS": "SPN_CPAP_PS",
    "BILEVEL":     "BiLevel",
    "BI_LEVEL":    "BiLevel",
    "BILEVEL_VG":  "BiLevel_VG",
    "BIPAP":       "BIPAP",
    "PC_BIPAP":    "PC_BIPAP",
    "SIMV":        "SIMV",
    "SIMV_PC":     "SIMV_PC",
    "SIMV_VC":     "SIMV_VC",
    "PC_SIMV":     "PC_SIMV",
    "VC_SIMV":     "VC_SIMV",
    "A_C_VC":      "A_C_VC",
    "A_C_PC":      "A_C_PC",
    "A_C_PRVC":    "A_C_PRVC",
    "AC_VC":       "A_C_VC",
    "AC_PC":       "A_C_PC",
    "PC_CMV":      "PC_CMV",
    "PC_PSV":      "PC_PSV",
    "PC_AC":       "PC_AC",
    "PC_PC_APRV":  "PC_PC_APRV",
    "APRV":        "PC_PC_APRV",
    "IPPV":        "IPPV",
    "VC_CMV":      "VC_CMV",
    "VC_AC":       "VC_AC",
    "VC_MMV":      "VC_MMV",
    "SPONTANEOUS": "SPN_CPAP_PS",
    "SPONT":       "SPN_CPAP_PS",
    "ASB":         "ASB",
    "NIV":         "NIV",
    "SBT":         "SBT",
    "STANDBY":     None,
}

ANTICOAGULANT_MAP: Dict[int, str] = {
    1: r"Heparin",
    2: r"Argatroban|Argatra",
}

ANTIPLATELET_MAP: Dict[int, str] = {
    1: r"Aspirin|ASS|Aspisol",
    2: r"Plavix|Clopidogrel",
    3: r"Ticagrelor|Brilique",
    4: r"Prasugrel|Efient",
}

ANTIBIOTIC_MAP: Dict[int, str] = {
    1:  r"Cefuroxim|Zinacef|Zinnat",
    2:  r"Piperacillin|Tazobactam|Pip/Taz|Tazobac",
    3:  r"Meropenem|Meronem",
    4:  r"Vancomycin|Vanco",
    5:  r"Vancomycin.*p\.o\.|Vanco.*p\.o\.",
    6:  r"Linezolid|Zyvoxid",
    7:  r"Daptomycin|Cubicin",
    8:  r"Penicillin G|Penicillin",
    9:  r"Flucloxacillin|Staphylex",
    10: r"Rifampicin|Eremfat",
    11: r"Gentamicin|Refobacin",
    12: r"Tobramycin|Gernebacin",
    13: r"Ciprofloxacin|Cipro",
    15: r"Erythromycin|Erythrocin",
    16: r"Caspofungin|Cancidas",
    17: r"Amphotericin B|Ampho-Moronal|Ambisome",
    18: r"Metronidazol|Clont|Arilin",
    19: r"Cefazolin|Gramaxin",
    20: r"Ceftriaxon|Rocephin",
}

MEDICATION_SPEC_MAP: Dict[int, str] = {
    1:  r"Alprostadil|Prostin",
    2:  r"Bicarbonat|Bicarb",
    3:  r"Prostacyclin|Iloprost|Ventavis|Remodulin|Flolan",
    4:  r"Propofol|Midazolam|Ketamin|Dexmedetomidin|Dexmetomidin|Dormicum|Esketamin|Ketanest|Dexdor|Disoprivan|Thiopental|SEDALAM",
    5:  r"Rocuronium|Pancuronium|Atracurium|Cisatracurium|Esmeron|Nimbex",
    6:  r"Sildenafil|Revatio|Viagra",
    7:  r"Hydrocortison|Dexamethason|Prednisolon|Methylprednisolon|Solu-Decortin|Fortecortin|Urbason",
    8:  r"Trometamol|THAM|Tris",
    10: r"Sufentanil|Fentanyl|Remifentanil|Morphin|Piritramid|Dipidolor|Oxycodon|Oxygesic|Targin|Oxycontin",
    11: r"Haloperidol|Quetiapin|Risperidon|Haldol|Seroquel|Pipamperon|Dipiperon",
}

NARCOTICS_SPEC_MAP: Dict[int, str] = {
    1: r"Propofol|Disoprivan",
    2: r"Midazolam|Dormicum|SEDALAM",
    3: r"Ketamin|Esketamin|Ketanest",
    4: r"Dexmedetomidin|Dexmetomidin|Dexdor",
}


# =============================================================================
# SOURCE MAPPING
# Logischer Quellenname → Liste von source_type-Werten im DataFrame
# "__CONTAINS__" = contains-Suche statt exakter Übereinstimmung (für Impella)
# =============================================================================
SOURCE_MAPPING: Dict[str, Any] = {
    "lab":       ["Lab"],
    "vitals":    ["Vitals", "Vitalparameter (manuell)"],
    "medication":["Medikation", "Medication"],
    "ecmo":      ["ECMO"],
    "impella":   "__CONTAINS__",
    "crrt":      ["HÄMOFILTER", "CRRT"],
    "respiratory": [
        "Beatmung",
        "Tubus/Beatmung",
        "NIV-Beatmungsprotokoll manuell",
        "NIV-Maskenbeatmung",
        "Aktivitäten Beatmung",
        "Erfassung der Beatmungszeit",
        "Respiratory",
    ],
    "o2_supply": ["O2 Gabe"],
    "fluidbalance": ["Fluidbalance", "Bilanz"],
    "nirs":      ["NIRS"],
    "patient_info": ["PatientInfo"],
    "Richmond-Agitation-Sedation":      ["Richmond-Agitation-Sedation"],
    "GCS (Jugendliche und Erwachsene)": ["GCS (Jugendliche und Erwachsene)"],
    "act":       ["ACT"],
}


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
})
