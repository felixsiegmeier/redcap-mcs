from typing import Dict

from ._base import FieldDef


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
    "mcv":     FieldDef("lab", "Blutbild", r"^MCV",                                   "number"),
    "mch":     FieldDef("lab", "Blutbild", r"^MCH",                                   "number"),
    "mchc":    FieldDef("lab", "Blutbild", r"^MCHC",                                  "number"),
    "rdw":     FieldDef("lab", "Blutbild", r"^RDW",                                   "number"),
    "ret":     FieldDef("lab", "Blutbild", r"^RETIKULOZYTEN",                         "number"),
    "rpi":     FieldDef("lab", "Blutbild", r"^Reti-Produktionsindex",                 "number"),
    "plt":     FieldDef("lab", "Blutbild", r"^PLT",                                   "number"),
    "fhb":     FieldDef("lab", r"Blutbild|Klinische Chemie", r"^FREIES HB",           "number_1dp_comma_decimal"),
    # Gerinnung
    "ptt":     FieldDef("lab", "Gerinnung", r"^PTT",                                  "number_1dp_comma_decimal"),
    "quick":   FieldDef("lab", "Gerinnung", r"^TPZ",                                  "number"),
    "inr":     FieldDef("lab", "Gerinnung", r"^INR",                                  "number_1dp_comma_decimal"),
    "act":     FieldDef("act", ".*",        r"^ACT",                                  "number"),
    # Enzyme
    "ck":      FieldDef("lab", "Enzyme", r"^CK \[|^CK$",                              "number"),
    "ckmb":    FieldDef("lab", "Enzyme", r"^CK-MB",                                   "number"),
    "ggt":     FieldDef("lab", "Enzyme", r"^GGT",                                     "number"),
    "ldh":     FieldDef("lab", "Enzyme", r"^LDH",                                     "number"),
    "lipase":  FieldDef("lab", "Enzyme", r"^LIPASE",                                  "number_1dp_comma_decimal"),
    "got":     FieldDef("lab", "Enzyme", r"^GOT",                                     "number"),
    "alat":    FieldDef("lab", "Enzyme", r"^GPT",                                     "number"),
    "trop":    FieldDef("lab", r"Enzyme|Klinische Chemie", r"^Troponin|^HS-TROP",     "number"),
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
