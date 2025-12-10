"""
MCS Data Parser - Hauptanwendung

Streamlit-basierte Anwendung zur Aufbereitung von MCS-Gerätedaten
(ECMO, Impella) für den REDCap-Import.

Architektur:
- state.py: Zentraler Zustandsmanager
- views/: Streamlit-Seiten (Homepage, Explorer, Export Builder, etc.)
- services/: Geschäftslogik (Aggregatoren)
- schemas/: Pydantic-Models für REDCap-Instrumente
"""

import streamlit as st

from state import get_state, Views
from views.sidebar import render_sidebar
from views.startpage import render_startpage
from views.homepage import render_homepage
from views.data_explorer import render_data_explorer
from views.daily_form import render_daily_form
from views.export_builder import render_export_builder


def run_app():
    """Haupteinstiegspunkt der Anwendung."""
    
    state = get_state()
    
    # Sidebar rendern (außer auf Startpage)
    if state.selected_view != Views.STARTPAGE:
        render_sidebar()
    else:
        with st.sidebar:
            st.header("Bitte Datei hochladen")
    
    # View-Routing
    match state.selected_view:
        case Views.STARTPAGE:
            render_startpage()
        
        case Views.HOMEPAGE:
            render_homepage()
        
        case Views.EXPLORER:
            render_data_explorer()
        
        case Views.DAILY_FORM:
            render_daily_form()
        
        case Views.EXPORT:
            render_export_builder()
        
        case _:
            st.error(f"Unbekannte View: {state.selected_view}")


if __name__ == "__main__":
    run_app()
