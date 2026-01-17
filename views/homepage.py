"""
Homepage - Datenübersicht und Navigation.

Zeigt nach dem Datei-Upload:
- Zeitbereich der Daten
- Verfügbare Datenquellen mit Anzahl der Datenpunkte  
- MCS-Gerätezeiträume (ECMO, Impella)
- Schnellaktionen zur Navigation
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from state import get_state, update_state, has_data, get_data, get_device_time_range, Views


def render_homepage():
    """Rendert die Homepage mit Datenübersicht."""
    
    st.header("📋 Übersicht")
    
    if not has_data():
        st.info(
            "Die CSV-Datei muss mit dem [mlife-parser](https://github.com/felixsiegmeier/mlife-parser/releases/latest) erzeugt werden. "
            "Lade die aktuelle Version des Parsers hier herunter: "
            "[mlife-parser v1.0.0](https://github.com/felixsiegmeier/mlife-parser/releases/latest)"
        )
        st.info("Keine Daten geladen. Bitte zuerst eine CSV-Datei hochladen.")
        return
    
    state = get_state()
    df = state.data
    
    # Zeitbereich
    _render_time_info()
    
    st.divider()
    
    # Datenübersicht
    _render_data_summary(df)
    
    st.divider()
    
    # Patientendaten (Gewicht/Größe)
    _render_patient_data_section()
    
    st.divider()
    
    # Device-Zeiträume
    _render_device_info()
    
    st.divider()
    
    # Quick Actions
    _render_quick_actions()


def _render_time_info():
    """Zeigt Zeitbereichs-Informationen."""
    state = get_state()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Verfügbarer Zeitraum")
        if state.time_range:
            start, end = state.time_range
            start_str = start.strftime("%d.%m.%Y") if isinstance(start, datetime) else str(start)
            end_str = end.strftime("%d.%m.%Y") if isinstance(end, datetime) else str(end)
            st.write(f"**{start_str}** bis **{end_str}**")
        else:
            st.write("Nicht verfügbar")
    
    with col2:
        st.subheader("🎯 Ausgewählter Zeitraum")
        if state.selected_time_range:
            start, end = state.selected_time_range
            start_str = start.strftime("%d.%m.%Y") if isinstance(start, datetime) else str(start)
            end_str = end.strftime("%d.%m.%Y") if isinstance(end, datetime) else str(end)
            st.write(f"**{start_str}** bis **{end_str}**")
        else:
            st.write("Nicht ausgewählt")


def _render_data_summary(df: pd.DataFrame):
    """Zeigt eine Zusammenfassung der Daten."""
    
    st.subheader("📊 Datenübersicht")
    
    # Zähle pro source_type
    source_counts = df["source_type"].value_counts().to_dict()
    
    # Kategorien mit Icons - manche benötigen contains-Suche
    categories = {
        "vitals": ("💓 Vitalwerte", ["Vitals", "Vitalparameter (manuell)"], False),
        "lab": ("🧪 Labor", ["Lab"], False),
        "ecmo": ("🫀 ECMO", ["ECMO"], False),
        "impella": ("🫀 Impella", ["Impella"], True),  # contains-Suche
        "respiratory": ("🌬️ Beatmung", ["Beatmung", "Respiratory"], False),
        "medication": ("💊 Medikation", ["Medikation", "Medication"], False),
        "crrt": ("🩸 CRRT", ["Hämofilter"], True),  # contains-Suche
    }
    
    # 4 Spalten für die Metriken
    cols = st.columns(4)
    col_idx = 0
    
    for key, (label, sources, use_contains) in categories.items():
        if use_contains:
            # Contains-Suche für source_types wie "Impella A. axilliaris rechts"
            count = 0
            for pattern in sources:
                for src, cnt in source_counts.items():
                    if pattern.lower() in src.lower():
                        count += cnt
        else:
            count = sum(source_counts.get(s, 0) for s in sources)
        
        if count > 0:
            with cols[col_idx % 4]:
                st.metric(label, f"{count:,}")
            col_idx += 1
    
    # Gesamtzahl
    st.caption(f"Gesamt: **{len(df):,}** Datenpunkte")


def _render_device_info():
    """Zeigt MCS-Device Informationen."""
    
    st.subheader("🔧 MCS-Geräte")
    
    col1, col2 = st.columns(2)
    
    with col1:
        ecmo_range = get_device_time_range("ecmo")
        if ecmo_range:
            start, end = ecmo_range
            st.markdown(f"**ECMO**")
            st.write(f"{start.strftime('%d.%m.%Y %H:%M')} - {end.strftime('%d.%m.%Y %H:%M')}")
        else:
            st.write("Keine ECMO-Daten")
    
    with col2:
        impella_range = get_device_time_range("impella")
        if impella_range:
            start, end = impella_range
            st.markdown(f"**Impella**")
            st.write(f"{start.strftime('%d.%m.%Y %H:%M')} - {end.strftime('%d.%m.%Y %H:%M')}")
        else:
            st.write("Keine Impella-Daten")
    
    # Button zum Setzen des MCS-Zeitraums
    ecmo_range = get_device_time_range("ecmo")
    impella_range = get_device_time_range("impella")
    
    if ecmo_range or impella_range:
        ranges = [r for r in [ecmo_range, impella_range] if r]
        mcs_start = min(r[0] for r in ranges)
        mcs_end = max(r[1] for r in ranges)
        
        # Konvertiere pd.Timestamp zu datetime für konsistenten Vergleich
        if hasattr(mcs_start, 'to_pydatetime'):
            mcs_start = mcs_start.to_pydatetime()
        if hasattr(mcs_end, 'to_pydatetime'):
            mcs_end = mcs_end.to_pydatetime()
        
        if st.button("🎯 Zeitraum auf MCS setzen", help="Setzt den ausgewählten Zeitraum auf den MCS-Gerätezeitraum"):
            # Pending time range setzen - wird in sidebar.py verarbeitet
            st.session_state["_pending_time_range"] = (mcs_start, mcs_end)
            st.rerun()


def _render_quick_actions():
    """Zeigt Quick-Action Buttons."""
    
    st.subheader("⚡ Schnellaktionen")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Daten erkunden", use_container_width=True):
            update_state(selected_view=Views.EXPLORER)
            st.rerun()
    
    with col2:
        if st.button("🔨 Export erstellen", use_container_width=True):
            update_state(selected_view=Views.EXPORT)
            st.rerun()


def _render_patient_data_section():
    """Zeigt Patientendaten (Gewicht/Größe) und ermöglicht manuelle Eingabe falls fehlend."""
    
    state = get_state()
    
    st.subheader("👤 Patientendaten")
    
    # Prüfe ob Gewicht/Größe in den Daten vorhanden sind
    df = state.data
    patient_info_data = get_data("patient_info")
    
    weight_found = False
    height_found = False
    
    if not patient_info_data.empty:
        # Suche nach Gewicht und Größe in den Daten
        weight_params = patient_info_data[
            patient_info_data["parameter"].str.lower().str.contains("gewicht|weight", na=False, regex=True)
        ]
        height_params = patient_info_data[
            patient_info_data["parameter"].str.lower().str.contains("größe|height|größe|länge", na=False, regex=True)
        ]
        
        if not weight_params.empty:
            weight_found = True
            # Nimm den letzten Wert
            weight_val = weight_params.iloc[-1]["value"]
            st.info(f"✅ Gewicht aus Datensatz: **{weight_val} kg**")
            # Speichere im State falls noch nicht gesetzt
            if state.patient_weight is None:
                state.patient_weight = float(weight_val)
        
        if not height_params.empty:
            height_found = True
            height_val = height_params.iloc[-1]["value"]
            st.info(f"✅ Größe aus Datensatz: **{height_val} cm**")
            if state.patient_height is None:
                state.patient_height = float(height_val)
    
    # Falls Gewicht fehlt: Warnung + Eingabefeld
    if not weight_found:
        st.warning(
            "⚠️ **Gewicht nicht im Datensatz vorhanden!**\n\n"
            "Das Gewicht wird zur Berechnung der Katecholaminperfusoren (µg/kg/min) benötigt. "
            "Falls keine Eingabe erfolgt, werden diese Parameter nicht exportiert."
        )
        
        col1, col2 = st.columns([3, 1])
        with col1:
            weight_input = st.text_input(
                "Gewicht eingeben (kg)",
                value=str(state.patient_weight) if state.patient_weight else "",
                key="patient_weight_input"
            )
            if weight_input:
                try:
                    weight_val = float(weight_input)
                    state.patient_weight = weight_val
                    st.success(f"✅ Gewicht gespeichert: **{weight_val} kg**")
                except ValueError:
                    st.error("Ungültige Eingabe - bitte eine Dezimalzahl eingeben (z.B. 75.5)")
        
        update_state(patient_weight=state.patient_weight)
    
    # Falls Größe fehlt: Info + optionales Eingabefeld
    if not height_found:
        st.info(
            "ℹ️ **Größe nicht im Datensatz vorhanden** (optional)\n\n"
            "Die Größe wird nicht zur Berechnung verwendet, kann aber für die Dokumentation nützlich sein."
        )
        
        col1, col2 = st.columns([3, 1])
        with col1:
            height_input = st.text_input(
                "Größe eingeben (cm)",
                value=str(state.patient_height) if state.patient_height else "",
                key="patient_height_input"
            )
            if height_input:
                try:
                    height_val = float(height_input)
                    state.patient_height = height_val
                    st.success(f"✅ Größe gespeichert: **{height_val} cm**")
                except ValueError:
                    st.error("Ungültige Eingabe - bitte eine Dezimalzahl eingeben (z.B. 175.0)")
        
        update_state(patient_height=state.patient_height)
