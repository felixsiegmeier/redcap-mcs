"""
Zentrales Mapping von Rohdaten-Parametern zu REDCap-Feldern.

Diese Datei enthält alle Regex-basierten Mappings für die verschiedenen
Aggregatoren. Dies erleichtert die Wartung, wenn sich Parameternamen
in den Quelldaten oder Feldnamen in REDCap ändern.
"""

from typing import Dict, Tuple, Optional

# =============================================================================
# LABOR MAPPING (LabAggregator)
# Mapping: LabModel-Feld -> (Source-Type, Kategorie-Pattern, Parameter-Pattern)
# =============================================================================
LAB_FIELD_MAP: Dict[str, Tuple[str, str, str]] = {
    # Blutgase arteriell
    "pc02": ("Lab", "Blutgase arteriell", r"^PCO2"),
    "p02": ("Lab", "Blutgase arteriell", r"^PO2"),
    "ph": ("Lab", "Blutgase arteriell", r"^PH$|^PH "),
    "hco3": ("Lab", "Blutgase arteriell", r"^HCO3"),
    "be": ("Lab", "Blutgase arteriell", r"^ABEc"),
    "sa02": ("Lab", "Blutgase arteriell", r"^O2-SAETTIGUNG"),
    "k": ("Lab", "Blutgase arteriell", r"^KALIUM"),
    "na": ("Lab", "Blutgase arteriell", r"^NATRIUM"),
    "gluc": ("Lab", "Blutgase arteriell", r"^GLUCOSE"),
    "lactate": ("Lab", "Blutgase arteriell", r"^LACTAT"),
    # Blutgase venös
    "sv02": ("Lab", "Blutgase venös", r"^O2-SAETTIGUNG"),
    # Hämatologie / Blutbild
    "wbc": ("Lab", "Blutbild", r"^WBC"),
    "hb": ("Lab", "Blutbild", r"^HB \(HGB\)|^HB\b"),
    "hct": ("Lab", "Blutbild", r"^HCT"),
    "plt": ("Lab", "Blutbild", r"^PLT"),
    "fhb": ("Lab", "Blutbild|Klinische Chemie", r"^FREIES HB"),
    # Gerinnung
    "ptt": ("Lab", "Gerinnung", r"^PTT"),
    "quick": ("Lab", "Gerinnung", r"^TPZ"),
    "inr": ("Lab", "Gerinnung", r"^INR"),
    "act": ("ACT", ".*", r"^ACT"),  # eigener source_type
    # Enzyme
    "ck": ("Lab", "Enzyme", r"^CK \[|^CK$"),
    "ckmb": ("Lab", "Enzyme", r"^CK-MB"),
    "ggt": ("Lab", "Enzyme", r"^GGT"),
    "ldh": ("Lab", "Enzyme", r"^LDH"),
    "lipase": ("Lab", "Enzyme", r"^LIPASE"),
    "got": ("Lab", "Enzyme", r"^GOT"),
    "alat": ("Lab", "Enzyme", r"^GPT"),
    # Klinische Chemie
    "pct": ("Lab", "Klinische Chemie|Proteine", r"^PROCALCITONIN"),
    "crp": ("Lab", "Klinische Chemie|Proteine", r"^CRP"),
    "bili": ("Lab", "Klinische Chemie", r"^BILI"),
    "crea": ("Lab", "Klinische Chemie|Retention", r"^KREATININ"),
    "urea": ("Lab", "Klinische Chemie|Retention", r"^HARNSTOFF"),
    "cc": ("Lab", "Klinische Chemie|Retention", r"^GFRKREA"),
    "albumin": ("Lab", "Klinische Chemie|Proteine", r"^ALBUMIN"),
    "hapto": ("Lab", "Klinische Chemie|Proteine", r"^HAPTOGLOBIN"),
}

# =============================================================================
# HÄMODYNAMIK & BEATMUNG MAPPING (HemodynamicsAggregator)
# Mapping: Model-Feld -> (Source-Type, Category-Pattern, Parameter-Pattern)
# =============================================================================
HEMODYNAMICS_FIELD_MAP: Dict[str, Tuple[str, str, str]] = {
    # Vitals
    "hr": ("Vitals", ".*", r"^HF\s*\["),
    "sys_bp": ("Vitals", ".*", r"^ABPs\s*\[|^ARTs\s*\["),
    "dia_bp": ("Vitals", ".*", r"^ABPd\s*\[|^ARTd\s*\["),
    "mean_bp": ("Vitals", ".*", r"^ABPm\s*\[|^ARTm\s*\["),
    "cvp": ("Vitals", ".*", r"^ZVDm\s*\["),
    "pcwp": ("Vitals", r"^Online.*", r"^PCWP\s*\[|^PAWP\s*\["),
    "sys_pap": ("Vitals", r"^Online.*", r"^PAPs\s*\["),
    "dia_pap": ("Vitals", r"^Online.*", r"^PAPd\s*\["),
    "mean_pap": ("Vitals", r"^Online.*", r"^PAPm\s*\["),
    "ci": ("Vitals", r"^Online.*", r"^CCI\s*\[|^HZV"),
    "nirs_left_c": ("Vitals", ".*", r"NIRS Channel 1 RSO2|NIRS.*Channel.*1"),
    "nirs_right_c": ("Vitals", ".*", r"NIRS Channel 2 RSO2|NIRS.*Channel.*2"),
    # Respiratory
    "fio2": ("Respiratory", ".*", r"^FiO2\s*\[%\]"),
    "o2": ("O2 Gabe", ".*", r"^O2\s*l/min"),
    "vent_peep": ("Respiratory", ".*", r"^PEEP\s*\["),
    "vent_pip": ("Respiratory", ".*", r"^Ppeak\s*\[|^insp.*Spitzendruck"),
    "conv_vent_rate": ("Respiratory", ".*", r"mand.*Atemfrequenz|^mand\. Atemfrequenz"),
    "spo2": ("Vitals", ".*", r"^SpO2\s*\[%\]"),
    "vent_spec": ("Respiratory", ".*", r"^Modus"),
    # Neurologie
    "rass": ("Richmond", ".*", r"^Summe Richmond-Agitation-Sedation"),
    "gcs": ("GCS", ".*", r"^Summe GCS2"),
}

HEMODYNAMICS_MEDICATION_MAP: Dict[str, str] = {
    "norepinephrine": r"(?<!o)Norepinephrin|^Arterenol",
    "epinephrine": r"(?<!Nor)Epinephrin|^Suprarenin",
    "dobutamine": r"Dobutamin",
    "milrinone": r"Milrinone|Corotrop",
    "vasopressin": r"Vasopressin|Empressin",
}

VASOACTIVE_SPEC_MAP: Dict[int, str] = {
    1: r"Dobutamin",
    2: r"Dopamin",
    3: r"Enoximon",
    4: r"(?<!Nor)Epinephrin|^Suprarenin",  # Epinephrin aber nicht in "Norepinephrin"
    5: r"Esmolol",
    6: r"Levosimendan|Simdax",
    7: r"Metaraminol|Aramino",
    8: r"Metoprolol|Beloc",
    9: r"Milrinone|Corotrop",
    10: r"Nicardipin",
    11: r"Nitroglycerin|Nitro",
    12: r"Nitroprussid",
    13: r"(?<!o)Norepinephrin|^Arterenol",  # Norepinephrin aber nicht "Epinephrin" allein
    14: r"Phenylephrin",
    15: r"Tolazolin",
    16: r"Vasopressin|Empressin",
    # 17: Other - wird automatisch gesetzt wenn vasoactive_o befüllt ist
}

VENT_SPEC_MAP: Dict[str, Optional[str]] = {
    "CPAP": "SPN_CPAP_PS",
    "CPAP_PS": "CPAP_PS",
    "SPN_CPAP": "SPN_CPAP_PS",
    "SPN_CPAP_PS": "SPN_CPAP_PS",
    "BILEVEL": "BiLevel",
    "BI_LEVEL": "BiLevel",
    "BILEVEL_VG": "BiLevel_VG",
    "BIPAP": "BIPAP",
    "PC_BIPAP": "PC_BIPAP",
    "SIMV": "SIMV",
    "SIMV_PC": "SIMV_PC",
    "SIMV_VC": "SIMV_VC",
    "PC_SIMV": "PC_SIMV",
    "VC_SIMV": "VC_SIMV",
    "A_C_VC": "A_C_VC",
    "A_C_PC": "A_C_PC",
    "A_C_PRVC": "A_C_PRVC",
    "AC_VC": "A_C_VC",
    "AC_PC": "A_C_PC",
    "PC_CMV": "PC_CMV",
    "PC_PSV": "PC_PSV",
    "PC_AC": "PC_AC",
    "PC_PC_APRV": "PC_PC_APRV",
    "APRV": "PC_PC_APRV",
    "IPPV": "IPPV",
    "VC_CMV": "VC_CMV",
    "VC_AC": "VC_AC",
    "VC_MMV": "VC_MMV",
    "SPONTANEOUS": "SPN_CPAP_PS",
    "SPONT": "SPN_CPAP_PS",
    "ASB": "ASB",
    "NIV": "NIV",
    "SBT": "SBT",
    "STANDBY": None,
}

# =============================================================================
# ANTICOAGULATION MAPPING
# =============================================================================
ANTICOAGULANT_MAP: Dict[int, str] = {
    1: r"Heparin",
    2: r"Argatroban|Argatra",
}

# =============================================================================
# ANTIPLATELET MAPPING
# =============================================================================
ANTIPLATELET_MAP: Dict[int, str] = {
    1: r"Aspirin|ASS|Aspisol",
    2: r"Plavix|Clopidogrel",
    3: r"Ticagrelor|Brilique",
    4: r"Prasugrel|Efient",
}

# =============================================================================
# ANTIBIOTIC / ANTIMYCOTIC MAPPING
# =============================================================================
ANTIBIOTIC_MAP: Dict[int, str] = {
    1: r"Cefuroxim|Zinacef|Zinnat",
    2: r"Piperacillin|Tazobactam|Pip/Taz|Tazobac",
    3: r"Meropenem|Meronem",
    4: r"Vancomycin|Vanco", # i.v.
    5: r"Vancomycin.*p\.o\.|Vanco.*p\.o\.", # p.o.
    6: r"Linezolid|Zyvoxid",
    7: r"Daptomycin|Cubicin",
    8: r"Penicillin G|Penicillin",
    9: r"Flucloxacillin|Staphylex",
    10: r"Rifampicin|Eremfat",
    11: r"Gentamicin|Refobacin",
    12: r"Tobramycin|Gernebacin",
    13: r"Ciprofloxacin|Cipro",
    15: r"Erythromycin|Erythrocin",
    16: r"Caspofungin|Cancidas",
    17: r"Amphotericin B|Ampho-Moronal|Ambisome", # inh.
    18: r"Metronidazol|Clont|Arilin",
    19: r"Cefazolin|Gramaxin",
    20: r"Ceftriaxon|Rocephin",
}

# =============================================================================
# PUMP MAPPING (PumpAggregator)
# =============================================================================
PUMP_FIELD_MAP: Dict[str, Tuple[str, str, str]] = {
    "ecls_rpm": ("ECMO", ".*", r"^Drehzahl"),
    "ecls_pf": ("ECMO", ".*", r"^Blutfluss arteriell|^Blutfluss.*l/min"),
    "ecls_gf": ("ECMO", ".*", r"^Gasfluss"),
    "ecls_fi02": ("ECMO", ".*", r"^FiO2"),
}

# =============================================================================
# IMPELLA MAPPING (ImpellaAggregator)
# =============================================================================
IMPELLA_FIELD_MAP: Dict[str, Tuple[str, str, str]] = {
    "imp_flow": ("Impella", ".*", r"^HZV"),
    "imp_purge_flow": ("Impella", ".*", r"Purgefluß|Purgefluss|Purge.*ml/h"),
    "imp_purge_pressure": ("Impella", ".*", r"Purgedruck"),
}
