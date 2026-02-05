"""
Sidebar - Globale Navigation und Einstellungen.

Enthält:
- Record ID Eingabe (für REDCap-Export)
- Zeitraum-Auswahl (filtert alle Views)
- Navigationsbuttons zu allen Seiten
"""

import streamlit as st
from datetime import datetime

from state import get_state, update_state, has_data, Views


def render_sidebar():
    """Rendert die Sidebar mit Navigation und Einstellungen."""
    
    with st.sidebar:
        st.header("Navigation")
        
        state = get_state()
        
        # Record ID
        record_id = st.text_input(
            "Record ID",
            value=state.record_id or "",
            key="sidebar_record_id",
            help="RedCap Record ID für den Export"
        )
        # Vergleich normalisieren: leerer String = None
        new_record_id = record_id if record_id else None
        if new_record_id != state.record_id:
            update_state(record_id=new_record_id)
            st.rerun()
        
        # Zeitbereich
        _render_time_range_picker()
        
        st.divider()
        
        # Daten-Filter
        _render_filter_options()
        
        st.divider()
        
        # Navigation
        if has_data():
            _render_navigation()


def _render_time_range_picker():
    """Rendert den Zeitbereich-Picker."""
    state = get_state()
    
    if state.time_range is None:
        return
    
    # Prüfe ob ein pending time range gesetzt wurde (z.B. vom MCS-Button)
    if "_pending_time_range" in st.session_state:
        pending = st.session_state.pop("_pending_time_range")
        # Widget-State setzen BEVOR das Widget gerendert wird
        start_date = pending[0].date() if hasattr(pending[0], 'date') else pending[0]
        end_date = pending[1].date() if hasattr(pending[1], 'date') else pending[1]
        st.session_state["sidebar_date_range"] = (start_date, end_date)
        # AppState auch aktualisieren
        update_state(selected_time_range=pending)
    
    # Defaults aus State
    default_start = state.time_range[0]
    default_end = state.time_range[1]
    
    if state.selected_time_range:
        default_start = state.selected_time_range[0]
        default_end = state.selected_time_range[1]
    
    # In date konvertieren falls datetime
    if isinstance(default_start, datetime):
        default_start = default_start.date()
    if isinstance(default_end, datetime):
        default_end = default_end.date()
    
    # Min/Max aus Daten
    min_date = state.time_range[0]
    max_date = state.time_range[1]
    if isinstance(min_date, datetime):
        min_date = min_date.date()
    if isinstance(max_date, datetime):
        max_date = max_date.date()
    
    # Widget-Argumente vorbereiten
    widget_kwargs = {
        "label": "Zeitraum",
        "min_value": min_date,
        "max_value": max_date,
        "key": "sidebar_date_range",
        "help": "Zeitraum für Exploration und Export"
    }
    
    # value nur setzen wenn Widget-Key noch nicht existiert
    # (sonst Warnung wegen doppelter Wertsetzung)
    if "sidebar_date_range" not in st.session_state:
        widget_kwargs["value"] = (default_start, default_end)
    
    date_range = st.date_input(**widget_kwargs)
    
    # State aktualisieren wenn Widget-Wert sich vom State unterscheidet
    if isinstance(date_range, tuple) and len(date_range) == 2:
        new_range = (
            datetime.combine(date_range[0], datetime.min.time()),
            datetime.combine(date_range[1], datetime.max.time())
        )
        # Vergleiche nur die Datums-Teile um Typ-Mismatches zu vermeiden
        current = state.selected_time_range
        if current is None or (new_range[0].date() != current[0].date() or new_range[1].date() != current[1].date()):
            update_state(selected_time_range=new_range)


def _render_filter_options():
    """Rendert die Filter-Optionen."""
    from state import get_state, save_state
    from utils.data_processing import filter_outliers
    
    state = get_state()
    
    st.subheader("Filter")
    
    # Checkbox für Ausreißer-Filterung
    filter_enabled = st.checkbox(
        "Ausreißer filtern",
        value=st.session_state.get("filter_outliers_enabled", False),
        key="filter_outliers_enabled",
        help="Filtert Werte außerhalb des 2.5-97.5% Perzentil-Bereichs pro Parameter"
    )
    
    # Wenn Checkbox aktiviert wird, wende Filterung an
    if filter_enabled and state.filtered_data is None:
        if state.data is not None and not state.data.empty:
            state.filtered_data, _ = filter_outliers(state.data)
            save_state(state)
            st.rerun()
    
    # Wenn Checkbox deaktiviert wird, lösche gefilterte Daten
    elif not filter_enabled and state.filtered_data is not None:
        state.filtered_data = None
        save_state(state)
        st.rerun()


def _render_navigation():
    """Rendert die Navigationsbuttons."""
    
    # Übersicht
    if st.button("Übersicht", use_container_width=True):
        update_state(selected_view=Views.HOMEPAGE)
        st.rerun()
    
    # Data Explorer
    if st.button("Data Explorer", use_container_width=True):
        update_state(selected_view=Views.EXPLORER)
        st.rerun()
    
    st.divider()
    
    # Export-Bereich
    st.subheader("Export")
    
    if st.button("Export Builder", use_container_width=True):
        update_state(selected_view=Views.EXPORT)
        st.rerun()
    
    if st.button("Tagesansicht", use_container_width=True):
        update_state(selected_view=Views.DAILY_FORM)
        st.rerun()
