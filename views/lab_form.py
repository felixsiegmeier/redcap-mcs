
"""
Lab Form View - Neue Implementierung für exportfähige Laborwert-Zusammenstellung.

Diese Datei wurde komplett neu geschrieben, um der veränderten Datenstruktur gerecht zu werden.
Die lab_form Liste wird nach Armen (ECLS/Impella) gruppiert und chronologisch sortiert dargestellt.
"""

import streamlit as st
from typing import Dict, Any, Callable, List
from datetime import date, time
import pandas as pd
from state_provider.state_provider_class import state_provider
from schemas.db_schemas.lab import LabModel, WithdrawalSite
from collections import defaultdict

# Mapping von LabModel-Feldern zu schönen Labels und Einheiten
FIELD_LABELS: Dict[str, str] = {
    "redcap_repeat_instance": "Day since implantation",
    "time_assess_labor": "Assessment time (labor)",
    "ecmella_2": "ECMELLA",
    "art_site": "Arterial site",
    "pc02": "PCO2 (mmHg)",
    "p02": "PO2 (mmHg)",
    "ph": "pH",
    "hco3": "HCO3 (mmol/L)",
    "be": "BE (mmol/L)",
    "sa02": "SaO2 (%)",
    "k": "Kalium (mmol/L)",
    "na": "Natrium (mmol/L)",
    "gluc": "Glukose (mg/dL)",
    "lactate": "Laktat (mmol/L)",
    "sv02": "SvO2 (%)",
    "wbc": "Leukozyten (10^9/L)",
    "hb": "Hämoglobin (g/dL)",
    "hct": "Hämatokrit (%)",
    "plt": "Thrombozyten (10^9/L)",
    "ptt": "PTT (s)",
    "quick": "Quick (%)",
    "inr": "INR",
    "post_act": "ACT (s)",
    "act": "ACT (s)",
    "ck": "CK (U/L)",
    "ckmb": "CK-MB (U/L)",
    "got": "GOT (U/L)",
    "alat": "ALAT (U/L)",
    "ggt": "GGT (U/L)",
    "ldh": "LDH (U/L)",
    "lipase": "Lipase (U/L)",
    "albumin": "Albumin (g/L)",
    "crp": "CRP (mg/L)",
    "post_crp": "Post CRP (mg/L)",
    "post_pct": "Post PCT (ng/mL)",
    "pct": "PCT (ng/mL)",
    "hemolysis": "Hämolyse",
    "fhb": "Freies Hämoglobin (mg/dL)",
    "hapto": "Haptoglobin (g/L)",
    "bili": "Bilirubin (mg/dL)",
    "crea": "Kreatinin (mg/dL)",
    "cc": "Kreatinin-Clearance (mL/min/1.73m²)",
    "urea": "Harnstoff (mg/dL)",
}

# Mapping von WithdrawalSite zu lesbaren Labels
WITHDRAWAL_SITE_LABELS: Dict[WithdrawalSite, str] = {
    WithdrawalSite.ARTERIA_RADIALIS_RIGHT: "Arteria radialis right",
    WithdrawalSite.ARTERIA_RADIALIS_LEFT: "Arteria radialis left",
    WithdrawalSite.ARTERIA_FEMORALIS_RIGHT: "Arteria femoralis right",
    WithdrawalSite.ARTERIA_FEMORALIS_LEFT: "Arteria femoralis left",
    WithdrawalSite.ARTERIA_BRACHIALIS_RIGHT: "Arteria brachialis right",
    WithdrawalSite.ARTERIA_BRACHIALIS_LEFT: "Arteria brachialis left",
    WithdrawalSite.UNKNOWN: "Unknown",
}

# Mapping von redcap_event_name zu Arm-Namen
ARM_NAMES: Dict[str, str] = {
    "ecls_arm_2": "ECLS-Arm",
    "impella_arm_2": "Impella-Arm",
}

# Mapping von Feld zu (Kategorie, Parameter) für query_data (aus LabAggregator)
FIELD_TO_PARAM: Dict[str, tuple[str, str]] = {
    "pc02": ("Blutgase arteriell", "PCO2"),
    "p02": ("Blutgase arteriell", "PO2"),
    "ph": ("Blutgase arteriell", "PH"),
    "hco3": ("Blutgase arteriell", "HCO3"),
    "be": ("Blutgase arteriell", "ABEc"),
    "sa02": ("Blutgase arteriell", "O2-SAETTIGUNG"),
    "k": ("Blutgase arteriell", "KALIUM"),
    "na": ("Blutgase arteriell", "NATRIUM"),
    "gluc": ("Blutgase arteriell", "GLUCOSE"),
    "lactate": ("Blutgase arteriell", "LACTAT"),
    "sv02": ("Blutgase venös", "O2-SAETTIGUNG"),
    "wbc": ("Blutbild", "WBC"),
    "hb": ("Blutbild", "HB"),
    "hct": ("Blutbild", "HCT"),
    "plt": ("Blutbild", "PLT"),
    "ptt": ("Gerinnung", "PTT"),
    "quick": ("Gerinnung", "TPZ"),
    "inr": ("Gerinnung", "INR"),
    "ck": ("Enzyme", "CK"),
    "ckmb": ("Enzyme", "CK-MB"),
    "ggt": ("Enzyme", "GGT"),
    "ldh": ("Enzyme", "LDH"),
    "lipase": ("Enzyme", "LIPASE"),
    "fhb": ("Blutbild", "FREIES HB"),
    "pct": ("Klinische Chemie", "PROCALCITONIN"),
    "bili": ("Klinische Chemie", "BILI"),
    "crea": ("Klinische Chemie", "KREATININ"),
    "urea": ("Klinische Chemie", "HARNSTOFF"),
    "cc": ("Klinische Chemie", "GFRKREA"),
    "got": ("Enzyme", "GOT"),
    "alat": ("Enzyme", "ALAT"),
    "albumin": ("Klinische Chemie", "ALBUMIN"),
    "post_crp": ("Klinische Chemie", "CRP"),
    "crp": ("Klinische Chemie", "CRP"),
    "post_pct": ("Klinische Chemie", "PROCALCITONIN"),
    "hemolysis": ("Klinische Chemie", "HAEMOLYSIS"),
    "hapto": ("Klinische Chemie", "HAPTOGLOBIN"),
    "post_act": ("Gerinnung", "ACT"),
    "act": ("Gerinnung", "ACT"),
}


def get_help_text(field: str, lab_entry: LabModel) -> str:
    """Generiert Help-Text mit allen verfügbaren Werten für den Parameter an diesem Tag."""
    if field not in FIELD_TO_PARAM:
        return ""
    category, parameter = FIELD_TO_PARAM[field]
    df = state_provider.query_data("lab", {"timestamp": lab_entry.assess_date_labor, "category": category, "parameter": parameter})
    if df.empty:
        return "No additional values available"
    values_with_times = []
    for _, row in df.iterrows():
        time_str = row["timestamp"].strftime("%H:%M") if pd.notna(row["timestamp"]) else "N/A"
        value_str = f"{row['value']} ({time_str})"
        values_with_times.append(value_str)
    return f"Available values: {', '.join(values_with_times)}"


def update_field(index: int, field: str) -> Callable[[], None]:
    """Callback-Funktion zum Aktualisieren eines Feldes in lab_form."""
    def inner() -> None:
        value = st.session_state[f"lab_{index}_{field}"]
        if field == "art_site":
            selected_label = st.session_state[f"lab_{index}_{field}"]
            value = next(key for key, val in WITHDRAWAL_SITE_LABELS.items() if val == selected_label)
        elif field == "ecmella_2":
            value = 1.0 if value else 0.0
        state_provider.update_lab_form_field(index, field, value)
    return inner


def render_field(field: str, value: Any, index: int, lab_entry: LabModel) -> None:
    """Rendert ein einzelnes Feld basierend auf seinem Typ."""
    label = FIELD_LABELS.get(field, field)
    key = f"lab_{index}_{field}"

    if field == "redcap_repeat_instance":
        if key not in st.session_state:
            st.session_state[key] = int(value) if value is not None else 0
        st.number_input(label, value=st.session_state[key], step=1, key=key, on_change=update_field(index, field))
    elif field == "ecmella_2":
        if key not in st.session_state:
            st.session_state[key] = bool(value == 1.0) if value is not None else False
        st.checkbox(label, value=st.session_state[key], key=key, on_change=update_field(index, field))
    elif field == "art_site":
        options = list(WITHDRAWAL_SITE_LABELS.values())
        current_label = WITHDRAWAL_SITE_LABELS.get(value, "Unknown")
        if key not in st.session_state:
            st.session_state[key] = current_label
        st.selectbox(label, options=options, key=key, on_change=update_field(index, field))
    elif field == "time_assess_labor":
        if key not in st.session_state:
            st.session_state[key] = value if value is not None else time.min
        st.time_input(label, value=st.session_state[key], key=key, on_change=update_field(index, field))
    else:
        # Float-Felder
        help_text = get_help_text(field, lab_entry)
        if key not in st.session_state:
            st.session_state[key] = float(value) if value is not None else 0.0
        st.number_input(label, value=st.session_state[key], step=0.01, key=key, on_change=update_field(index, field), help=help_text)


def lab_form() -> None:
    """Hauptfunktion für die Lab Form View."""
    st.title("Lab Form")

    lab_form_data = state_provider.get_lab_form()
    if not lab_form_data:
        st.info("No lab data available. Please create data in the Export Builder.")
        return

    # Gruppierung nach Arm
    arms: Dict[str, List[tuple[int, LabModel]]] = defaultdict(list)
    for i, entry in enumerate(lab_form_data):
        arm = entry.redcap_event_name or "unknown"
        arms[arm].append((i, entry))

    for arm_key, entries in arms.items():
        arm_name = ARM_NAMES.get(arm_key, arm_key)
        # Sortierung nach assess_date_labor
        entries.sort(key=lambda x: x[1].assess_date_labor or date.min)

        with st.expander(f"{arm_name} ({len(entries)} entries)", expanded=True):
            for index, lab_entry in entries:
                date_str = lab_entry.assess_date_labor.strftime("%Y-%m-%d") if lab_entry.assess_date_labor else "Unknown date"
                with st.expander(f"Date: {date_str}", expanded=False):
                    # Alle relevanten Felder rendern, außer den automatisch berechneten
                    fields_to_render = [f for f in LabModel.model_fields.keys() if f not in {
                        "record_id", "redcap_event_name", "redcap_repeat_instrument", "date_assess_labor",
                        "na_post_2", "assess_time_point_labor", "assess_date_labor", "labor_complete",
                        "post_pct", "post_crp", "post_act", "hemolysis"
                    }]
                    for field in fields_to_render:
                        value = getattr(lab_entry, field)
                        render_field(field, value, index, lab_entry)