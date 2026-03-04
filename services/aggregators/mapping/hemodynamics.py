from typing import Dict, Optional

from ._base import FieldDef


# =============================================================================
# HÄMODYNAMIK & BEATMUNG  (instrument: hemodynamics_ventilation_medication, repeating)
# =============================================================================
HEMODYNAMICS_REGISTRY: Dict[str, FieldDef] = {
    # Vitals
    "hr":           FieldDef("vitals", ".*",          r"^HF\s*\[",                                      "number"),
    "sys_bp":       FieldDef("vitals", ".*",          r"^ABPs\s*\[|^ARTs\s*\[",                         "number"),
    "dia_bp":       FieldDef("vitals", ".*",          r"^ABPd\s*\[|^ARTd\s*\[",                         "number"),
    "mean_bp":      FieldDef("vitals", ".*",          r"^ABPm\s*\[|^ARTm\s*\[",                         "number"),
    "cvp":          FieldDef("vitals", ".*",          r"^ZVDm\s*\[",                                    "number"),
    "pcwp":         FieldDef("vitals", r"^Online.*",  r"^PCWP\s*\[|^PAWP\s*\[",                        "number"),
    "sys_pap":      FieldDef("vitals", r"^Online.*",  r"^PAPs\s*\[",                                    "number"),
    "dia_pap":      FieldDef("vitals", r"^Online.*",  r"^PAPd\s*\[",                                    "number"),
    "mean_pap":     FieldDef("vitals", r"^Online.*",  r"^PAPm\s*\[",                                    "number"),
    "ci":           FieldDef("vitals", r"^Online.*",  r"^CCI\s*\[|^HZV",                               "number_1dp_comma_decimal"),
    "nirs_left_c":  FieldDef("vitals", ".*",          r"NIRS Channel 1 RSO2|NIRS.*Channel.*1",          "number"),
    "nirs_right_c": FieldDef("vitals", ".*",          r"NIRS Channel 2 RSO2|NIRS.*Channel.*2",          "number"),
    "sp02":         FieldDef("vitals", ".*",          r"^SpO2\s*\[%\]",                                 "number"),
    # Beatmung (Hamilton + Standard-Geräte)
    "fi02":          FieldDef("respiratory", ".*", r"^FiO2\s*(\[%\]|in\s*%)",                           "number"),
    "o2":            FieldDef("o2_supply",   ".*", r"^O2\s*l/min",                                      "number"),
    "vent_peep":     FieldDef("respiratory", ".*", r"^s?PEEP\s*\[|^Expirationsdruck\s*\(PEEP\)",        "number"),
    "vent_pip":      FieldDef("respiratory", ".*", r"^s?P[Ii][Pp]\s*\[|^Ppeak\s*\[|^s?Pin\s*\[|^insp.*Spitz", "number"),
    "conv_vent_rate":FieldDef("respiratory", ".*", r"mand.*Atemfrequenz|mandator.*Atemfrequenz",         "number"),
    "vent_spec":     FieldDef("respiratory", ".*", r"^Modus$|^Beatmungsform",                           "number"),  # String → _map_ventilation_spec()
    # Neurologie
    "rass": FieldDef("Richmond-Agitation-Sedation",      ".*", r"^Summe Richmond-Agitation-Sedation",   "number"),
    "gcs":  FieldDef("GCS (Jugendliche und Erwachsene)", ".*", r"^Summe GCS2",                          "number"),
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
# TRANSFUSION  (Teil von Hämodynamik, zählt Einheiten statt aggregieren)
# =============================================================================
TRANSFUSION_REGISTRY: Dict[str, FieldDef] = {
    "thromb_t": FieldDef("medication", "Blutersatz", r"^TK",                  "number"),
    "ery_t":    FieldDef("medication", "Blutersatz", r"^EK",                  "number"),
    "ffp_t":    FieldDef("medication", "Blutersatz", r"^FFP",                 "number"),
    "ppsb_t":   FieldDef("medication", ".*",         r"Prothromplex|Cofactor","number"),
    "fib_t":    FieldDef("medication", ".*",         r"Haemocomplettan",      "number"),
    "at3_t":    FieldDef("medication", ".*",         r"Antithrombin",         "number"),
    "fxiii_t":  FieldDef("medication", ".*",         r"Faktor XIII",          "number"),
}


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
