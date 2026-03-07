from typing import Dict

from ._base import FieldDef


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
    "na":      FieldDef("lab", "Blutgase arteriell",          r"^NATRIUM",          "number"),
    "sa02":    FieldDef("lab", "Blutgase arteriell",          r"^O2-SAETTIGUNG",    "number_1dp_comma_decimal"),
    "gluc":    FieldDef("lab", "Blutgase arteriell",          r"^GLUCOSE",          "number"),
    "lactate": FieldDef("lab", "Blutgase arteriell",          r"^LACTAT",           "number"),
    "svo2":    FieldDef("lab", r"Blutgase venös|Blutgase gv", r"^O2-SAETTIGUNG",   "number_1dp_comma_decimal"),
}

_PRE_VENT: Dict[str, FieldDef] = {
    "fi02":          FieldDef("respiratory", ".*", r"^FiO2\s*(\[%\]|in\s*%)",                            "number"),
    "vent_peep":     FieldDef("respiratory", ".*", r"^s?PEEP\s*\[|^Expirationsdruck\s*\(PEEP\)",         "number"),
    "vent_pip":      FieldDef("respiratory", ".*", r"^s?P[Ii][Pp]\s*\[|^Ppeak\s*\[|^s?Pin\s*\[|^insp.*Spitz", "number"),
    "conv_vent_rate":FieldDef("respiratory", ".*", r"mand.*Atemfrequenz|mandator.*Atemfrequenz",          "number"),
    "02l":           FieldDef("o2_supply",   ".*", r"^O2\s*l/min",                                       "number"),  # → pre_02l_i / pre_02l
}

# Beatmungsmodus: String-Wert → _map_ventilation_spec() → Integer
_PRE_VENT_SPEC: Dict[str, FieldDef] = {
    "vent_spec": FieldDef("respiratory", ".*", r"^Modus$|^Beatmungsform", "number"),
}

_PRE_HEMO: Dict[str, FieldDef] = {
    "hr":      FieldDef("vitals", ".*",         r"^HF\s*\[",                       "number"),
    "sys_bp":  FieldDef("vitals", ".*",         r"^ABPs\s*\[|^ARTs\s*\[",          "number"),
    "dia_bp":  FieldDef("vitals", ".*",         r"^ABPd\s*\[|^ARTd\s*\[",          "number"),
    "mean_bp": FieldDef("vitals", ".*",         r"^ABPm\s*\[|^ARTm\s*\[",          "number"),
    "cvd":     FieldDef("vitals", ".*",         r"^ZVDm\s*\[",                     "number"),  # cvd, nicht cvp!
    "sp02":    FieldDef("vitals", ".*",         r"^SpO2\s*\[%\]",                  "number_1dp_comma_decimal"),
    "pcwp":    FieldDef("vitals", r"^Online.*", r"^PCWP\s*\[|^PAWP\s*\[",         "number"),
    "sys_pap": FieldDef("vitals", r"^Online.*", r"^PAPs\s*\[",                     "number"),
    "dia_pap": FieldDef("vitals", r"^Online.*", r"^PAPd\s*\[",                     "number"),
    "mean_pap":FieldDef("vitals", r"^Online.*", r"^PAPm\s*\[",                     "number"),
    "ci":      FieldDef("vitals", r"^Online.*", r"^CCI\s*\[|^HZV",                "number_1dp_comma_decimal"),
}

_PRE_GCS: Dict[str, FieldDef] = {
    "gcs": FieldDef("GCS (Jugendliche und Erwachsene)", ".*", r"^Summe GCS2", "number"),
}

_PRE_LAB: Dict[str, FieldDef] = {
    "wbc":    FieldDef("lab", "Blutbild",                    r"^WBC",                "number_1dp_comma_decimal"),
    "hb":     FieldDef("lab", "Blutbild",                    r"^HB \(HGB\)|^HB\b",  "number_1dp_comma_decimal"),
    "hct":    FieldDef("lab", "Blutbild",                    r"^HCT",                "number_1dp_comma_decimal"),
    "mcv":    FieldDef("lab", "Blutbild",                    r"^MCV",                "number_1dp_comma_decimal"),
    "mch":    FieldDef("lab", "Blutbild",                    r"^MCH",                "number_1dp_comma_decimal"),
    "mchc":   FieldDef("lab", "Blutbild",                    r"^MCHC",               "number_1dp_comma_decimal"),
    "ret":    FieldDef("lab", "Blutbild",                    r"^RETIKULOZYTEN",       "number"),
    "rpi":    FieldDef("lab", "Blutbild",                    r"^Reti-Produktionsindex","number"),
    "rdw":    FieldDef("lab", "Blutbild",                    r"^RDW",                "number_1dp_comma_decimal"),
    "plt":    FieldDef("lab", "Blutbild",                    r"^PLT",                "number"),
    "ptt":    FieldDef("lab", "Gerinnung",                   r"^PTT",                "number_1dp_comma_decimal"),
    "quick":  FieldDef("lab", "Gerinnung",                   r"^TPZ",                "number"),
    "inr":    FieldDef("lab", "Gerinnung",                   r"^INR",                "number_1dp_comma_decimal"),
    "ck":     FieldDef("lab", "Enzyme",                      r"^CK \[|^CK$",         "number"),
    "ckmb":   FieldDef("lab", "Enzyme",                      r"^CK-MB",              "number"),
    "got":    FieldDef("lab", "Enzyme",                      r"^GOT",                "number"),
    "ldh":    FieldDef("lab", "Enzyme",                      r"^LDH",                "number"),
    "lipase": FieldDef("lab", "Enzyme",                      r"^LIPASE",             "number_1dp_comma_decimal"),
    "crea":   FieldDef("lab", r"Klinische Chemie|Retention", r"^KREATININ",          "number_1dp_comma_decimal"),
    "urea":   FieldDef("lab", r"Klinische Chemie|Retention", r"^HARNSTOFF",          "number_1dp_comma_decimal"),
    "cc":     FieldDef("lab", r"Klinische Chemie|Retention", r"^GFRKREA",            "number_2dp_comma_decimal"),
    "alb":    FieldDef("lab", r"Klinische Chemie|Proteine",  r"^ALBUMIN",            "number_1dp_comma_decimal"),
    "crp":    FieldDef("lab", r"Klinische Chemie|Proteine",  r"^CRP",                "number_1dp_comma_decimal"),
    "pct":    FieldDef("lab", r"Klinische Chemie|Proteine",  r"^PROCALCITONIN",      "number_2dp_comma_decimal"),
    "act":    FieldDef("act", ".*",                          r"^ACT",                "number"),
    "fhb":    FieldDef("lab", r"Blutbild|Klinische Chemie",  r"^FREIES HB",          "number_1dp_comma_decimal"),
    "hapto":  FieldDef("lab", r"Klinische Chemie|Proteine",  r"^HAPTOGLOBIN",        "number_1dp_comma_decimal"),
    "bili":   FieldDef("lab", "Klinische Chemie",            r"^BILI",               "number_2dp_comma_decimal"),
    "trop":   FieldDef("lab", r"Enzyme|Klinische Chemie",    r"^Troponin|^HS-TROP",  "number"),
    "alat":   FieldDef("lab", "Enzyme",                      r"^GPT",                "number"),
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
