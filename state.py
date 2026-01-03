"""
Application State - Zentraler Zustandsmanager für die REDCap-MCS App.

Dieses Modul bietet:
- AppState: Dataclass mit allen UI- und Daten-Zuständen
- get_state/update_state/save_state: Zugriff auf den Session State
- load_data: Lädt CSV-Daten und berechnet Metadaten
- get_data: Filtert Daten nach source_type (lab, vitals, ecmo, etc.)

Die State-Struktur ist so aufgebaut, dass neue Instrumente hinzugefügt
werden können, ohne den Code zu ändern (INSTRUMENT_REGISTRY).
"""

import streamlit as st
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Any, Dict, Type
from datetime import datetime, time

from schemas.db_schemas.base import BaseExportModel
from schemas.db_schemas.lab import LabModel
from schemas.db_schemas.hemodynamics import HemodynamicsModel
from schemas.db_schemas.pump import PumpModel
from schemas.db_schemas.impella import ImpellaAssessmentModel


class Views(Enum):
    STARTPAGE = "startpage"
    HOMEPAGE = "homepage"
    EXPLORER = "explorer"
    DAILY_FORM = "daily_form"
    EXPORT = "export"


# Registry für verfügbare Instrumente
# Kann später erweitert werden ohne State-Änderungen
INSTRUMENT_REGISTRY: Dict[str, Type[BaseExportModel]] = {
    "labor": LabModel,
    "hemodynamics_ventilation_medication": HemodynamicsModel,
    "pump": PumpModel,
    "impellaassessment_and_complications": ImpellaAssessmentModel,
}

# Mapping: Event -> verfügbare Instrumente
EVENT_INSTRUMENTS: Dict[str, list[str]] = {
    "baseline_arm_2": [],  # Keine täglichen Daten-Instrumente
    "ecls_arm_2": ["labor", "hemodynamics_ventilation_medication", "pump"],
    "impella_arm_2": ["labor", "hemodynamics_ventilation_medication", "impellaassessment_and_complications"],
}


@dataclass
class AppState:
    """Zentraler Application State - wird in st.session_state gespeichert."""
    
    # Kerndaten
    data: Optional[pd.DataFrame] = None
    filtered_data: Optional[pd.DataFrame] = None  # Gefilterte Daten (wenn filter_outliers aktiv)
    record_id: Optional[str] = None
    
    # Navigation
    selected_view: Views = Views.STARTPAGE
    
    # Zeitbereiche (aus Daten abgeleitet)
    time_range: Optional[tuple] = None  # (min, max) der gesamten Daten
    selected_time_range: Optional[tuple] = None  # Vom User ausgewählter Bereich
    
    # Device-Zeiten für Export
    nearest_ecls_time: Optional[time] = None
    nearest_impella_time: Optional[time] = None
    
    # Export-Daten: Generisches Dict für alle Instrumente
    # Key = instrument_name (z.B. "labor", "echocardiography")
    # Value = Liste von Export-Models
    value_strategy: str = "nearest"
    export_forms: Dict[str, List[Any]] = field(default_factory=dict)
    
    # Rückwärtskompatibilität: lab_form Property
    @property
    def lab_form(self) -> Optional[List[LabModel]]:
        """Rückwärtskompatibilität für bestehenden Code."""
        return self.export_forms.get("labor")
    
    @lab_form.setter
    def lab_form(self, value: Optional[List[LabModel]]):
        """Setzt Labor-Formulare."""
        if value is None:
            self.export_forms.pop("labor", None)
        else:
            self.export_forms["labor"] = value
    
    # Explorer UI State (für die generische Datenansicht)
    explorer_selected_sources: List[str] = field(default_factory=list)
    explorer_selected_categories: List[str] = field(default_factory=list)
    explorer_selected_parameters: List[str] = field(default_factory=list)
    explorer_show_chart: bool = False


# ============================================================================
# State Access Functions
# ============================================================================

def get_state() -> AppState:
    """Holt den aktuellen AppState aus der Session."""
    if "app_state" not in st.session_state:
        st.session_state.app_state = AppState()
    return st.session_state.app_state


def save_state(state: AppState) -> None:
    """Speichert den AppState in der Session."""
    st.session_state.app_state = state


def update_state(**kwargs) -> None:
    """Aktualisiert einzelne Felder im State."""
    state = get_state()
    for key, value in kwargs.items():
        if hasattr(state, key):
            setattr(state, key, value)
    save_state(state)


def reset_state() -> None:
    """Setzt den State zurück."""
    st.session_state.app_state = AppState()


# ============================================================================
# Data Loading
# ============================================================================

def load_data(df: pd.DataFrame) -> AppState:
    """
    Lädt einen DataFrame in den State und berechnet Metadaten.
    
    Args:
        df: DataFrame im Long-Format mit Spalten:
            timestamp, source_type, category, parameter, value, ...
    """
    state = get_state()
    
    # Timestamp sicherstellen
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    
    state.data = df
    
    # Daten direkt filtern und Checkbox aktivieren
    from utils.data_processing import filter_outliers
    state.filtered_data, _ = filter_outliers(df)
    st.session_state["filter_outliers_enabled"] = True
    
    # Zeitbereich berechnen
    if not df.empty and "timestamp" in df.columns:
        ts_clean = df["timestamp"].dropna()
        if not ts_clean.empty:
            state.time_range = (ts_clean.min(), ts_clean.max())
            state.selected_time_range = state.time_range
    
    # Device-Zeiten für Export ermitteln
    _update_device_times(state, df)
    
    state.selected_view = Views.HOMEPAGE
    save_state(state)
    return state


def _update_device_times(state: AppState, df: pd.DataFrame) -> None:
    """Ermittelt die frühesten Device-Startzeiten für den Export."""
    if df.empty or "source_type" not in df.columns:
        return
    
    # ECMO
    ecmo_df = df[df["source_type"] == "ECMO"]
    if not ecmo_df.empty and "timestamp" in ecmo_df.columns:
        earliest = ecmo_df["timestamp"].min()
        if pd.notna(earliest):
            state.nearest_ecls_time = earliest.time()
    
    # Impella (mit contains, da oft "Impella A. axillaris rechts" etc.)
    impella_df = df[df["source_type"].str.upper().str.contains("IMPELLA", na=False)]
    if not impella_df.empty and "timestamp" in impella_df.columns:
        earliest = impella_df["timestamp"].min()
        if pd.notna(earliest):
            state.nearest_impella_time = earliest.time()


# ============================================================================
# Data Query Helpers
# ============================================================================

# Mapping für benutzerfreundliche Abfragen
# Für "impella" wird contains-Suche verwendet (s. get_data)
SOURCE_MAPPING = {
    "lab": ["Lab"],
    "vitals": ["Vitals", "Vitalparameter (manuell)"],
    "medication": ["Medikation", "Medication"],
    "ecmo": ["ECMO"],
    "impella": "__CONTAINS__",  # Spezialfall: contains-Suche
    "crrt": ["HÄMOFILTER", "CRRT"],
    "respiratory": ["Beatmung", "Respiratory"],
    "fluidbalance": ["Fluidbalance", "Bilanz"],
    "nirs": ["NIRS"],
    "patient_info": ["PatientInfo"],
}


def get_data(source: Optional[str] = None) -> pd.DataFrame:
    """
    Holt Daten aus dem State, optional gefiltert nach Source.
    Nutzt gefilterte Daten wenn die Outlier-Filter-Checkbox aktiv ist.
    
    Args:
        source: Optional - "lab", "vitals", "ecmo", etc. oder None für alle Daten
        
    Returns:
        DataFrame (kann leer sein)
    """
    state = get_state()
    
    # Nutze filtered_data wenn Filter aktiv, sonst state.data
    use_filtered = st.session_state.get("filter_outliers_enabled", False)
    df_to_use = state.filtered_data if (use_filtered and state.filtered_data is not None) else state.data
    
    if df_to_use is None or df_to_use.empty:
        return pd.DataFrame()
    
    df = df_to_use
    
    if source is None:
        return df.copy()
    
    source_lower = source.lower()
    
    # Mapping anwenden
    if source_lower in SOURCE_MAPPING:
        target = SOURCE_MAPPING[source_lower]
        
        # Spezialfall: contains-Suche (für Impella etc.)
        if target == "__CONTAINS__":
            return df[df["source_type"].str.upper().str.contains(source.upper(), na=False)].copy()
        
        # Standard: Liste von exakten Matches
        return df[df["source_type"].isin(target)].copy()
    
    # Direkte Suche
    return df[df["source_type"].str.lower() == source_lower].copy()


def has_data() -> bool:
    """Prüft ob Daten geladen sind."""
    state = get_state()
    return state.data is not None and not state.data.empty


def has_device_data(device: str) -> bool:
    """Prüft ob Daten für ein bestimmtes Device vorhanden sind."""
    return not get_data(device).empty


def get_available_sources() -> List[str]:
    """Gibt alle verfügbaren source_type Werte zurück (aus gefilterten oder ungefilterten Daten)."""
    state = get_state()
    use_filtered = st.session_state.get("filter_outliers_enabled", False)
    df_to_use = state.filtered_data if (use_filtered and state.filtered_data is not None) else state.data
    
    if df_to_use is None or df_to_use.empty:
        return []
    return df_to_use["source_type"].unique().tolist()


def get_device_time_range(device: str) -> Optional[tuple]:
    """Gibt den Zeitbereich für ein Device zurück."""
    df = get_data(device)
    if df.empty or "timestamp" not in df.columns:
        return None
    
    ts = df["timestamp"].dropna()
    if ts.empty:
        return None
    
    return (ts.min(), ts.max())
