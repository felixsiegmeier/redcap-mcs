"""
Startpage - CSV-Upload und Datenvalidierung.

Erste Seite der Anwendung. Erwartet eine CSV-Datei mit:
- timestamp: Zeitstempel der Messung
- source_type: Datenquelle (Lab, Vitals, ECMO, etc.)
- category: Kategorie innerhalb der Quelle
- parameter: Name des Parameters
- value: Messwert
"""

import streamlit as st
import pandas as pd

from state import load_data, Views


def render_startpage():
    """Rendert die Startseite mit File Upload."""
    
    st.title("🏥 MCS Data Parser")
    
    st.write("Laden Sie Ihre CSV-Datei hoch, um die Daten zu analysieren und für RedCap zu exportieren.")

    st.info("Die CSV-Datei wird mit dem mlife-parser erzeugt.")
    st.markdown(
        "<a href='https://github.com/felixsiegmeier/mlife-parser/releases' target='_blank'>"
        "<button style='background-color:#0099ff;color:white;padding:8px 16px;border:none;border-radius:4px;font-size:16px;cursor:pointer;'>"
        "🔗 Zum aktuellen Release des Parsers"
        "</button></a>", unsafe_allow_html=True
    )
    
    st.divider()
    
    # File Upload
    uploaded_file = st.file_uploader(
        "CSV-Datei auswählen",
        type=["csv"],
    )
    
    if uploaded_file is not None:
        try:
            with st.spinner("Lade Daten..."):
                # CSV einlesen
                df = pd.read_csv(uploaded_file, sep=";")
                
                # Validierung
                required_cols = ["timestamp", "source_type", "parameter", "value"]
                missing_cols = [c for c in required_cols if c not in df.columns]
                
                if missing_cols:
                    st.error(f"Fehlende Spalten: {', '.join(missing_cols)}")
                    st.write("Vorhandene Spalten:", list(df.columns))
                    return
                
                # Daten laden
                state = load_data(df)
                
                st.success(f"✅ {len(df):,} Datenpunkte erfolgreich geladen!")
                
                # Automatisch zur Homepage wechseln
                st.rerun()
                
        except Exception as e:
            st.error(f"Fehler beim Laden der Datei: {e}")
            st.exception(e)
