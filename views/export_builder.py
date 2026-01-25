"""
Export Builder - REDCap-Export für mehrere Instrumente.

Erstellt tägliche Export-Datensätze für:
- Labor (labor)
- Hämodynamik/Beatmung/Medikation (hemodynamics_ventilation_medication)
- ECMO/Pump (pump) - nur für ecls_arm_2
- Impella Assessment (impellaassessment_and_complications) - nur für impella_arm_2

Die Formatierung entspricht den REDCap-Validierungstypen:
- Datumsformat: DD/MM/YYYY
- Zeitformat: HH:MM
- Dezimalzeichen: Komma (für number_Xdp_comma_decimal)
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime, time, timedelta
from typing import Optional, List, Dict, Any

from state import get_state, update_state, save_state, get_data, has_data
from services.aggregators import (
    LabAggregator,
    HemodynamicsAggregator,
    PumpAggregator,
    ImpellaAggregator,
)


# REDCap Validierungstypen für Formatierung (aus DataDictionary)
REDCAP_VALIDATION_TYPES = {
    # Labor
    "pc02": "number_1dp_comma_decimal",
    "p02": "number_1dp_comma_decimal",
    "hco3": "number_1dp_comma_decimal",
    "be": "number_1dp_comma_decimal",
    "sa02": "number_1dp_comma_decimal",
    "k": "number_1dp_comma_decimal",
    "sv02": "number_1dp_comma_decimal",
    "wbc": "number_1dp_comma_decimal",
    "hb": "number_1dp_comma_decimal",
    "hct": "number_1dp_comma_decimal",
    "ptt": "number_1dp_comma_decimal",
    "inr": "number_1dp_comma_decimal",
    "lipase": "number_1dp_comma_decimal",
    "albumin": "number_1dp_comma_decimal",
    "crp": "number_1dp_comma_decimal",
    "fhb": "number_1dp_comma_decimal",
    "hapto": "number_1dp_comma_decimal",
    "crea": "number_1dp_comma_decimal",
    "urea": "number_1dp_comma_decimal",
    "ph": "number_2dp_comma_decimal",
    "pct": "number_2dp_comma_decimal",
    "bili": "number_2dp_comma_decimal",
    "cc": "number_2dp_comma_decimal",
    "na": "number",
    "gluc": "number",
    "lactate": "number",
    "plt": "number",
    "quick": "number",
    "act": "number",
    "ck": "number",
    "ckmb": "number",
    "got": "number",
    "ldh": "number",
    "alat": "number",
    "ggt": "number",
    
    # Impella (aus DataDictionary)
    "imp_level": "number",
    "imp_flow": "number_1dp_comma_decimal",
    "imp_purge_pressure": "number",
    "imp_purge_flow": "number_1dp_comma_decimal",
    "imp_rpm": "number_2dp_comma_decimal",
    
    # Hemodynamics - Vitals
    "hr": "number",
    "sys_bp": "number",
    "dia_bp": "number",
    "mean_bp": "number",
    "cvp": "number",
    "sp02": "number",
    "nirs_left_c": "number",
    "nirs_right_c": "number",
    "nirs_left_f": "number",
    "nirs_right_f": "number",
    
    # Hemodynamics - PAC/Swan-Ganz
    "pcwp": "number",
    "sys_pap": "number",
    "dia_pap": "number",
    "mean_pap": "number",
    "ci": "number_1dp_comma_decimal",
    
    # Hemodynamics - Vasoaktiva
    "dobutamine": "number_2dp_comma_decimal",
    "epinephrine": "number_2dp_comma_decimal",
    "norepinephrine": "number_2dp_comma_decimal",
    "vasopressin": "number_2dp_comma_decimal",
    "milrinone": "number_2dp_comma_decimal",
    
    # Hemodynamics - Beatmung
    "o2": "number",
    "fi02": "number",
    "hfv_rate": "number",
    "conv_vent_rate": "number",
    "vent_map": "number",
    "vent_pip": "number",
    "vent_peep": "number",
    
    # Hemodynamics - Neurologie
    "gcs": "number",
    
    # Hemodynamics - Transfusion
    "thromb_t": "number",
    "ery_t": "number",
    "ffp_t": "number",
    "ppsb_t": "number",
    "fib_t": "number",
    "at3_t": "number",
    "fxiii_t": "number",
    
    # Hemodynamics - Bilanz
    "urine": "number",
    "output_renal_repl": "number",
    "fluid_balance_numb": "number",
    
    # ECMO/Pump
    "ecls_rpm": "number",
    "ecls_pf": "number_1dp_comma_decimal",
    "ecls_gf": "number_1dp_comma_decimal",
    "ecls_fi02": "number",
}

# Verfügbare Instrumente mit Labels
AVAILABLE_INSTRUMENTS = {
    "labor": {
        "label": "🧪 Labor",
        "events": ["ecls_arm_2", "impella_arm_2"],
        "aggregator": "LabAggregator",
    },
    "hemodynamics_ventilation_medication": {
        "label": "💓 Hämodynamik / Beatmung",
        "events": ["ecls_arm_2", "impella_arm_2"],
        "aggregator": "HemodynamicsAggregator",
    },
    "pump": {
        "label": "🔄 ECMO / Pump",
        "events": ["ecls_arm_2"],
        "aggregator": "PumpAggregator",
    },
    "impellaassessment_and_complications": {
        "label": "❤️ Impella Assessment",
        "events": ["impella_arm_2"],
        "aggregator": "ImpellaAggregator",
    },
}


def render_export_builder():
    """Hauptfunktion für den Export Builder."""
    
    st.header("🔨 Export Builder")
    st.write("Erstelle Export-Daten für REDCap. Wähle Instrumente und Events aus.")
    
    if not has_data():
        st.warning("Keine Daten geladen.")
        return
    
    state = get_state()
    
    # Instrument-Auswahl
    _render_instrument_selection()
    
    st.divider()
    
    # Einstellungen
    _render_settings()
    
    st.divider()
    
    # Build & Export
    _render_build_section()


def _render_instrument_selection():
    """Rendert die Instrument-Auswahl mit Checkboxen."""
    
    st.subheader("📦 Instrumente auswählen")
    
    # Session State für Auswahl initialisieren
    if "export_instruments" not in st.session_state:
        st.session_state.export_instruments = {}
    
    # Prüfe welche Datenquellen verfügbar sind
    has_ecmo = not get_data("ecmo").empty
    has_impella = not get_data("impella").empty
    
    # Instrument-Checkboxen in Spalten
    cols = st.columns(2)
    
    for i, (instr_key, instr_info) in enumerate(AVAILABLE_INSTRUMENTS.items()):
        with cols[i % 2]:
            # Event-spezifische Checkboxen
            for event in instr_info["events"]:
                # Prüfe ob Event-Daten vorhanden sind
                if event == "ecls_arm_2" and not has_ecmo:
                    continue
                if event == "impella_arm_2" and not has_impella:
                    continue
                
                event_label = "ECLS" if event == "ecls_arm_2" else "Impella"
                key = f"{instr_key}_{event}"
                
                # Default: Labor + verfügbare Events aktiviert
                default = (instr_key == "labor")
                
                checked = st.checkbox(
                    f"{instr_info['label']} ({event_label})",
                    value=st.session_state.export_instruments.get(key, default),
                    key=f"cb_{key}"
                )
                st.session_state.export_instruments[key] = checked


def _render_settings():
    """Rendert die Einstellungs-Sektion."""
    
    state = get_state()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Record ID anzeigen (wird in Sidebar bearbeitet)
        if state.record_id:
            st.info(f"🏷️ Record ID: **{state.record_id}**")
        else:
            st.warning("⚠️ Keine Record ID gesetzt (Sidebar)")
        
        # Value Strategy
        strategies = ["nearest", "median", "mean", "first", "last"]
        current_strategy = state.value_strategy if state.value_strategy in strategies else "nearest"
        strategy_idx = strategies.index(current_strategy)
        
        selected_strategy = st.selectbox(
            "Wert-Strategie",
            strategies,
            index=strategy_idx,
            help="Wie sollen mehrere Werte am selben Tag aggregiert werden?"
        )
        if selected_strategy != state.value_strategy:
            update_state(value_strategy=selected_strategy)
    
    with col2:
        # Zeitbereich-Auswahl
        _render_time_range_selector()
        
        # Nearest Time Picker (nur bei "nearest" Strategie)
        if state.value_strategy == "nearest":
            _render_nearest_time_pickers()


def _render_time_range_selector():
    """Rendert die Zeitraum-Auswahl im Export Builder."""
    from state import get_device_time_range
    
    state = get_state()
    
    # Aktuellen Zeitraum anzeigen
    if state.selected_time_range:
        start, end = state.selected_time_range
        start_str = start.strftime("%d.%m.%Y") if isinstance(start, datetime) else str(start)
        end_str = end.strftime("%d.%m.%Y") if isinstance(end, datetime) else str(end)
        st.info(f"📅 Zeitraum: **{start_str}** bis **{end_str}**")
    else:
        st.warning("⚠️ Kein Zeitraum ausgewählt")
    
    # MCS-Zeitraum Button
    ecmo_range = get_device_time_range("ecmo")
    impella_range = get_device_time_range("impella")
    
    if ecmo_range or impella_range:
        ranges = [r for r in [ecmo_range, impella_range] if r]
        mcs_start = min(r[0] for r in ranges)
        mcs_end = max(r[1] for r in ranges)
        
        # Konvertiere pd.Timestamp zu datetime
        if hasattr(mcs_start, 'to_pydatetime'):
            mcs_start = mcs_start.to_pydatetime()
        if hasattr(mcs_end, 'to_pydatetime'):
            mcs_end = mcs_end.to_pydatetime()
        
        if st.button("🎯 Auf MCS-Zeitraum setzen", key="builder_mcs_range"):
            update_state(selected_time_range=(mcs_start, mcs_end))
            st.rerun()


def _render_nearest_time_pickers():
    """Rendert die Time-Picker für die nearest-Strategie."""
    
    state = get_state()
    
    # ECMO
    ecmo_df = get_data("ecmo")
    if not ecmo_df.empty:
        default_time = state.nearest_ecls_time or time(0, 0)
        selected_time = st.time_input(
            "ECLS Referenzzeit",
            value=default_time,
            help="Zeit für 'nearest'-Suche bei ECLS-Daten"
        )
        if selected_time != state.nearest_ecls_time:
            update_state(nearest_ecls_time=selected_time)
    
    # Impella
    impella_df = get_data("impella")
    if not impella_df.empty:
        default_time = state.nearest_impella_time or time(0, 0)
        selected_time = st.time_input(
            "Impella Referenzzeit",
            value=default_time,
            help="Zeit für 'nearest'-Suche bei Impella-Daten"
        )
        if selected_time != state.nearest_impella_time:
            update_state(nearest_impella_time=selected_time)


def _render_build_section():
    """Rendert den Build & Download Bereich."""
    
    state = get_state()
    
    # Validierung
    if not state.record_id:
        st.warning("⚠️ Bitte Record ID eingeben.")
        return
    
    if not state.selected_time_range:
        st.warning("⚠️ Kein Zeitraum ausgewählt.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔨 Daten erstellen", use_container_width=True, type="primary"):
            _build_multi_instrument_data()
    
    # Download wenn Daten vorhanden
    all_forms = _get_all_export_forms()
    if all_forms:
        with col2:
            csv_data = _export_multi_csv(all_forms)
            st.download_button(
                "📥 CSV herunterladen",
                data=csv_data,
                file_name="redcap_export.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        st.success(f"✅ {len(all_forms)} Einträge erstellt.")
        
        # Zusammenfassung nach Instrument
        instrument_counts = {}
        for form in all_forms:
            instr = getattr(form, 'redcap_repeat_instrument', 'unknown')
            instrument_counts[instr] = instrument_counts.get(instr, 0) + 1
        
        summary = ", ".join([f"{k}: {v}" for k, v in instrument_counts.items()])
        st.info(f"📊 {summary}")
        
        # Vorschau
        with st.expander("📋 Vorschau"):
            preview_data = [entry.model_dump() for entry in all_forms]
            st.dataframe(pd.DataFrame(preview_data), hide_index=True)


def _get_all_export_forms() -> List[Any]:
    """Holt alle Export-Formulare aus dem State."""
    state = get_state()
    all_forms = []
    for forms in state.export_forms.values():
        if forms:
            all_forms.extend(forms)
    return all_forms


def _build_multi_instrument_data():
    """Erstellt Export-Daten für alle ausgewählten Instrumente."""
    
    state = get_state()
    selected = st.session_state.get("export_instruments", {})
    
    # Datumsliste erstellen
    dates = _get_date_range()
    if not dates:
        st.error("Keine Tage im ausgewählten Zeitraum.")
        return
    
    # Export-Forms zurücksetzen
    new_export_forms: Dict[str, List[Any]] = {}
    
    # Pro Instrument + Event aggregieren
    for key, is_selected in selected.items():
        if not is_selected:
            continue
        
        # Key aufsplitten: "labor_ecls_arm_2" -> ("labor", "ecls_arm_2")
        # Events sind immer "ecls_arm_2" oder "impella_arm_2"
        if key.endswith("_ecls_arm_2"):
            event_name = "ecls_arm_2"
            instr_name = key[:-len("_ecls_arm_2")]
        elif key.endswith("_impella_arm_2"):
            event_name = "impella_arm_2"
            instr_name = key[:-len("_impella_arm_2")]
        else:
            continue
        
        # Referenz-Zeit je nach Event
        if event_name == "ecls_arm_2":
            ref_time = state.nearest_ecls_time
            ref_df = get_data("ecmo")
        else:
            ref_time = state.nearest_impella_time
            ref_df = get_data("impella")
        
        if ref_df.empty:
            continue
        
        # Einträge für jeden Tag erstellen
        entries = []
        instance = 1
        
        for day in dates:
            day_data = ref_df[ref_df["timestamp"].dt.date == day]
            if day_data.empty:
                continue
            
            entry = _create_instrument_entry(
                instrument=instr_name,
                day=day,
                record_id=state.record_id,
                event_name=event_name,
                instance=instance,
                nearest_time=ref_time,
                value_strategy=state.value_strategy
            )
            
            if entry:
                entries.append(entry)
                instance += 1
        
        # In export_forms speichern (mit Event-Suffix für Eindeutigkeit)
        form_key = f"{instr_name}_{event_name}"
        new_export_forms[form_key] = entries
    
    # State aktualisieren
    state.export_forms = new_export_forms
    save_state(state)
    st.rerun()


def _get_date_range() -> List[date]:
    """Erstellt Liste der Tage im ausgewählten Zeitraum."""
    state = get_state()
    
    if not state.selected_time_range:
        return []
    
    dates = []
    start, end = state.selected_time_range
    
    if isinstance(start, datetime):
        start = start.date()
    if isinstance(end, datetime):
        end = end.date()
    
    current = start
    while current <= end:
        dates.append(current)
        current += timedelta(days=1)
    
    return dates


def _create_instrument_entry(
    instrument: str,
    day: date,
    record_id: str,
    event_name: str,
    instance: int,
    nearest_time: Optional[time],
    value_strategy: str
) -> Optional[Any]:
    """Erstellt einen Eintrag für das angegebene Instrument."""
    
    if instrument == "labor":
        aggregator = LabAggregator(
            date=day,
            record_id=record_id,
            redcap_event_name=event_name,
            redcap_repeat_instrument="labor",
            redcap_repeat_instance=instance,
            value_strategy=value_strategy,
            nearest_time=nearest_time
        )
        return aggregator.create_entry()
    
    elif instrument == "hemodynamics_ventilation_medication":
        aggregator = HemodynamicsAggregator(
            date=day,
            record_id=record_id,
            redcap_event_name=event_name,
            redcap_repeat_instance=instance,
            value_strategy=value_strategy,
            nearest_time=nearest_time
        )
        return aggregator.create_entry()
    
    elif instrument == "pump":
        aggregator = PumpAggregator(
            date=day,
            record_id=record_id,
            redcap_repeat_instance=instance,
            value_strategy=value_strategy,
            nearest_time=nearest_time
        )
        return aggregator.create_entry()
    
    elif instrument == "impellaassessment_and_complications":
        aggregator = ImpellaAggregator(
            date=day,
            record_id=record_id,
            redcap_repeat_instance=instance,
            value_strategy=value_strategy,
            nearest_time=nearest_time
        )
        return aggregator.create_entry()
    
    return None


def _export_multi_csv(forms: List[Any]) -> str:
    """Exportiert alle Formulare als eine CSV-Datei."""
    
    if not forms:
        return ""
    
    # Alle Formulare zu Dicts konvertieren (exclude=True Felder werden automatisch ausgeschlossen)
    data = [entry.model_dump() for entry in forms]
    df = pd.DataFrame(data)
    
    # Formatierung
    df = _format_dataframe(df)
    
    return df.to_csv(index=False, sep=",", na_rep="")


def _format_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Formatiert DataFrame für REDCap-Export."""
    
    formatted = df.copy()
    
    for col in formatted.columns:
        validation_type = REDCAP_VALIDATION_TYPES.get(col)
        formatted[col] = formatted[col].apply(
            lambda v: _format_value(v, validation_type)
        )
    
    return formatted


def _format_value(value, validation_type=None):
    """Formatiert einen einzelnen Wert für REDCap."""
    
    if pd.isna(value):
        return ""
    
    if isinstance(value, float):
        if validation_type == "number_1dp_comma_decimal":
            return f"{value:.1f}".replace(".", ",")
        elif validation_type == "number_2dp_comma_decimal":
            return f"{value:.2f}".replace(".", ",")
        elif validation_type in ("number", "integer"):
            return int(round(value))
        else:
            if value.is_integer():
                return int(value)
            return str(value).replace(".", ",")
    
    if isinstance(value, int):
        return value
    
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    
    if isinstance(value, time):
        return value.strftime("%H:%M")
    
    return value
