"""
Tagesansicht - Alle Instrumente für einen Tag.

Zeigt die generierten Export-Daten pro Tag mit der Möglichkeit,
Werte zu bearbeiten. Für jeden Parameter werden alle verfügbaren
Tageswerte angezeigt, aus denen einer ausgewählt werden kann.

Gruppiert nach Events (ECLS, Impella) und Instrumenten.
"""

import streamlit as st
from datetime import date
from typing import List, Any

import re

from state import get_state, save_state, has_data, get_event_instruments
from services.aggregators.base import revalidate_all_data, update_export_entry
from utils.field_hints import FIELD_LABELS, get_day_values, render_field_with_hints, get_form_date
from schemas.db_schemas.lab import LabModel
from schemas.db_schemas.hemodynamics import HemodynamicsModel
from schemas.db_schemas.pump import PumpModel
from schemas.db_schemas.impella import ImpellaAssessmentModel



# Instrument-Anzeige-Konfiguration
INSTRUMENT_CONFIG = {
    "labor": {
        "icon": None,
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
        "icon": None,
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
        "icon": None,
        "label": "ECMO / Pump",
        "model": PumpModel,
        "sections": {
            "ECMO-Parameter": ["ecls_rpm", "ecls_pf", "ecls_gf", "ecls_fi02"],
        }
    },
    "impellaassessment_and_complications": {
        "icon": None,
        "label": "Impella",
        "model": ImpellaAssessmentModel,
        "sections": {
            "Impella-Parameter": ["imp_flow", "imp_purge_flow", "imp_purge_pressure", "imp_p_level"],
        }
    },
}

def render_daily_form():
    """Hauptfunktion für die tagesbasierte Formularansicht."""
    
    st.header("Tagesansicht")
    
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
    
    # Aus export_forms sammeln
    for forms in state.export_forms.values():
        for entry in forms:
            entry_date = get_form_date(entry)
            if entry_date:
                days.add(entry_date)
    
    # Sortiert zurückgeben
    return sorted(days)


def _get_events_for_day(day: date) -> List[str]:
    """Ermittelt verfügbare Events für einen Tag basierend auf export_forms."""
    state = get_state()
    events = set()

    # Aus export_forms ermitteln welche Events für diesen Tag existieren
    for form_key, entries in state.export_forms.items():
        m = re.search(r'_((?:ecls|impella|baseline)_arm_\d+)$', form_key)
        if not m:
            continue
        event_name = m.group(1)

        # Prüfen ob ein Entry für diesen Tag existiert
        for entry in entries:
            entry_date = get_form_date(entry)
            if entry_date == day:
                events.add(event_name)
                break

    return sorted(events)


def _get_event_label(event_name: str) -> str:
    """Gibt das Label für einen Event-Namen zurück (arm-agnostisch)."""
    if "ecls" in event_name:
        return "ECLS"
    if "impella" in event_name:
        return "Impella"
    return event_name


def _render_day_instruments(day: date, day_number: int, event_name: str, hide_empty: bool = True):
    """Rendert alle Instrumente für einen Tag und Event."""
    
    state = get_state()
    
    # Verfügbare Instrumente für diesen Event
    available_instruments = get_event_instruments(get_state().arm).get(event_name, [])
    
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
            form_date = get_form_date(form)
            if form_date == day:
                entry = form
                entry_idx = i
                break
        
        # Status-Text
        status_text = "(Vollständig)" if entry else "(Fehlt)"
        expander_label = f"{label} {status_text}"
        if icon:
            expander_label = f"{icon} {expander_label}"
        
        with st.expander(expander_label, expanded=(entry is not None)):
            if entry:
                _render_instrument_fields(instr_key, entry, form_key, entry_idx, hide_empty)
            else:
                st.info(f"Noch keine {label}-Daten für diesen Tag. Bitte im Export Builder erstellen.")



def _render_instrument_fields(instr_key: str, entry: Any, form_key: str, entry_idx: int, hide_empty: bool = True):
    """Rendert die Felder eines Instruments mit Werte-Auswahl."""
    
    config = INSTRUMENT_CONFIG.get(instr_key, {})
    sections = config.get("sections", {})
    
    state = get_state()
    forms = state.export_forms.get(form_key, [])
    
    # Datum für Tageswerte
    entry_date = get_form_date(entry)
    
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
                key_base = f"df_{form_key}_{entry_idx}_{field}"
                
                # Tageswerte holen wenn Mapping existiert
                day_values = get_day_values(field, entry_date) if entry_date else []
                
                # Dropdown mit Hints rendern
                new_value = render_field_with_hints(
                    label=label,
                    current_value=current_value,
                    day_values=day_values,
                    key_base=key_base
                )
                
                if new_value != current_value:
                    if update_export_entry(form_key, entry_idx, field, new_value):
                        st.rerun()


