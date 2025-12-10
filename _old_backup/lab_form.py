"""
Lab Form - Vereinfachte Version

Bearbeitung der erstellten Labor-Exportdaten.
"""

import streamlit as st
import pandas as pd
from datetime import date, time
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

from state import get_state, save_state, get_data
from schemas.db_schemas.lab import LabModel, WithdrawalSite


# Mapping: Feld -> (Kategorie-Pattern, Parameter-Pattern) - gleich wie in lab_aggregator.py
FIELD_TO_SOURCE = {
    # Blutgase arteriell
    "pc02": ("Blutgase arteriell", r"^PCO2"),
    "p02": ("Blutgase arteriell", r"^PO2"),
    "ph": ("Blutgase arteriell", r"^PH$|^PH "),
    "hco3": ("Blutgase arteriell", r"^HCO3"),
    "be": ("Blutgase arteriell", r"^ABEc"),
    "sa02": ("Blutgase arteriell", r"^O2-SAETTIGUNG"),
    "k": ("Blutgase arteriell", r"^KALIUM"),
    "na": ("Blutgase arteriell", r"^NATRIUM"),
    "gluc": ("Blutgase arteriell", r"^GLUCOSE"),
    "lactate": ("Blutgase arteriell", r"^LACTAT"),
    # Blutgase venös
    "sv02": ("Blutgase venös", r"^O2-SAETTIGUNG"),
    # Blutbild
    "wbc": ("Blutbild", r"^WBC"),
    "hb": ("Blutbild", r"^HB \(HGB\)|^HB\b"),
    "hct": ("Blutbild", r"^HCT"),
    "plt": ("Blutbild", r"^PLT"),
    "fhb": ("Blutbild|Klinische Chemie", r"^FREIES HB"),
    # Gerinnung
    "ptt": ("Gerinnung", r"^PTT"),
    "quick": ("Gerinnung", r"^TPZ"),
    "inr": ("Gerinnung", r"^INR"),
    "act": ("__ACT__", r".*"),  # Spezialfall: eigener source_type
    # Enzyme
    "ck": ("Enzyme", r"^CK \[|^CK$"),
    "ckmb": ("Enzyme", r"^CK-MB"),
    "ggt": ("Enzyme", r"^GGT"),
    "ldh": ("Enzyme", r"^LDH"),
    "lipase": ("Enzyme", r"^LIPASE"),
    "got": ("Enzyme", r"^GOT"),
    "alat": ("Enzyme", r"^GPT"),
    # Klinische Chemie
    "pct": ("Klinische Chemie|Proteine", r"^PROCALCITONIN"),
    "crp": ("Klinische Chemie|Proteine", r"^CRP"),
    "bili": ("Klinische Chemie", r"^BILI"),
    "crea": ("Klinische Chemie|Retention", r"^KREATININ"),
    "urea": ("Klinische Chemie|Retention", r"^HARNSTOFF"),
    "cc": ("Klinische Chemie|Retention", r"^GFRKREA"),
    "albumin": ("Klinische Chemie|Proteine", r"^ALBUMIN"),
    "hapto": ("Klinische Chemie|Proteine", r"^HAPTOGLOBIN"),
}


# Feld-Labels
FIELD_LABELS = {
    "redcap_repeat_instance": "Tag seit Implantation",
    "time_assess_labor": "Erhebungszeit",
    "ecmella_2": "ECMELLA",
    "art_site": "Entnahmestelle",
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
    "pct": "PCT (ng/mL)",
    "fhb": "Freies Hämoglobin (mg/dL)",
    "hapto": "Haptoglobin (g/L)",
    "bili": "Bilirubin (mg/dL)",
    "crea": "Kreatinin (mg/dL)",
    "cc": "Kreatinin-Clearance (mL/min/1.73m²)",
    "urea": "Harnstoff (mg/dL)",
}

# Withdrawal Site Labels
WITHDRAWAL_SITE_LABELS = {
    WithdrawalSite.ARTERIA_RADIALIS_RIGHT: "A. radialis rechts",
    WithdrawalSite.ARTERIA_RADIALIS_LEFT: "A. radialis links",
    WithdrawalSite.ARTERIA_FEMORALIS_RIGHT: "A. femoralis rechts",
    WithdrawalSite.ARTERIA_FEMORALIS_LEFT: "A. femoralis links",
    WithdrawalSite.ARTERIA_BRACHIALIS_RIGHT: "A. brachialis rechts",
    WithdrawalSite.ARTERIA_BRACHIALIS_LEFT: "A. brachialis links",
    WithdrawalSite.UNKNOWN: "Unbekannt",
}

# Arm-Namen
ARM_NAMES = {
    "ecls_arm_2": "🫀 ECLS-Arm",
    "impella_arm_2": "🫀 Impella-Arm",
}

# Felder die nicht angezeigt werden sollen
HIDDEN_FIELDS = {
    "record_id", "redcap_event_name", "redcap_repeat_instrument",
    "date_assess_labor", "na_post_2", "assess_time_point_labor",
    "assess_date_labor", "labor_complete", "post_pct", "post_crp",
    "post_act", "hemolysis"
}


def render_lab_form():
    """Hauptfunktion für das Labor-Formular."""
    
    st.header("📝 Labor-Formular")
    
    state = get_state()
    
    if not state.lab_form:
        st.info("Keine Labor-Daten vorhanden. Bitte zuerst im Export Builder Daten erstellen.")
        return
    
    st.write(f"**{len(state.lab_form)}** Einträge zur Bearbeitung verfügbar.")
    
    # Nach Arm gruppieren
    arms: Dict[str, List[tuple[int, LabModel]]] = defaultdict(list)
    for i, entry in enumerate(state.lab_form):
        arm = entry.redcap_event_name or "unknown"
        arms[arm].append((i, entry))
    
    # Tabs für Arme
    arm_keys = list(arms.keys())
    if len(arm_keys) > 1:
        tabs = st.tabs([ARM_NAMES.get(k, k) for k in arm_keys])
        for tab, arm_key in zip(tabs, arm_keys):
            with tab:
                _render_arm_entries(arms[arm_key])
    elif arm_keys:
        _render_arm_entries(arms[arm_keys[0]])


def _render_arm_entries(entries: List[tuple[int, LabModel]]):
    """Rendert die Einträge für einen Arm."""
    
    # Nach Datum sortieren
    entries.sort(key=lambda x: x[1].assess_date_labor or date.min)
    
    for index, lab_entry in entries:
        date_str = lab_entry.assess_date_labor.strftime("%d.%m.%Y") if lab_entry.assess_date_labor else "Unbekannt"
        instance = lab_entry.redcap_repeat_instance or "?"
        
        with st.expander(f"📅 {date_str} (Tag {instance})", expanded=False):
            _render_entry_fields(index, lab_entry)


def _render_entry_fields(index: int, lab_entry: LabModel):
    """Rendert die Felder eines Eintrags."""
    
    state = get_state()
    
    # Felder in Kategorien gruppieren
    categories = {
        "Blutgase": ["ph", "pc02", "p02", "hco3", "be", "sa02", "sv02"],
        "Elektrolyte": ["k", "na", "gluc", "lactate"],
        "Blutbild": ["wbc", "hb", "hct", "plt"],
        "Gerinnung": ["ptt", "quick", "inr", "act"],
        "Enzyme": ["ck", "ckmb", "got", "alat", "ggt", "ldh", "lipase"],
        "Klinische Chemie": ["albumin", "crp", "pct", "fhb", "hapto", "bili", "crea", "cc", "urea"],
        "Sonstiges": ["redcap_repeat_instance", "time_assess_labor", "art_site", "ecmella_2"],
    }
    
    for cat_name, fields in categories.items():
        with st.container():
            st.caption(f"**{cat_name}**")
            cols = st.columns(3)
            col_idx = 0
            
            for field in fields:
                if field in HIDDEN_FIELDS:
                    continue
                if not hasattr(lab_entry, field):
                    continue
                
                value = getattr(lab_entry, field)
                
                with cols[col_idx % 3]:
                    new_value = _render_field(index, field, value, lab_entry)
                    
                    # Wert aktualisieren wenn geändert
                    if new_value != value:
                        setattr(state.lab_form[index], field, new_value)
                        _update_derived_fields(state.lab_form[index], field)
                        save_state(state)
                
                col_idx += 1


def _render_field(index: int, field: str, value: Any, lab_entry: LabModel) -> Any:
    """Rendert ein einzelnes Feld und gibt den neuen Wert zurück."""
    
    label = FIELD_LABELS.get(field, field)
    key = f"lab_{index}_{field}"
    
    # Art Site - Dropdown
    if field == "art_site":
        options = list(WITHDRAWAL_SITE_LABELS.values())
        current_label = WITHDRAWAL_SITE_LABELS.get(value, "Unbekannt")
        selected = st.selectbox(label, options, index=options.index(current_label), key=key)
        # Label zurück zu Enum
        return next((k for k, v in WITHDRAWAL_SITE_LABELS.items() if v == selected), WithdrawalSite.UNKNOWN)
    
    # Zeit-Feld
    if field == "time_assess_labor":
        return st.time_input(label, value=value or time(0, 0), key=key)
    
    # Checkbox
    if field == "ecmella_2":
        return 1 if st.checkbox(label, value=bool(value), key=key) else 0
    
    # Integer
    if field == "redcap_repeat_instance":
        return st.number_input(label, value=int(value or 0), step=1, key=key)
    
    # Float (Standard) - mit Quick-Select für verfügbare Werte
    return _render_numeric_field_with_select(index, field, value, lab_entry)


def _render_numeric_field_with_select(
    index: int, 
    field: str, 
    value: Any, 
    lab_entry: LabModel
) -> Optional[float]:
    """
    Rendert ein numerisches Feld mit Quick-Select Dropdown für Tageswerte.
    """
    label = FIELD_LABELS.get(field, field)
    key = f"lab_{index}_{field}"
    
    # Tageswerte holen
    day_values = _get_day_values(field, lab_entry)
    
    # Wenn Tageswerte vorhanden: Selectbox + manuelles Input
    if day_values:
        # Dropdown-Optionen erstellen
        options = ["Manuell eingeben..."]
        value_map = {}
        for val, time_str in day_values:
            option_label = f"{val:.2f} ({time_str})"
            options.append(option_label)
            value_map[option_label] = val
        
        # Aktuellen Wert in Optionen finden
        current_option = "Manuell eingeben..."
        if value is not None:
            for opt, opt_val in value_map.items():
                if abs(opt_val - value) < 0.01:
                    current_option = opt
                    break
        
        # Selectbox
        selected_option = st.selectbox(
            f"{label}",
            options=options,
            index=options.index(current_option) if current_option in options else 0,
            key=f"{key}_select",
            help=f"📊 {len(day_values)} Werte vom {lab_entry.assess_date_labor.strftime('%d.%m.%Y') if lab_entry.assess_date_labor else 'Tag'}"
        )
        
        if selected_option == "Manuell eingeben...":
            # Manuelles Input anzeigen
            return st.number_input(
                "Wert eingeben",
                value=float(value) if value is not None else None,
                step=0.01,
                format="%.2f",
                key=f"{key}_manual",
                label_visibility="collapsed"
            )
        else:
            return value_map.get(selected_option)
    
    # Keine Tageswerte: einfaches Number-Input
    help_text = "Keine Werte für diesen Tag verfügbar"
    return st.number_input(
        label,
        value=float(value) if value is not None else None,
        step=0.01,
        format="%.2f",
        key=key,
        help=help_text
    )


def _get_help_text(field: str, lab_entry: LabModel) -> str:
    """Generiert Hilfetext mit verfügbaren Werten aus den Quelldaten."""
    
    if field not in FIELD_TO_SOURCE:
        return ""
    
    values = _get_day_values(field, lab_entry)
    
    if not values:
        return "Keine Werte für diesen Tag verfügbar"
    
    # Formatiere als "Wert (HH:MM)"
    formatted = [f"{v:.2f} ({t})" for v, t in values]
    
    # Max 8 Werte anzeigen
    if len(formatted) > 8:
        formatted = formatted[:8] + [f"... +{len(formatted)-8} weitere"]
    
    return f"📊 Tageswerte: {', '.join(formatted)}"


def _get_day_values(field: str, lab_entry: LabModel) -> List[Tuple[float, str]]:
    """
    Holt alle Werte für einen Parameter am Tag des Lab-Eintrags.
    
    Returns:
        Liste von (Wert, Uhrzeit-String) Tupeln, sortiert nach Zeit
    """
    if field not in FIELD_TO_SOURCE:
        return []
    
    category, param_pattern = FIELD_TO_SOURCE[field]
    
    # ACT Spezialfall
    if category == "__ACT__":
        return _get_act_day_values(lab_entry)
    
    df = get_data("lab")
    if df.empty or lab_entry.assess_date_labor is None:
        return []
    
    # Filter auf Tag
    day_mask = df["timestamp"].dt.date == lab_entry.assess_date_labor
    df = df[day_mask]
    
    if df.empty:
        return []
    
    # Filter auf Kategorie und Parameter (Regex)
    mask = (
        df["category"].str.contains(category, case=False, na=False, regex=True) &
        df["parameter"].str.contains(param_pattern, case=False, na=False, regex=True)
    )
    df = df[mask]
    
    if df.empty:
        return []
    
    # Werte extrahieren
    results = []
    for _, row in df.iterrows():
        try:
            val = float(row["value"])
            time_str = row["timestamp"].strftime("%H:%M") if pd.notna(row["timestamp"]) else "?"
            results.append((val, time_str))
        except (ValueError, TypeError):
            continue
    
    # Nach Zeit sortieren
    results.sort(key=lambda x: x[1])
    return results


def _get_act_day_values(lab_entry: LabModel) -> List[Tuple[float, str]]:
    """Holt ACT-Werte vom ACT source_type."""
    state = get_state()
    if state.data is None or lab_entry.assess_date_labor is None:
        return []
    
    df = state.data
    mask = (
        (df["source_type"] == "ACT") &
        (df["timestamp"].dt.date == lab_entry.assess_date_labor)
    )
    df = df[mask]
    
    if df.empty:
        return []
    
    results = []
    for _, row in df.iterrows():
        try:
            val = float(row["value"])
            time_str = row["timestamp"].strftime("%H:%M") if pd.notna(row["timestamp"]) else "?"
            results.append((val, time_str))
        except (ValueError, TypeError):
            continue
    
    results.sort(key=lambda x: x[1])
    return results


def _update_derived_fields(entry: LabModel, changed_field: str):
    """Aktualisiert abgeleitete Felder basierend auf Änderungen."""
    
    # post_pct
    if changed_field == "pct":
        entry.post_pct = 1 if entry.pct is not None else 0
    
    # post_crp
    if changed_field == "crp":
        entry.post_crp = 1 if entry.crp is not None else 0
    
    # post_act
    if changed_field == "act":
        entry.post_act = 1 if entry.act is not None else 0
    
    # hemolysis
    if changed_field in ("fhb", "hapto", "bili"):
        has_hemolysis = any([entry.fhb, entry.hapto, entry.bili])
        entry.hemolysis = 1 if has_hemolysis else 0
