"""
Tagesansicht - Alle Instrumente für einen Tag.

Zeigt die generierten Export-Daten pro Tag mit der Möglichkeit,
Werte zu bearbeiten. Für jeden Parameter werden alle verfügbaren
Tageswerte angezeigt, aus denen einer ausgewählt werden kann.

Gruppiert nach Events (ECLS, Impella) und Instrumenten.
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime
from typing import Dict, List, Any, Optional

from state import get_state, save_state, get_data, has_data, EVENT_INSTRUMENTS
from schemas.db_schemas.lab import LabModel
from schemas.db_schemas.hemodynamics import HemodynamicsModel
from schemas.db_schemas.pump import PumpModel
from schemas.db_schemas.impella import ImpellaAssessmentModel


# Instrument-Anzeige-Konfiguration
INSTRUMENT_CONFIG = {
    "labor": {
        "icon": "🧪",
        "label": "Labor",
        "model": LabModel,
        "sections": {
            "Blutgase arteriell": ["ph", "pc02", "p02", "hco3", "be", "sa02"],
            "Elektrolyte": ["k", "na", "gluc", "lactate"],
            "Blutbild": ["wbc", "hb", "hct", "plt"],
            "Gerinnung": ["ptt", "quick", "inr", "act"],
            "Organmarker": ["ck", "ckmb", "got", "alat", "ggt", "ldh", "lipase"],
            "Nierenfunktion": ["crea", "cc", "urea"],
            "Infektionsmarker": ["crp", "pct"],
            "Sonstiges": ["bili", "albumin", "fhb", "hapto", "sv02"],
        }
    },
    "hemodynamics_ventilation_medication": {
        "icon": "💓",
        "label": "Hämodynamik / Beatmung",
        "model": HemodynamicsModel,
        "sections": {
            "Vitalzeichen": ["hr", "sys_bp", "dia_bp", "mean_bp", "cvp"],
            "NIRS": ["nirs_left_c", "nirs_right_c", "nirs_left_f", "nirs_right_f"],
            "Beatmung": ["fi02", "vent_peep", "vent_pip", "conv_vent_rate"],
            "Katecholamine": ["norepinephrine", "epinephrine", "dobutamine", "milrinone", "vasopressin"],
            "Transfusionen": ["ery_t", "ffp_t", "thromb_t", "ppsb_t", "fib_t"],
            "Niere / Bilanz": ["urine", "output_renal_repl", "fluid_balance_numb"],
        }
    },
    "pump": {
        "icon": "🔄",
        "label": "ECMO / Pump",
        "model": PumpModel,
        "sections": {
            "ECMO-Parameter": ["ecls_rpm", "ecls_pf", "ecls_gf", "ecls_fi02"],
        }
    },
    "impellaassessment_and_complications": {
        "icon": "❤️",
        "label": "Impella",
        "model": ImpellaAssessmentModel,
        "sections": {
            "Impella-Parameter": ["imp_flow", "imp_purge_flow", "imp_purge_pressure", "imp_p_level"],
        }
    },
}

# Feld-Labels (erweitert)
FIELD_LABELS = {
    # Labor
    "ph": "pH", "pc02": "PCO2", "p02": "PO2", "hco3": "HCO3", "be": "BE",
    "sa02": "SaO2 (%)", "k": "Kalium", "na": "Natrium", "gluc": "Glukose",
    "lactate": "Laktat", "wbc": "Leukozyten", "hb": "Hämoglobin", "hct": "Hämatokrit",
    "plt": "Thrombozyten", "ptt": "PTT", "quick": "Quick (%)", "inr": "INR",
    "act": "ACT", "ck": "CK", "ckmb": "CK-MB", "got": "GOT", "alat": "ALAT",
    "ggt": "GGT", "ldh": "LDH", "lipase": "Lipase", "crea": "Kreatinin",
    "cc": "Krea-Clearance", "urea": "Harnstoff", "crp": "CRP", "pct": "PCT",
    "bili": "Bilirubin", "albumin": "Albumin", "fhb": "freies Hb", "hapto": "Haptoglobin",
    "sv02": "SvO2 (%)",
    # Hemodynamics
    "hr": "Herzfrequenz", "sys_bp": "RR sys", "dia_bp": "RR dia", "mean_bp": "MAP",
    "cvp": "ZVD", "nirs_left_c": "NIRS links cerebral", "nirs_right_c": "NIRS rechts cerebral",
    "nirs_left_f": "NIRS links femoral", "nirs_right_f": "NIRS rechts femoral",
    "fi02": "FiO2 (%)", "vent_peep": "PEEP", "vent_pip": "PIP", "conv_vent_rate": "Atemfrequenz",
    "norepinephrine": "Noradrenalin", "epinephrine": "Adrenalin", "dobutamine": "Dobutamin",
    "milrinone": "Milrinon", "vasopressin": "Vasopressin",
    "ery_t": "Erythrozyten", "ffp_t": "FFP", "thromb_t": "Thrombozyten", 
    "ppsb_t": "PPSB", "fib_t": "Fibrinogen",
    "urine": "Urin (ml)", "output_renal_repl": "CRRT Output", "fluid_balance_numb": "Bilanz",
    # ECMO
    "ecls_rpm": "Drehzahl (rpm)", "ecls_pf": "Blutfluss (L/min)", 
    "ecls_gf": "Gasfluss (L/min)", "ecls_fi02": "FiO2 (%)",
    # Impella
    "imp_flow": "Flow (L/min)", "imp_purge_flow": "Purge-Flow (ml/h)",
    "imp_purge_pressure": "Purge-Druck (mmHg)", "imp_p_level": "P-Level",
}

# Mapping: Feld -> (source_type, category_pattern, parameter_pattern)
# Für das Abrufen aller Tageswerte
FIELD_TO_SOURCE = {
    # Labor (aus Lab source_type)
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
    "sv02": ("Lab", "Blutgase venös", r"^O2-SAETTIGUNG"),
    "wbc": ("Lab", "Blutbild", r"^WBC"),
    "hb": ("Lab", "Blutbild", r"^HB"),
    "hct": ("Lab", "Blutbild", r"^HCT"),
    "plt": ("Lab", "Blutbild", r"^PLT"),
    "ptt": ("Lab", "Gerinnung", r"^PTT"),
    "quick": ("Lab", "Gerinnung", r"^TPZ"),
    "inr": ("Lab", "Gerinnung", r"^INR"),
    "ck": ("Lab", "Enzyme", r"^CK \[|^CK$"),
    "ckmb": ("Lab", "Enzyme", r"^CK-MB"),
    "got": ("Lab", "Enzyme", r"^GOT"),
    "alat": ("Lab", "Enzyme", r"^GPT"),
    "ggt": ("Lab", "Enzyme", r"^GGT"),
    "ldh": ("Lab", "Enzyme", r"^LDH"),
    "lipase": ("Lab", "Enzyme", r"^LIPASE"),
    "crp": ("Lab", "Klinische Chemie|Proteine", r"^CRP"),
    "pct": ("Lab", "Klinische Chemie|Proteine", r"^PROCALCITONIN"),
    "crea": ("Lab", "Klinische Chemie|Retention", r"^KREATININ"),
    "urea": ("Lab", "Klinische Chemie|Retention", r"^HARNSTOFF"),
    "cc": ("Lab", "Klinische Chemie|Retention", r"^GFRKREA"),
    "bili": ("Lab", "Klinische Chemie", r"^BILI"),
    "albumin": ("Lab", "Klinische Chemie|Proteine", r"^ALBUMIN"),
    "fhb": ("Lab", "Blutbild|Klinische Chemie", r"^FREIES HB"),
    "hapto": ("Lab", "Klinische Chemie|Proteine", r"^HAPTOGLOBIN"),
    # Vitals
    "hr": ("Vitals", ".*", r"^HF\s*\["),
    "sys_bp": ("Vitals", ".*", r"^ABPs\s*\[|^ARTs\s*\["),
    "dia_bp": ("Vitals", ".*", r"^ABPd\s*\[|^ARTd\s*\["),
    "mean_bp": ("Vitals", ".*", r"^ABPm\s*\[|^ARTm\s*\["),
    "cvp": ("Vitals", ".*", r"^ZVDm\s*\["),
    "nirs_left_c": ("Vitals", ".*", r"NIRS Channel 1 RSO2|NIRS.*Channel.*1"),
    "nirs_right_c": ("Vitals", ".*", r"NIRS Channel 2 RSO2|NIRS.*Channel.*2"),
    # Respiratory
    "fi02": ("Respiratory", ".*", r"^FiO2\s*\[%\]"),
    "vent_peep": ("Respiratory", ".*", r"^PEEP\s*\["),
    "vent_pip": ("Respiratory", ".*", r"^Ppeak\s*\[|^insp.*Spitzendruck"),
    # ECMO
    "ecls_rpm": ("ECMO", ".*", r"^Drehzahl"),
    "ecls_pf": ("ECMO", ".*", r"^Blutfluss arteriell|^Blutfluss.*l/min"),
    "ecls_gf": ("ECMO", ".*", r"^Gasfluss"),
    "ecls_fi02": ("ECMO", ".*", r"^FiO2"),
    # Impella
    "imp_flow": ("Impella", ".*", r"^HZV"),
    "imp_purge_flow": ("Impella", ".*", r"Purgefluß|Purgefluss|Purge.*ml/h"),
    "imp_purge_pressure": ("Impella", ".*", r"Purgedruck"),
}


def render_daily_form():
    """Hauptfunktion für die tagesbasierte Formularansicht."""
    
    st.header("📅 Tagesansicht")
    
    if not has_data():
        st.warning("Keine Daten geladen.")
        return
    
    state = get_state()
    
    # Verfügbare Tage ermitteln
    available_days = _get_available_days()
    
    if not available_days:
        st.info("Keine exportierten Daten vorhanden. Bitte zuerst im Export-Builder Daten generieren.")
        return
    
    # Tag-Auswahl
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_day = st.selectbox(
            "Tag auswählen",
            options=available_days,
            format_func=lambda d: f"{d.strftime('%d.%m.%Y')} (Tag {(d - available_days[0]).days + 1})"
        )
    
    with col2:
        hide_empty = st.checkbox(
            "Leere Felder ausblenden",
            value=True,
            key="daily_form_hide_empty"
        )
    
    st.divider()
    
    # Tag-Nummer (1-basiert)
    day_number = (selected_day - available_days[0]).days + 1
    
    # Verfügbare Events für diesen Tag
    events = _get_events_for_day(selected_day)
    
    if not events:
        st.warning(f"Keine Daten für {selected_day.strftime('%d.%m.%Y')} vorhanden.")
        return
    
    # Tabs für Events (wenn mehrere)
    if len(events) > 1:
        event_tabs = st.tabs([_get_event_label(e) for e in events])
        for event_tab, event_name in zip(event_tabs, events):
            with event_tab:
                _render_day_instruments(selected_day, day_number, event_name, hide_empty)
    else:
        # Nur ein Event - kein Tab nötig
        _render_day_instruments(selected_day, day_number, events[0], hide_empty)


def _get_available_days() -> List[date]:
    """Ermittelt alle Tage die durch den Builder generiert wurden.
    
    Nur Tage für die export_forms existieren werden angezeigt.
    """
    state = get_state()
    
    days = set()
    
    # Datumsfelder pro Instrument
    date_fields = {
        "labor": "assess_date_labor",
        "hemodynamics_ventilation_medication": "assess_date_hemo",
        "pump": "ecls_compl_date",
        "impellaassessment_and_complications": "imp_compl_date",
    }
    
    # Aus export_forms sammeln
    for form_key, entries in state.export_forms.items():
        # form_key ist z.B. "labor_ecls_arm_2" -> instrument ist "labor"
        for instr_name, date_field in date_fields.items():
            if form_key.startswith(instr_name):
                for entry in entries:
                    # entry ist ein Pydantic Model
                    entry_date = getattr(entry, date_field, None)
                    if entry_date:
                        days.add(entry_date)
                break
    
    # Sortiert zurückgeben
    return sorted(days)


def _get_events_for_day(day: date) -> List[str]:
    """Ermittelt verfügbare Events für einen Tag basierend auf export_forms."""
    state = get_state()
    events = set()
    
    # Datumsfelder pro Instrument
    date_fields = {
        "labor": "assess_date_labor",
        "hemodynamics_ventilation_medication": "assess_date_hemo",
        "pump": "ecls_compl_date",
        "impellaassessment_and_complications": "imp_compl_date",
    }
    
    # Aus export_forms ermitteln welche Events für diesen Tag existieren
    for form_key, entries in state.export_forms.items():
        # form_key ist z.B. "labor_ecls_arm_2" oder "pump_ecls_arm_2"
        if form_key.endswith("_ecls_arm_2"):
            event_name = "ecls_arm_2"
            instr_name = form_key[:-len("_ecls_arm_2")]
        elif form_key.endswith("_impella_arm_2"):
            event_name = "impella_arm_2"
            instr_name = form_key[:-len("_impella_arm_2")]
        else:
            continue
        
        # Prüfen ob ein Entry für diesen Tag existiert
        date_field = date_fields.get(instr_name)
        if date_field:
            for entry in entries:
                entry_date = getattr(entry, date_field, None)
                if entry_date == day:
                    events.add(event_name)
                    break
    
    return sorted(events)


def _get_event_label(event_name: str) -> str:
    """Gibt das Label für einen Event-Namen zurück."""
    labels = {
        "ecls_arm_2": "🫀 ECLS",
        "impella_arm_2": "❤️ Impella",
    }
    return labels.get(event_name, event_name)


def _render_day_instruments(day: date, day_number: int, event_name: str, hide_empty: bool = True):
    """Rendert alle Instrumente für einen Tag und Event."""
    
    state = get_state()
    
    # Verfügbare Instrumente für diesen Event
    available_instruments = EVENT_INSTRUMENTS.get(event_name, [])
    
    # Expander für jedes Instrument
    for instr_key in available_instruments:
        config = INSTRUMENT_CONFIG.get(instr_key)
        if not config:
            continue
        
        icon = config["icon"]
        label = config["label"]
        
        # Prüfe ob Daten für dieses Instrument existieren
        form_key = f"{instr_key}_{event_name}"
        forms = state.export_forms.get(form_key, [])
        
        # Finde den Eintrag für diesen Tag
        entry = None
        entry_idx = None
        for i, form in enumerate(forms):
            form_date = _get_form_date(form)
            if form_date == day:
                entry = form
                entry_idx = i
                break
        
        # Status-Icon
        status = "✅" if entry else "⏳"
        
        with st.expander(f"{icon} {label} {status}", expanded=(entry is not None)):
            if entry:
                _render_instrument_fields(instr_key, entry, form_key, entry_idx, hide_empty)
            else:
                st.info(f"Noch keine {label}-Daten für diesen Tag. Bitte im Export Builder erstellen.")


def _get_form_date(form: Any) -> Optional[date]:
    """Extrahiert das Datum aus einem Formular."""
    # Verschiedene Datumsfelder je nach Instrument
    for field in ["assess_date_labor", "assess_date_hemo", "ecls_compl_date", "imp_compl_date", "assess_date"]:
        val = getattr(form, field, None)
        if val:
            if isinstance(val, date):
                return val
            if isinstance(val, datetime):
                return val.date()
    return None


def _render_instrument_fields(instr_key: str, entry: Any, form_key: str, entry_idx: int, hide_empty: bool = True):
    """Rendert die Felder eines Instruments mit Werte-Auswahl."""
    
    config = INSTRUMENT_CONFIG.get(instr_key, {})
    sections = config.get("sections", {})
    
    state = get_state()
    forms = state.export_forms.get(form_key, [])
    
    # Datum für Tageswerte
    entry_date = _get_form_date(entry)
    
    changed = False
    
    for section_name, fields in sections.items():
        # Felder filtern wenn hide_empty aktiv
        if hide_empty:
            visible_fields = [f for f in fields if getattr(entry, f, None) is not None]
        else:
            visible_fields = fields
        
        # Section überspringen wenn keine sichtbaren Felder
        if not visible_fields:
            continue
        
        st.markdown(f"**{section_name}**")
        
        # Felder in Spalten
        cols = st.columns(3)
        
        for i, field in enumerate(visible_fields):
            with cols[i % 3]:
                label = FIELD_LABELS.get(field, field)
                current_value = getattr(entry, field, None)
                key_base = f"{form_key}_{entry_idx}_{field}"
                
                # Tageswerte holen wenn Mapping existiert
                day_values = _get_day_values(field, entry_date) if entry_date else []
                
                if day_values:
                    # Dropdown mit allen Tageswerten
                    new_value = _render_field_with_select(
                        label, current_value, day_values, key_base
                    )
                else:
                    # Einfaches Number-Input
                    new_value = st.number_input(
                        label,
                        value=float(current_value) if current_value is not None else None,
                        format="%.2f",
                        key=key_base,
                        label_visibility="visible"
                    )
                
                if new_value != current_value:
                    setattr(entry, field, new_value)
                    changed = True
    
    if changed:
        # Zurück in State speichern
        forms[entry_idx] = entry
        state.export_forms[form_key] = forms
        save_state(state)


def _get_day_values(field: str, day: date) -> List[tuple]:
    """
    Holt alle Werte eines Feldes für einen Tag.
    
    Returns:
        Liste von (wert, uhrzeit_string) Tupeln
    """
    if field not in FIELD_TO_SOURCE:
        return []
    
    source_type, category_pattern, param_pattern = FIELD_TO_SOURCE[field]
    
    # Daten laden
    df = get_data(source_type.lower())
    if df.empty:
        return []
    
    # Auf Tag filtern
    if "timestamp" not in df.columns:
        return []
    
    day_df = df[df["timestamp"].dt.date == day]
    if day_df.empty:
        return []
    
    # Parameter-Filter
    param_mask = day_df["parameter"].str.contains(param_pattern, case=False, na=False, regex=True)
    
    # Category-Filter (optional)
    if "category" in day_df.columns and category_pattern != ".*":
        cat_mask = day_df["category"].str.contains(category_pattern, case=False, na=False, regex=True)
        mask = param_mask & cat_mask
    else:
        mask = param_mask
    
    filtered = day_df[mask]
    if filtered.empty:
        return []
    
    # Werte extrahieren
    results = []
    for _, row in filtered.iterrows():
        try:
            val = float(row["value"])
            time_str = row["timestamp"].strftime("%H:%M") if pd.notna(row["timestamp"]) else "?"
            results.append((val, time_str))
        except (ValueError, TypeError):
            continue
    
    # Nach Zeit sortieren
    results.sort(key=lambda x: x[1])
    return results


def _render_field_with_select(
    label: str,
    current_value: Optional[float],
    day_values: List[tuple],
    key_base: str
) -> Optional[float]:
    """
    Rendert ein numerisches Feld mit Dropdown für Tageswerte.
    """
    # Dropdown-Optionen erstellen
    options = ["Manuell eingeben..."]
    value_map = {}
    
    for val, time_str in day_values:
        option_label = f"{val:.2f} ({time_str})"
        options.append(option_label)
        value_map[option_label] = val
    
    # Aktuellen Wert in Optionen finden
    current_option = "Manuell eingeben..."
    if current_value is not None:
        for opt, opt_val in value_map.items():
            if abs(opt_val - current_value) < 0.01:
                current_option = opt
                break
    
    # Selectbox
    selected_option = st.selectbox(
        label,
        options=options,
        index=options.index(current_option) if current_option in options else 0,
        key=f"{key_base}_select",
        help=f"📊 {len(day_values)} Werte verfügbar"
    )
    
    if selected_option == "Manuell eingeben...":
        # Manuelles Input
        return st.number_input(
            "Wert",
            value=float(current_value) if current_value is not None else None,
            step=0.01,
            format="%.2f",
            key=f"{key_base}_manual",
            label_visibility="collapsed"
        )
    else:
        return value_map.get(selected_option)
