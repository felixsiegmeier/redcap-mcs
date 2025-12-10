"""
Data Explorer - Interaktive Datenvisualisierung.

Ermöglicht das Filtern und Visualisieren aller Datentypen:
- Labor, Vitalwerte, ECMO, Impella, Beatmung, etc.
- Zeitfilter und Parameter-Auswahl
- Tagesmediane oder Einzelwerte
- Ausreißer-Filterung
- Altair-Zeitreihen-Charts
"""

import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, time as dt_time

from state import get_state, get_data, has_data


# Schönere Labels für source_type Werte
SOURCE_LABELS = {
    "Lab": "🧪 Labor",
    "Vitals": "💓 Vitalwerte",
    "Vitalparameter (manuell)": "💓 Vitalwerte (manuell)",
    "ECMO": "🫀 ECMO",
    "IMPELLA": "🫀 Impella",
    "Beatmung": "🌬️ Beatmung",
    "Respiratory": "🌬️ Beatmung",
    "Medikation": "💊 Medikation",
    "Medication": "💊 Medikation",
    "HÄMOFILTER": "🩸 CRRT/Hämofilter",
    "CRRT": "🩸 CRRT",
    "Bilanz": "💧 Flüssigkeitsbilanz",
    "NIRS": "🧠 NIRS",
    "PatientInfo": "👤 Patienteninfo",
}

# Die wichtigsten/sinnvollen Datenquellen für den Explorer
# Format: (Label, source_type-Pattern, use_contains)
CORE_SOURCES = [
    ("🧪 Laborwerte", "Lab", False),
    ("🌬️ Respiratorwerte", "Respiratory", False),
    ("💓 Vitalwerte", "Vitals", False),
    ("🫀 Impella", "Impella", True),  # contains-Suche
    ("🫀 ECMO", "ECMO", False),
    ("🩸 CRRT", "Hämofilter", True),  # contains-Suche
    ("🧠 NIRS", "NIRS", True),  # contains-Suche für "PSI/NIRS/ICP"
    ("🩸 Blutprodukte", "__CATEGORY__:Blutersatz", False),  # Spezial: category-Filter
    ("💧 Bilanzen", "FluidBalance", False),
]


def render_data_explorer():
    """Hauptfunktion für den Data Explorer."""
    state = get_state()
    
    if not has_data():
        st.warning("Keine Daten geladen. Bitte zuerst eine CSV-Datei hochladen.")
        return
    
    df = state.data.copy()
    
    st.header("📊 Data Explorer")
    
    # Zeitbereich anzeigen
    if state.selected_time_range:
        start, end = state.selected_time_range
        if isinstance(start, datetime):
            st.caption(f"Zeitraum: {start.strftime('%d.%m.%Y')} - {end.strftime('%d.%m.%Y')}")
    
    # =========================================================================
    # Filter-Sektion
    # =========================================================================
    
    with st.expander("🔍 Filter", expanded=True):
        # Checkbox für alle Datenquellen
        show_all_sources = st.checkbox(
            "📋 Alle Datenquellen anzeigen",
            value=False,
            key="explorer_show_all_sources",
            help="Zeigt alle verfügbaren Datenquellen statt nur der wichtigsten"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if show_all_sources:
                # Alle source_types anzeigen
                available_sources = sorted(df["source_type"].unique().tolist())
                source_options = [f"{SOURCE_LABELS.get(s, s)}" for s in available_sources]
                
                selected_source_labels = st.multiselect(
                    "Datenquellen",
                    options=source_options,
                    default=[],
                    key="explorer_sources_all"
                )
                
                # Labels zurück zu source_type mappen
                label_to_source = {f"{SOURCE_LABELS.get(s, s)}": s for s in available_sources}
                selected_sources = [label_to_source.get(label, label) for label in selected_source_labels]
            else:
                # Nur die wichtigsten Quellen anzeigen
                core_options = [label for label, pattern, _ in CORE_SOURCES]
                
                selected_core_labels = st.multiselect(
                    "Datenquellen",
                    options=core_options,
                    default=[],
                    key="explorer_sources_core"
                )
                
                # Ausgewählte Patterns sammeln
                selected_sources = []  # Wird unten speziell behandelt
            
            # Filter anwenden
            if show_all_sources:
                if selected_sources:
                    df = df[df["source_type"].isin(selected_sources)]
            else:
                # Core-Sources: Spezielle Filterlogik
                if selected_core_labels:
                    mask = pd.Series(False, index=df.index)
                    
                    for label, pattern, use_contains in CORE_SOURCES:
                        if label not in selected_core_labels:
                            continue
                        
                        if pattern.startswith("__CATEGORY__:"):
                            # Category-Filter für Blutprodukte
                            cat_value = pattern.replace("__CATEGORY__:", "")
                            mask |= (df["category"] == cat_value)
                        elif use_contains:
                            # Contains-Suche für Impella, CRRT, NIRS
                            mask |= df["source_type"].str.contains(pattern, case=False, na=False)
                        else:
                            # Exakte Suche
                            mask |= (df["source_type"] == pattern)
                    
                    df = df[mask]
        
        with col2:
            # 2. Zeitfilter
            if "timestamp" in df.columns and not df.empty:
                ts_clean = df["timestamp"].dropna()
                if not ts_clean.empty:
                    min_date = ts_clean.min().date()
                    max_date = ts_clean.max().date()
                    
                    date_range = st.date_input(
                        "Zeitraum",
                        value=(min_date, max_date),
                        min_value=min_date,
                        max_value=max_date,
                        key="explorer_date_range"
                    )
                    
                    if isinstance(date_range, tuple) and len(date_range) == 2:
                        start_dt = datetime.combine(date_range[0], dt_time.min)
                        end_dt = datetime.combine(date_range[1], dt_time.max)
                        df = df[(df["timestamp"] >= start_dt) & (df["timestamp"] <= end_dt)]
        
        # 3. Parameter Filter
        if not df.empty and "parameter" in df.columns:
            available_params = sorted(df["parameter"].dropna().unique().tolist())
            if available_params:
                selected_params = st.multiselect(
                    "Parameter",
                    options=available_params,
                    default=[],
                    key="explorer_params"
                )
                
                if selected_params:
                    df = df[df["parameter"].isin(selected_params)]
        
        # 4. Optionen
        col_opt1, col_opt2 = st.columns(2)
        
        with col_opt1:
            show_daily_median = st.checkbox(
                "📊 24h-Median anzeigen",
                value=False,
                key="explorer_daily_median",
                help="Zeigt für numerische Werte den Median pro Tag statt Einzelwerte"
            )
        
        with col_opt2:
            filter_outliers = st.checkbox(
                "🎯 Ausreißer filtern",
                value=True,
                key="explorer_filter_outliers",
                help="Entfernt Werte außerhalb des 2.5-97.5% Perzentil-Bereichs (pro Parameter)"
            )
    
    # =========================================================================
    # Daten anzeigen
    # =========================================================================
    
    st.divider()
    
    if df.empty:
        st.info("Keine Daten für die ausgewählten Filter gefunden.")
        return
    
    # Ausreißer-Filterung anwenden wenn aktiviert
    filter_outliers = st.session_state.get("explorer_filter_outliers", True)
    outlier_count = 0
    
    if filter_outliers:
        df, outlier_count = _filter_outliers(df)
    
    # Statistik
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Datenpunkte", len(df))
    with col2:
        unique_params = df["parameter"].nunique() if "parameter" in df.columns else 0
        st.metric("Parameter", unique_params)
    with col3:
        unique_sources = df["source_type"].nunique() if "source_type" in df.columns else 0
        st.metric("Datenquellen", unique_sources)
    with col4:
        if filter_outliers and outlier_count > 0:
            st.metric("Ausreißer gefiltert", outlier_count)
    
    # 24h-Median Aggregation anwenden wenn aktiviert
    show_daily_median = st.session_state.get("explorer_daily_median", False)
    
    if show_daily_median:
        df_display = _aggregate_daily_median(df)
        if df_display.empty:
            st.info("Keine numerischen Werte für 24h-Median-Aggregation gefunden.")
            return
    else:
        df_display = df
    
    # Tabs für Tabelle und Chart
    tab_table, tab_chart = st.tabs(["📋 Tabelle", "📈 Chart"])
    
    with tab_table:
        # Spalten für Anzeige auswählen
        if show_daily_median:
            display_cols = ["date", "source_type", "parameter", "median_value", "count"]
        else:
            display_cols = ["timestamp", "source_type", "parameter", "value"]
        display_cols = [c for c in display_cols if c in df_display.columns]
        
        st.dataframe(
            df_display[display_cols].sort_values(display_cols[0], ascending=False),
            use_container_width=True,
            height=400,
            hide_index=True
        )
    
    with tab_chart:
        _render_chart(df_display, is_aggregated=show_daily_median)


def _filter_outliers(df: pd.DataFrame, lower_pct: float = 2.5, upper_pct: float = 97.5) -> tuple:
    """
    Filtert Ausreißer basierend auf Perzentilen pro Parameter.
    
    Args:
        df: DataFrame mit Daten
        lower_pct: Unteres Perzentil (Standard: 2.5%)
        upper_pct: Oberes Perzentil (Standard: 97.5%)
    
    Returns:
        Tuple (gefilterter DataFrame, Anzahl entfernter Ausreißer)
    """
    if df.empty or "value" not in df.columns:
        return df, 0
    
    df_work = df.copy()
    df_work["_value_numeric"] = pd.to_numeric(df_work["value"], errors="coerce")
    
    original_count = len(df_work)
    
    # Erstelle Maske für zu behaltende Zeilen
    keep_mask = pd.Series(True, index=df_work.index)
    
    # Pro Parameter filtern (falls vorhanden)
    if "parameter" in df_work.columns:
        for param in df_work["parameter"].dropna().unique():
            param_mask = df_work["parameter"] == param
            param_values = df_work.loc[param_mask, "_value_numeric"].dropna()
            
            if len(param_values) < 5:  # Zu wenige Werte für sinnvolle Perzentile
                continue
            
            lower = param_values.quantile(lower_pct / 100)
            upper = param_values.quantile(upper_pct / 100)
            
            # Numerische Werte außerhalb des Bereichs markieren
            numeric_mask = param_mask & df_work["_value_numeric"].notna()
            out_of_range = numeric_mask & (
                (df_work["_value_numeric"] < lower) | (df_work["_value_numeric"] > upper)
            )
            keep_mask = keep_mask & ~out_of_range
    else:
        # Ohne Parameter: globale Perzentile
        numeric_vals = df_work["_value_numeric"].dropna()
        if len(numeric_vals) >= 5:
            lower = numeric_vals.quantile(lower_pct / 100)
            upper = numeric_vals.quantile(upper_pct / 100)
            
            numeric_mask = df_work["_value_numeric"].notna()
            out_of_range = numeric_mask & (
                (df_work["_value_numeric"] < lower) | (df_work["_value_numeric"] > upper)
            )
            keep_mask = keep_mask & ~out_of_range
    
    df_filtered = df[keep_mask].copy()
    outlier_count = original_count - len(df_filtered)
    
    return df_filtered, outlier_count


def _aggregate_daily_median(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregiert numerische Werte zu 24h-Median pro Parameter."""
    
    if df.empty or "timestamp" not in df.columns:
        return pd.DataFrame()
    
    df_agg = df.copy()
    
    # Nur numerische Werte
    df_agg["value_numeric"] = pd.to_numeric(df_agg["value"], errors="coerce")
    df_agg = df_agg.dropna(subset=["value_numeric", "timestamp"])
    
    if df_agg.empty:
        return pd.DataFrame()
    
    # Datum extrahieren
    df_agg["date"] = df_agg["timestamp"].dt.date
    
    # Gruppierung nach Datum, source_type und Parameter
    group_cols = ["date", "source_type"]
    if "parameter" in df_agg.columns:
        group_cols.append("parameter")
    
    aggregated = df_agg.groupby(group_cols, as_index=False).agg(
        median_value=("value_numeric", "median"),
        count=("value_numeric", "count")
    )
    
    return aggregated


def _render_chart(df: pd.DataFrame, is_aggregated: bool = False):
    """Rendert einen interaktiven Chart für numerische Daten."""
    
    if df.empty:
        st.info("Keine Daten für Chart verfügbar.")
        return
    
    df_chart = df.copy()
    
    if is_aggregated:
        # Aggregierte Daten: date und median_value verwenden
        if "date" not in df_chart.columns or "median_value" not in df_chart.columns:
            st.info("Keine aggregierten Daten verfügbar.")
            return
        
        # Date zu datetime konvertieren für Chart
        df_chart["timestamp"] = pd.to_datetime(df_chart["date"])
        value_field = "median_value:Q"
        y_title = "Median-Wert (24h)"
        tooltip_value = alt.Tooltip("median_value:Q", title="Median", format=".2f")
    else:
        # Rohdaten: value zu numerisch konvertieren
        df_chart["value_numeric"] = pd.to_numeric(df_chart["value"], errors="coerce")
        df_chart = df_chart.dropna(subset=["value_numeric", "timestamp"])
        
        if df_chart.empty:
            st.info("Keine numerischen Werte für Chart verfügbar.")
            return
        
        value_field = "value_numeric:Q"
        y_title = "Wert"
        tooltip_value = alt.Tooltip("value_numeric:Q", title="Wert", format=".2f")
    
    # Warnung bei zu vielen Datenpunkten
    if len(df_chart) > 5000:
        st.warning(f"Große Datenmenge ({len(df_chart)} Punkte). Chart könnte langsam sein.")
        if not st.checkbox("Trotzdem anzeigen", key="chart_large_data"):
            return
    
    # Parameter für Farbkodierung
    color_field = "parameter:N" if "parameter" in df_chart.columns else "source_type:N"
    
    # Altair Chart
    chart = alt.Chart(df_chart).mark_line(point=True).encode(
        x=alt.X("timestamp:T", title="Zeit"),
        y=alt.Y(value_field, title=y_title),
        color=alt.Color(color_field, title="Parameter"),
        tooltip=[
            alt.Tooltip("timestamp:T", title="Zeit", format="%d.%m.%Y %H:%M"),
            alt.Tooltip("parameter:N", title="Parameter"),
            tooltip_value,
            alt.Tooltip("source_type:N", title="Quelle"),
        ]
    ).properties(
        height=400
    ).interactive()
    
    st.altair_chart(chart, use_container_width=True)
