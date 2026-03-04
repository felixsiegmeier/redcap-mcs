from typing import Any, Dict


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
