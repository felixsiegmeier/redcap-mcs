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
    "pco2":    FieldDef("lab", "Blutgase arteriell",          r"^PCO2",             "number_1dp_comma_decimal", "15,0", "120,0"),
    "p02":     FieldDef("lab", "Blutgase arteriell",          r"^PO2",              "number_1dp_comma_decimal", "20,0", "600,0"),
    "ph":      FieldDef("lab", "Blutgase arteriell",          r"^PH$|^PH ",         "number_2dp_comma_decimal", "6,80", "7,70"),
    "hco3":    FieldDef("lab", "Blutgase arteriell",          r"^HCO3",             "number_1dp_comma_decimal", "5,0", "50,0"),
    "be":      FieldDef("lab", "Blutgase arteriell",          r"^ABEc",             "number_1dp_comma_decimal", "-25,0", "25,0"),
    "k":       FieldDef("lab", "Blutgase arteriell",          r"^KALIUM",           "number_1dp_comma_decimal", "1,5", "9,0"),
    "na":      FieldDef("lab", "Blutgase arteriell",          r"^NATRIUM",          "number", "110", "160"),
    "sa02":    FieldDef("lab", "Blutgase arteriell",          r"^O2-SAETTIGUNG",    "number_1dp_comma_decimal", "30,0", "100,0"),
    "gluc":    FieldDef("lab", "Blutgase arteriell",          r"^GLUCOSE",          "number", "20", "500"),
    "lactate": FieldDef("lab", "Blutgase arteriell",          r"^LACTAT",           "number", "1", "250"),
    "svo2":    FieldDef("lab", r"Blutgase venös|Blutgase gv", r"^O2-SAETTIGUNG",   "number_1dp_comma_decimal", "15,0", "100,0"),
}

_PRE_VENT: Dict[str, FieldDef] = {
    "fi02":          FieldDef("respiratory", ".*", r"^FiO2\s*(\[%\]|in\s*%)",                            "number", "20", "100"),
    "vent_peep":     FieldDef("respiratory", ".*", r"^s?PEEP\s*\[|^Expirationsdruck\s*\(PEEP\)",         "number", "1", "30"),
    "vent_pip":      FieldDef("respiratory", ".*", r"^s?P[Ii][Pp]\s*\[|^Ppeak\s*\[|^s?Pin\s*\[|^insp.*Spitz", "number", "1", "40"),
    "conv_vent_rate":FieldDef("respiratory", ".*", r"mand.*Atemfrequenz|mandator.*Atemfrequenz",          "number", "1", "30"),
    "02l":           FieldDef("o2_supply",   ".*", r"^O2\s*l/min",                                       "number", "0", "20"),  # → pre_02l_i / pre_02l
}

# Beatmungsmodus: String-Wert → _map_ventilation_spec() → Integer
_PRE_VENT_SPEC: Dict[str, FieldDef] = {
    "vent_spec": FieldDef("respiratory", ".*", r"^Modus$|^Beatmungsform", "", "", ""),
}

_PRE_HEMO: Dict[str, FieldDef] = {
    "hr":      FieldDef("vitals", ".*",         r"^HF\s*\[",                       "number", "10", "200"),
    "sys_bp":  FieldDef("vitals", ".*",         r"^ABPs\s*\[|^ARTs\s*\[",          "number", "20", "250"),
    "dia_bp":  FieldDef("vitals", ".*",         r"^ABPd\s*\[|^ARTd\s*\[",          "number", "20", "200"),
    "mean_bp": FieldDef("vitals", ".*",         r"^ABPm\s*\[|^ARTm\s*\[",          "number", "20", "200"),
    "cvd":     FieldDef("vitals", ".*",         r"^ZVDm\s*\[",                     "integer", "0", "30"),  # cvd, nicht cvp!
    "sp02":    FieldDef("vitals", ".*",         r"^SpO2\s*\[%\]",                  "number_1dp_comma_decimal", "20", "100"),
    "pcwp":    FieldDef("vitals", r"^Online.*", r"^PCWP\s*\[|^PAWP\s*\[", "number", "0", "25"),
    "sys_pap": FieldDef("vitals", r"^Online.*", r"^PAPs\s*\[", "number", "0", "100"),
    "dia_pap": FieldDef("vitals", r"^Online.*", r"^PAPd\s*\[", "number", "0", "80"),
    "mean_pap":FieldDef("vitals", r"^Online.*", r"^PAPm\s*\[", "number", "0", "80"),
    "ci":      FieldDef("vitals", r"^Online.*", r"^CCI\s*\[|^HZV", "number_1dp_comma_decimal", "0,1", "7,0"),
}

_PRE_GCS: Dict[str, FieldDef] = {
    "gcs": FieldDef("GCS (Jugendliche und Erwachsene)", ".*", r"^Summe GCS2", "number", "3", "15"),
}

_PRE_LAB: Dict[str, FieldDef] = {
    "wbc":    FieldDef("lab", "Blutbild", r"^WBC", "number_1dp_comma_decimal", "0,1", "30,0"),
    "hb":     FieldDef("lab", "Blutbild",                    r"^HB \(HGB\)|^HB\b",  "number_1dp_comma_decimal", "4,5", "20,0"),
    "hct":    FieldDef("lab", "Blutbild", r"^HCT", "number_1dp_comma_decimal", "20,0", "60,0"),
    "mcv":    FieldDef("lab", "Blutbild",                    r"^MCV",                "number_1dp_comma_decimal", "70,0", "99,0"),
    "mch":    FieldDef("lab", "Blutbild",                    r"^MCH",                "number_1dp_comma_decimal", "20,0", "40,0"),
    "mchc":   FieldDef("lab", "Blutbild",                    r"^MCHC",               "number_1dp_comma_decimal", "30,0", "40,0"),
    "ret":    FieldDef("lab", "Blutbild",                    r"^RETIKULOZYTEN",       "number", "", ""),
    "rpi":    FieldDef("lab", "Blutbild",                    r"^Reti-Produktionsindex","number", "", ""),
    "rdw":    FieldDef("lab", "Blutbild",                    r"^RDW",                "number_1dp_comma_decimal", "10,0", "15,0"),
    "plt":    FieldDef("lab", "Blutbild", r"^PLT", "number", "1", "800"),
    "ptt":    FieldDef("lab", "Gerinnung", r"^PTT", "number_1dp_comma_decimal", "22,0", "180,0"),
    "quick":  FieldDef("lab", "Gerinnung", r"^TPZ", "number", "1", "100"),
    "inr":    FieldDef("lab", "Gerinnung", r"^INR", "number_1dp_comma_decimal", "1,0", "8,0"),
    "ck":     FieldDef("lab", "Enzyme", r"^CK \[|^CK$", "number", "0", "20000"),
    "ckmb":   FieldDef("lab", "Enzyme", r"^CK-MB", "number", "0", "700"),
    "got":    FieldDef("lab", "Enzyme", r"^GOT", "number", "1", "10000"),
    "ldh":    FieldDef("lab", "Enzyme", r"^LDH", "number", "1", "20000"),
    "lipase": FieldDef("lab", "Enzyme", r"^LIPASE", "number_1dp_comma_decimal", "4,0", "200,0"),
    "crea":   FieldDef("lab", r"Klinische Chemie|Retention", r"^KREATININ", "number_1dp_comma_decimal", "0,1", "7,0"),
    "urea":   FieldDef("lab", r"Klinische Chemie|Retention", r"^HARNSTOFF", "number_1dp_comma_decimal", "10,0", "300,0"),
    "cc":     FieldDef("lab", r"Klinische Chemie|Retention", r"^GFRKREA", "number_2dp_comma_decimal", "1,00", "150,00"),
    "alb":    FieldDef("lab", r"Klinische Chemie|Proteine",  r"^ALBUMIN",            "number_1dp_comma_decimal", "1,0", "10,0"),
    "crp":    FieldDef("lab", r"Klinische Chemie|Proteine", r"^CRP", "number_1dp_comma_decimal", "1,0", "50,0"),
    "pct":    FieldDef("lab", r"Klinische Chemie|Proteine", r"^PROCALCITONIN", "number_2dp_comma_decimal", "0,00", "10,00"),
    "act":    FieldDef("act", ".*", r"^ACT", "number", "90", "800"),
    "fhb":    FieldDef("lab", r"Blutbild|Klinische Chemie", r"^FREIES HB", "number_2dp_comma_decimal", "0,0", "200,0"),
    "hapto":  FieldDef("lab", r"Klinische Chemie|Proteine", r"^HAPTOGLOBIN", "number_1dp_comma_decimal", "8,0", "300,0"),
    "bili":   FieldDef("lab", "Klinische Chemie", r"^BILI", "number_1dp_comma_decimal", "0,00", "40,00"),
    "trop":   FieldDef("lab", r"Enzyme|Klinische Chemie",    r"^Troponin|^HS-TROP",  "number", "", ""),
    "alat":   FieldDef("lab", "Enzyme",                      r"^GPT",                "", "", ""),
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
