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
from services.aggregators.base import revalidate_all_data, update_export_entry
from utils.field_hints import get_day_values, render_field_with_hints, get_form_date, FIELD_LABELS
from services.aggregators import (
    LabAggregator,
    HemodynamicsAggregator,
    PumpAggregator,
    ImpellaAggregator,
    PreImpellaAggregator,
    PreVAECLSAggregator,
    DemographyAggregator,
)
from services.aggregators.mapping import REDCAP_VALIDATION_TYPES  # noqa: F401

# Verfügbare Instrumente mit Labels (Events als abstrakte Device-Keys)
AVAILABLE_INSTRUMENTS = {
    "labor": {
        "label": "Labor",
        "events": ["ecls", "impella"],
        "aggregator": "LabAggregator",
    },
    "hemodynamics_ventilation_medication": {
        "label": "Hämodynamik / Beatmung",
        "events": ["ecls", "impella"],
        "aggregator": "HemodynamicsAggregator",
    },
    "pump": {
        "label": "ECMO / Pump",
        "events": ["ecls"],
        "aggregator": "PumpAggregator",
    },
    "impellaassessment_and_complications": {
        "label": "Impella Assessment",
        "events": ["impella"],
        "aggregator": "ImpellaAggregator",
    },
    "pre_impella": {
        "label": "Pre-Impella Assessment",
        "events": ["impella"],
        "aggregator": "PreImpellaAggregator",
        "is_pre": True
    },
    "pre_vaecls": {
        "label": "Pre-ECLS Assessment",
        "events": ["ecls"],
        "aggregator": "PreVAECLSAggregator",
        "is_pre": True
    },
    "demography": {
        "label": "Demographie",
        "events": ["baseline"],
        "aggregator": "DemographyAggregator",
    },
}


def render_export_builder():
    """Hauptfunktion für den Export Builder."""

    st.header("Export Builder")
    st.write("Erstellen Sie Export-Daten für REDCap. Wählen Sie Instrumente und Events aus.")

    if not has_data():
        st.warning("Keine Daten geladen.")
        return

    state = get_state()

    # Instrument-Auswahl
    _render_instrument_selection()

    st.divider()

    # ECMELLA-Konfiguration (zeitgleiche Implantation)
    _render_ecmella_config()

    # Einstellungen
    _render_settings()

    st.divider()

    # Build & Export
    _render_build_section()


def _render_instrument_selection():
    """Rendert die Instrument-Auswahl mit Checkboxen."""

    st.subheader("Instrumente auswählen")

    # Session State für Auswahl initialisieren
    if "export_instruments" not in st.session_state:
        st.session_state.export_instruments = {}

    # Prüfe welche Datenquellen verfügbar sind
    has_ecmo = not get_data("ecmo").empty
    has_impella = not get_data("impella").empty
    has_patientinfo = not get_data("PatientInfo").empty

    state = get_state()
    arm = state.arm

    # Instrument-Checkboxen in Spalten
    cols = st.columns(2)

    for i, (instr_key, instr_info) in enumerate(AVAILABLE_INSTRUMENTS.items()):
        with cols[i % 2]:
            # Event-spezifische Checkboxen (abstrakte Keys → konkrete Event-Namen)
            for event_device in instr_info["events"]:
                event = f"{event_device}_arm_{arm}"

                # Prüfe ob Event-Daten vorhanden sind
                if event_device == "ecls" and not has_ecmo:
                    continue
                if event_device == "impella" and not has_impella:
                    continue
                if event_device == "baseline" and not has_patientinfo:
                    continue

                event_label = {"ecls": "ECLS", "impella": "Impella", "baseline": "Baseline"}.get(event_device, event_device)
                key = f"{instr_key}_{event}"

                # Default: Alle Instrumente standardmäßig aktiviert
                default = True

                checked = st.checkbox(
                    f"{instr_info['label']} ({event_label})",
                    value=st.session_state.export_instruments.get(key, default),
                    key=f"cb_{key}"
                )
                st.session_state.export_instruments[key] = checked


def _render_ecmella_config():
    """Rendert die ECMELLA-Konfigurationsfrage.

    Erscheint nur, wenn sowohl ECMO- als auch Impella-Daten vorhanden sind
    UND das Pre-Impella Instrument ausgewählt ist. Fragt, ob Impella und ECLS
    zeitgleich implantiert wurden (ECMELLA 2.0), da in diesem Fall keine
    Pre-Impella-Parameter erhoben werden (REDCap Branching-Logik).
    """
    has_ecmo = not get_data("ecmo").empty
    has_impella = not get_data("impella").empty
    pre_impella_selected = st.session_state.get("export_instruments", {}).get(
        f"pre_impella_impella_arm_{get_state().arm}", False
    )

    # Nur relevant wenn beide Devices vorhanden und Pre-Impella ausgewählt
    if not (has_ecmo and has_impella and pre_impella_selected):
        return

    state = get_state()

    st.subheader("ECMELLA-Konfiguration")

    # Aktuellen Wert auslesen (None → Nein als sicherer Standard)
    current_val = state.ecmella_same_session
    current_idx = 1 if current_val is True else 0

    selected = st.radio(
        "Wurden Impella und ECLS zeitgleich / in derselben Session implantiert? (ECMELLA 2.0)",
        options=["Nein – getrennte Implantation", "Ja – gleiche Session (ECMELLA 2.0)"],
        index=current_idx,
        horizontal=True,
        help=(
            "Bei simultaner Implantation (ECMELLA 2.0) werden die Pre-Impella-Parameter "
            "nicht erhoben und pre_ecmella_2_0 wird auf 1 gesetzt. "
            "Bei getrennter Implantation werden alle Pre-Parameter normal befüllt "
            "(pre_ecmella_2_0 = 0)."
        ),
    )

    new_value = selected.startswith("Ja")
    if new_value != state.ecmella_same_session:
        update_state(ecmella_same_session=new_value)

    if new_value:
        st.warning(
            "⚠️ ECMELLA 2.0: Pre-Impella-Parameter werden **nicht** erhoben "
            "(pre_ecmella_2_0 = 1, pre_ecmella_2_0_2 = 1)."
        )
    else:
        st.info(
            "ℹ️ Getrennte Implantation: Pre-Impella-Parameter werden normal erhoben "
            "(pre_ecmella_2_0 = 0, pre_ecmella_2_0_2 = 0)."
        )

    st.divider()


def _render_settings():
    """Rendert die Einstellungs-Sektion."""
    
    state = get_state()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Erkannten Arm anzeigen
        arm = state.arm
        arm_labels = {1: "Arm 1 – nur ECLS", 2: "Arm 2 – ECLS + Impella", 3: "Arm 3 – nur Impella"}
        st.info(f"Erkannter REDCap-Arm: **{arm_labels.get(arm, arm)}**")

        # Record ID anzeigen (wird in Sidebar bearbeitet)
        if state.record_id:
            st.info(f"Record ID: **{state.record_id}**")
        else:
            st.warning("Keine Record ID gesetzt (Sidebar)")
        
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
        st.info(f"Zeitraum: **{start_str}** bis **{end_str}**")
    else:
        st.warning("Kein Zeitraum ausgewählt")
    
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
        
        if st.button("Zeitraum auf MCS setzen", key="builder_mcs_range"):
            update_state(selected_time_range=(mcs_start, mcs_end))
            st.rerun()
            
    # Hinweis zu Pre-Assessments
    st.caption("ℹ️ Pre-Assessments werden immer für den Zeitpunkt der Implantation erstellt, unabhängig vom gewählten Zeitraum.")


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
        st.warning("Bitte Record ID eingeben.")
        return
    
    if not state.selected_time_range:
        st.warning("Kein Zeitraum ausgewählt.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Daten erstellen", use_container_width=True, type="primary"):
            _build_multi_instrument_data()
    
    # Download wenn Daten vorhanden
    all_forms = _get_all_export_forms()
    if all_forms:
        with col2:
            csv_data = _export_multi_csv(all_forms)
            st.download_button(
                "CSV herunterladen",
                data=csv_data,
                file_name="redcap_export.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        st.success(f"{len(all_forms)} Einträge erstellt.")
        
        # Validierungswarnungen anzeigen
        if "validation_warnings" not in st.session_state:
            revalidate_all_data()
            
        warnings = st.session_state.get("validation_warnings", [])
        if warnings:
            with st.expander(f"⚠️ {len(warnings)} Validierungs-Warnungen (Werte außerhalb REDCap-Bereich)", expanded=True):
                st.warning("Die folgenden Werte liegen außerhalb der im REDCap-Datenwörterbuch definierten Grenzen. Bitte prüfen Sie diese vor dem Import.")
                
                edit_mode = st.toggle("Quick Edit Modus (Werte direkt hier korrigieren)", value=False, key="export_quick_edit_toggle")
                
                if edit_mode:
                    # Collect changes in a list to avoid session state mutation during iteration
                    to_save = []
                    
                    # Filter warnings that have alternatives available
                    editable_warnings = []
                    for w in warnings:
                        form_key = w.get("form_key")
                        entry_idx = w.get("entry_idx")
                        if form_key and entry_idx is not None:
                            entries = state.export_forms.get(form_key, [])
                            if entry_idx < len(entries):
                                entry = entries[entry_idx]
                                entry_date = get_form_date(entry)
                                day_values = get_day_values(w['field'], entry_date) if entry_date else []
                                if day_values:
                                    editable_warnings.append((w, entry, day_values))
                    
                    if not editable_warnings:
                        st.info("Keine der Warnungen hat alternative Werte in den Rohdaten verfügbar.")
                    
                    for i, (w, entry, day_values) in enumerate(editable_warnings):
                        form_key = w["form_key"]
                        entry_idx = w["entry_idx"]
                        with st.container():
                            cols = st.columns([1.5, 1, 1, 1, 1, 1, 3.5])
                            with cols[0]:
                                st.write(f"**{w['field']}**\n{w['date']}")
                            with cols[1]:
                                st.caption("WERT")
                                st.write(f"{w['value']}")
                            with cols[2]:
                                st.caption("MIN")
                                st.write(f"{w['min']}")
                            with cols[3]:
                                st.caption("MAX")
                                st.write(f"{w['max']}")
                            with cols[4]:
                                st.caption("FEHLER")
                                st.write(f"{w['reason']}")
                            with cols[5]:
                                st.caption("EVENT")
                                st.write(f"{w['event']}")
                            with cols[6]:
                                current_val = getattr(entry, w['field'], None) if not hasattr(entry, "get") else entry.get(w['field'])
                                
                                # Dropdown mit Hints rendern
                                label = FIELD_LABELS.get(w['field'], w['field'])
                                new_val = render_field_with_hints(
                                    label=f"Korrektur {label}",
                                    current_value=current_val,
                                    day_values=day_values,
                                    key_base=f"qe_{form_key}_{entry_idx}_{w['field']}",
                                    label_visibility="collapsed"
                                )
                                
                                if new_val != current_val:
                                    if update_export_entry(form_key, entry_idx, w['field'], new_val):
                                        st.rerun()
                        st.divider()
                else:
                    w_df = pd.DataFrame(warnings)
                    # Spalten sortieren für bessere Lesbarkeit
                    display_cols = ["date", "event", "instance", "field", "value", "min", "max", "reason"]
                    # Nur vorhandene Spalten nutzen
                    actual_cols = [c for c in display_cols if c in w_df.columns]
                    st.dataframe(w_df[actual_cols], hide_index=True, use_container_width=True)

        # Zusammenfassung nach Instrument
        instrument_counts = {}
        for form in all_forms:
            # Nutze get_instrument_name() statt direktes Attribut, da Pre-Assessments redcap_repeat_instrument=None haben
            if isinstance(form, dict):
                # Für gemergete Pre-Assessment Dicts: bestimme Namen aus redcap_event_name
                event = form.get("redcap_event_name", "")
                if "ecls" in event:
                    instr = "pre_vaecls (merged)"
                elif "impella" in event:
                    instr = "pre_impella (merged)"
                else:
                    instr = "unknown"
            else:
                instr = form.get_instrument_name()
            instrument_counts[instr] = instrument_counts.get(instr, 0) + 1

        summary = ", ".join([f"{k}: {v}" for k, v in instrument_counts.items()])
        st.info(f"Zusammenfassung: {summary}")
        
        # Vorschau
        with st.expander("Vorschau"):
            preview_data = []
            for entry in all_forms:
                if isinstance(entry, dict):
                    preview_data.append(entry)
                else:
                    preview_data.append(entry.model_dump())
            st.dataframe(pd.DataFrame(preview_data), hide_index=True)


def _get_all_export_forms() -> List[Any]:
    """Holt alle Export-Formulare aus dem State."""
    state = get_state()
    all_forms = []
    for forms in state.export_forms.values():
        if forms:
            all_forms.extend(forms)
    return all_forms


def _merge_pre_assessment_entries(hv_lab_entry: Any, med_entry: Any) -> Dict[str, Any]:
    """
    Merged zwei Pre-Assessment Einträge (HV-Lab und Medication) in ein Dictionary.

    Da beide Instrumente non-repeating sind und denselben redcap_event_name haben,
    müssen sie in REDCap als eine Zeile importiert werden.

    Returns:
        Dictionary mit allen Feldern beider Einträge kombiniert.
    """
    # Beide Entries zu Dicts konvertieren
    hv_lab_dict = hv_lab_entry.model_dump()
    med_dict = med_entry.model_dump()

    # Merge: Medication-Felder zum HV-Lab Dict hinzufügen
    merged = hv_lab_dict.copy()

    # Übernehme alle Felder vom Medication Entry (außer redundante Basis-Felder)
    for key, value in med_dict.items():
        # Überspringe redundante Felder, die bereits im HV-Lab Entry sind
        if key in ['record_id', 'redcap_event_name', 'redcap_repeat_instrument', 'redcap_repeat_instance']:
            continue
        # Füge alle anderen Felder hinzu
        merged[key] = value

    return merged


def _build_multi_instrument_data():
    """Erstellt Export-Daten für alle ausgewählten Instrumente."""
    import re

    state = get_state()
    selected = st.session_state.get("export_instruments", {})

    arm = state.arm
    ecls_event     = f"ecls_arm_{arm}"
    impella_event  = f"impella_arm_{arm}"
    baseline_event = f"baseline_arm_{arm}"

    # Datumsliste erstellen
    dates = _get_date_range()

    # Reset warnings
    st.session_state["validation_warnings"] = []

    # Export-Forms zurücksetzen
    new_export_forms: Dict[str, List[Any]] = {}

    # Pro Instrument + Event aggregieren
    for key, is_selected in selected.items():
        if not is_selected:
            continue

        # Key aufsplitten: "labor_ecls_arm_1" -> instr_name="labor", event_name="ecls_arm_1"
        m = re.search(r'_((?:ecls|impella|baseline)_arm_\d+)$', key)
        if not m:
            continue
        event_name = m.group(1)
        instr_name = key[: -(len(event_name) + 1)]

        # Referenz-Zeit je nach Event
        if event_name.startswith("ecls"):
            ref_time = state.nearest_ecls_time
            ref_df = get_data("ecmo")
        elif event_name.startswith("impella"):
            ref_time = state.nearest_impella_time
            ref_df = get_data("impella")
        else:  # baseline
            ref_time = None
            ref_df = get_data("PatientInfo")

        if ref_df.empty:
            continue

        # Pre-Assessment (einmalig)
        if AVAILABLE_INSTRUMENTS.get(instr_name, {}).get("is_pre"):
            # Bestimme Ankerzeitpunkt
            if event_name.startswith("ecls"):
                earliest = get_data("ecmo")["timestamp"].min()
            else:
                earliest = get_data("impella")["timestamp"].min()

            if pd.isna(earliest):
                continue

            agg_class = globals().get(AVAILABLE_INSTRUMENTS[instr_name]["aggregator"])
            if not agg_class:
                continue

            # Für Pre-Impella: ECMELLA-Status übergeben (zeitgleiche Implantation)
            if instr_name == "pre_impella":
                aggregator = agg_class(
                    anchor_datetime=earliest,
                    record_id=state.record_id,
                    data=state.data,
                    ecmella_same_session=state.ecmella_same_session or False,
                    redcap_event_name=impella_event,
                )
            else:
                aggregator = agg_class(
                    anchor_datetime=earliest,
                    record_id=state.record_id,
                    data=state.data,
                    redcap_event_name=ecls_event,
                )

            # Erstelle beide Entries und merge sie zu einem Dictionary
            # Da beide non-repeating sind und denselben event haben,
            # müssen sie in REDCap als eine Zeile importiert werden
            hv_lab_entry = aggregator.create_hv_lab_entry()
            med_entry = aggregator.create_medication_entry()

            merged_dict = _merge_pre_assessment_entries(hv_lab_entry, med_entry)

            # Speichere das gemergete Dictionary als eine Zeile
            form_key = f"{instr_name}_{event_name}"
            new_export_forms[form_key] = [merged_dict]

            continue

        # Demography (einmalig)
        if instr_name == "demography":
            aggregator = DemographyAggregator(
                date=dates[0] if dates else date.today(),
                record_id=state.record_id,
                redcap_event_name=event_name,
                data=state.data
            )
            entry = aggregator.create_entry()
            
            form_key = f"{entry.get_instrument_name()}_{event_name}"
            new_export_forms[form_key] = [entry]
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
    
    # Neu validieren um Metadaten für Quick Edit zu erhalten
    revalidate_all_data()
    
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
        entry = aggregator.create_entry()
        return entry
    
    elif instrument == "hemodynamics_ventilation_medication":
        aggregator = HemodynamicsAggregator(
            date=day,
            record_id=record_id,
            redcap_event_name=event_name,
            redcap_repeat_instance=instance,
            value_strategy=value_strategy,
            nearest_time=nearest_time
        )
        entry = aggregator.create_entry()
        return entry
    
    elif instrument == "pump":
        aggregator = PumpAggregator(
            date=day,
            record_id=record_id,
            redcap_repeat_instance=instance,
            redcap_event_name=event_name,
            value_strategy=value_strategy,
            nearest_time=nearest_time
        )
        entry = aggregator.create_entry()
        return entry

    elif instrument == "impellaassessment_and_complications":
        aggregator = ImpellaAggregator(
            date=day,
            record_id=record_id,
            redcap_repeat_instance=instance,
            redcap_event_name=event_name,
            value_strategy=value_strategy,
            nearest_time=nearest_time
        )
        entry = aggregator.create_entry()
        return entry
    
    elif instrument == "demography":
        aggregator = DemographyAggregator(
            date=day,
            record_id=record_id,
            redcap_event_name=event_name,
            redcap_repeat_instance=instance,
            data=get_state().data
        )
        entry = aggregator.create_entry()
        return entry
    
    return None


def _export_multi_csv(forms: List[Any]) -> str:
    """Exportiert alle Formulare als eine CSV-Datei."""

    if not forms:
        return ""

    # Alle Formulare zu Dicts konvertieren (exclude=True Felder werden automatisch ausgeschlossen)
    # Forms können entweder Pydantic Models oder bereits Dicts sein (bei gemergte Pre-Assessments)
    data = []
    for entry in forms:
        if isinstance(entry, dict):
            data.append(entry)
        else:
            data.append(entry.model_dump())

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
        elif validation_type == "number":
            # Standard REDCap 'number' validation typically expects a dot as decimal separator
            # Rounding to int (previous behavior) was incorrect for values with decimals
            if value.is_integer():
                return int(value)
            return str(value)
        elif validation_type == "integer":
            return int(round(value))
        else:
            # Fallback for unknown types: use comma for this project's locale
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
