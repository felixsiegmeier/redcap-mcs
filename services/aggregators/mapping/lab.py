from typing import Dict

from ._base import FieldDef


# =============================================================================
# LABOR  (instrument: labor, repeating)
# =============================================================================
LAB_REGISTRY: Dict[str, FieldDef] = {
    # Blutgase arteriell
    "pc02":    FieldDef("lab", "Blutgase arteriell", r"^PCO2", "number_1dp_comma_decimal", "15,0", "120,0"),
    "p02":     FieldDef("lab", "Blutgase arteriell", r"^PO2", "number_1dp_comma_decimal", "20,0", "600,0"),
    "ph":      FieldDef("lab", "Blutgase arteriell", r"^PH$|^PH ", "number_2dp_comma_decimal", "6,80", "7,70"),
    "hco3":    FieldDef("lab", "Blutgase arteriell", r"^HCO3", "number_1dp_comma_decimal", "5,0", "50,0"),
    "be":      FieldDef("lab", "Blutgase arteriell", r"^ABEc", "number_1dp_comma_decimal", "-25,0", "25,0"),
    "sa02":    FieldDef("lab", "Blutgase arteriell", r"^O2-SAETTIGUNG", "number_1dp_comma_decimal", "30,0", "100,0"),
    "k":       FieldDef("lab", "Blutgase arteriell", r"^KALIUM", "number_1dp_comma_decimal", "1,5", "9,0"),
    "na":      FieldDef("lab", "Blutgase arteriell", r"^NATRIUM", "number", "110", "160"),
    "gluc":    FieldDef("lab", "Blutgase arteriell", r"^GLUCOSE", "number", "20", "500"),
    "lactate": FieldDef("lab", "Blutgase arteriell", r"^LACTAT", "number", "1", "250"),
    # Blutgase venös (inkl. gemischt-venös)
    "sv02":    FieldDef("lab", r"Blutgase venös|Blutgase gv", r"^O2-SAETTIGUNG", "number_1dp_comma_decimal", "15,0", "100,0"),
    # Hämatologie / Blutbild
    "wbc":     FieldDef("lab", "Blutbild", r"^WBC", "number_1dp_comma_decimal", "0,1", "30,0"),
    "hb":      FieldDef("lab", "Blutbild", r"^HB \(HGB\)|^HB\b", "number_1dp_comma_decimal", "4,5", "20,0"),
    "hct":     FieldDef("lab", "Blutbild", r"^HCT", "number_1dp_comma_decimal", "20,0", "60,0"),
    "mcv":     FieldDef("lab", "Blutbild", r"^MCV", "number", "", ""),
    "mch":     FieldDef("lab", "Blutbild", r"^MCH", "number", "", ""),
    "mchc":    FieldDef("lab", "Blutbild", r"^MCHC", "number", "", ""),
    "rdw":     FieldDef("lab", "Blutbild", r"^RDW", "number", "", ""),
    "ret":     FieldDef("lab", "Blutbild", r"^RETIKULOZYTEN", "number", "", ""),
    "rpi":     FieldDef("lab", "Blutbild", r"^Reti-Produktionsindex", "number", "", ""),
    "plt":     FieldDef("lab", "Blutbild", r"^PLT", "number", "1", "800"),
    "fhb":     FieldDef("lab", r"Blutbild|Klinische Chemie", r"^FREIES HB", "number_1dp_comma_decimal", "0,0", "200,0"),
    # Gerinnung
    "ptt":     FieldDef("lab", "Gerinnung", r"^PTT", "number_1dp_comma_decimal", "22,0", "180,0"),
    "quick":   FieldDef("lab", "Gerinnung", r"^TPZ", "number", "1", "100"),
    "inr":     FieldDef("lab", "Gerinnung", r"^INR", "number_1dp_comma_decimal", "1,0", "8,0"),
    "act":     FieldDef("act", ".*", r"^ACT", "number", "90", "800"),
    # Enzyme
    "ck":      FieldDef("lab", "Enzyme", r"^CK \[|^CK$", "number", "0", "20000"),
    "ckmb":    FieldDef("lab", "Enzyme", r"^CK-MB", "number", "0", "700"),
    "ggt":     FieldDef("lab", "Enzyme", r"^GGT", "", "", ""),
    "ldh":     FieldDef("lab", "Enzyme", r"^LDH", "number", "1", "20000"),
    "lipase":  FieldDef("lab", "Enzyme", r"^LIPASE", "number_1dp_comma_decimal", "4,0", "200,0"),
    "got":     FieldDef("lab", "Enzyme", r"^GOT", "number", "1", "10000"),
    "alat":    FieldDef("lab", "Enzyme", r"^GPT", "", "", ""),
    "trop":    FieldDef("lab", r"Enzyme|Klinische Chemie", r"^Troponin|^HS-TROP", "number", "", ""),
    # Klinische Chemie
    "pct":     FieldDef("lab", r"Klinische Chemie|Proteine", r"^PROCALCITONIN", "number_2dp_comma_decimal", "0,00", "10,00"),
    "crp":     FieldDef("lab", r"Klinische Chemie|Proteine", r"^CRP", "number_1dp_comma_decimal", "1,0", "50,0"),
    "bili":    FieldDef("lab", "Klinische Chemie", r"^BILI", "number_2dp_comma_decimal", "0,00", "40,00"),
    "crea":    FieldDef("lab", r"Klinische Chemie|Retention", r"^KREATININ", "number_1dp_comma_decimal", "0,1", "7,0"),
    "urea":    FieldDef("lab", r"Klinische Chemie|Retention", r"^HARNSTOFF", "number_1dp_comma_decimal", "10,0", "300,0"),
    "cc":      FieldDef("lab", r"Klinische Chemie|Retention", r"^GFRKREA", "number_2dp_comma_decimal", "1,00", "150,00"),
    "albumin": FieldDef("lab", r"Klinische Chemie|Proteine", r"^ALBUMIN", "number_1dp_comma_decimal", "0,1", "6,0"),
    "hapto":   FieldDef("lab", r"Klinische Chemie|Proteine", r"^HAPTOGLOBIN", "number_1dp_comma_decimal", "8,0", "300,0"),
}
