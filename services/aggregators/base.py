"""
Base Aggregator - Abstrakte Basisklasse für Instrument-Aggregatoren.

Jeder Aggregator ist verantwortlich für:
1. Quelldaten für einen Tag zu extrahieren (get_source_data)
2. Werte nach Strategie zu aggregieren (aggregate_value)
3. Ein Pydantic Export-Model zu erstellen (create_entry)

Aggregations-Strategien:
- nearest: Wert am nächsten zur Referenzzeit
- median: Median aller Tageswerte
- mean: Durchschnitt aller Tageswerte
- first/last: Erster/letzter Wert des Tages
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Tuple, Type, Any
from datetime import date, time
import pandas as pd

from schemas.db_schemas.base import BaseExportModel


def _parse_float(v) -> Optional[float]:
    """Robuste float-Konvertierung für Laborwerte und Validierungsgrenzen."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        try:
            return float(v)
        except Exception:
            return None
    try:
        s = str(v).strip()
    except Exception:
        return None
    if not s or re.match(r"^\d{1,2}[\./]\d{1,2}[\./]\d{2,4}$", s):
        return None
    s_norm = s.replace(",", ".")
    m = re.search(r"[-+]?\d+(?:\.\d+)?", s_norm)
    return float(m.group(0)) if m else None


def validate_value(
    value: Any,
    min_val_str: Optional[str],
    max_val_str: Optional[str],
    field_name: str,
    record_id: str,
    event: str,
    instance: Optional[int],
    date_str: str
) -> Optional[Dict[str, Any]]:
    """
    Standalone validation function that can be used outside of aggregators.
    Returns a warning dict or None.
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return None

    float_val = _parse_float(value)
    if float_val is None:
        return None

    min_val = _parse_float(min_val_str)
    max_val = _parse_float(max_val_str)

    if min_val is not None and float_val < min_val:
        return {
            "record_id": record_id,
            "event": event,
            "instance": instance,
            "date": date_str,
            "field": field_name,
            "value": value,
            "min": min_val_str,
            "max": max_val_str,
            "reason": "below_min"
        }
    elif max_val is not None and float_val > max_val:
        return {
            "record_id": record_id,
            "event": event,
            "instance": instance,
            "date": date_str,
            "field": field_name,
            "value": value,
            "min": min_val_str,
            "max": max_val_str,
            "reason": "above_max"
        }
    return None


def revalidate_all_data():
    """
    Re-validates all export_forms in st.session_state and updates validation_warnings.
    """
    import streamlit as st
    from state import get_state
    from services.aggregators.mapping import REDCAP_FIELD_DEFS
    
    state = get_state()
    all_warnings = []
    
    # Iterate through all forms in state.export_forms
    for form_key, entries in state.export_forms.items():
        if not entries:
            continue
            
        for i, entry in enumerate(entries):
            # entry can be a Pydantic model or a dict
            if hasattr(entry, "model_dump"):
                entry_dict = entry.model_dump()
            else:
                entry_dict = entry
            
            record_id = entry_dict.get("record_id", state.record_id)
            event = entry_dict.get("redcap_event_name", "")
            instance = entry_dict.get("redcap_repeat_instance")
            
            # Find date field
            from utils.field_hints import get_form_date
            entry_date_obj = get_form_date(entry)
            entry_date_str = str(entry_date_obj) if entry_date_obj else ""
            
            # Check all fields that have a definition in REDCAP_FIELD_DEFS
            for field_name, value in entry_dict.items():
                if field_name in REDCAP_FIELD_DEFS:
                    field_def = REDCAP_FIELD_DEFS[field_name]
                    if field_def.min_val or field_def.max_val:
                        warning = validate_value(
                            value,
                            field_def.min_val,
                            field_def.max_val,
                            field_name,
                            record_id,
                            event,
                            instance,
                            entry_date_str
                        )
                        if warning:
                            # Add some metadata for quick edit
                            warning["form_key"] = form_key
                            warning["entry_idx"] = i
                            all_warnings.append(warning)
                            
    st.session_state["validation_warnings"] = all_warnings

def update_export_entry(form_key: str, entry_idx: int, field: str, new_value: Any) -> bool:
    """
    Aktualisiert einen Eintrag in st.session_state.export_forms und triggert Re-Validierung.
    Wird sowohl von der Tagesansicht als auch vom Quick Edit im Export Builder genutzt.
    """
    import streamlit as st
    from state import get_state, save_state
    
    state = get_state()
    entries = state.export_forms.get(form_key, [])
    if entry_idx < len(entries):
        entry = entries[entry_idx]
        
        # Prüfen, ob sich der Wert wirklich geändert hat
        current_val = getattr(entry, field, None) if not hasattr(entry, "get") else entry.get(field)
        if current_val == new_value:
            return False
            
        if isinstance(entry, dict):
            entry[field] = new_value
        else:
            setattr(entry, field, new_value)
            
        # Zurück in State schreiben
        entries[entry_idx] = entry
        state.export_forms[form_key] = entries
        save_state(state)
        
        # Validierung aktualisieren
        revalidate_all_data()
        return True
    return False


logger = logging.getLogger(__name__)


class BaseAggregator(ABC):
    """
    Abstrakte Basis-Klasse für alle Instrument-Aggregatoren.
    
    Subklassen implementieren die spezifische Logik für jedes REDCap-Instrument.
    """
    
    # Zu überschreiben in Subklassen
    INSTRUMENT_NAME: str = ""
    MODEL_CLASS: Type[BaseExportModel] = BaseExportModel
    
    # Mapping: Model-Feld -> (Datenquelle, Kategorie-Pattern, Parameter-Pattern)
    # Wird in Subklassen definiert
    FIELD_MAP: Dict[str, Tuple[str, str, str]] = {}
    
    def __init__(
        self,
        date: date,
        record_id: str,
        redcap_event_name: str,
        redcap_repeat_instance: Optional[int] = None,
        value_strategy: str = "median",
        nearest_time: Optional[time] = None,
        data: Optional[pd.DataFrame] = None
    ):
        """
        Initialisiert den Aggregator.
        
        Args:
            date: Datum für das Werte aggregiert werden sollen
            record_id: REDCap Record ID
            redcap_event_name: REDCap Event Name (z.B. "ecls_arm_2")
            redcap_repeat_instance: Instanz-Nummer (Tag seit Implantation)
            value_strategy: Aggregations-Strategie ("median", "mean", "nearest", "first", "last")
            nearest_time: Referenz-Zeit für "nearest" Strategie
            data: Optional - DataFrame mit Quelldaten (sonst aus State)
        """
        self.date = date
        self.record_id = record_id
        self.redcap_event_name = redcap_event_name
        self.redcap_repeat_instance = redcap_repeat_instance
        self.value_strategy = value_strategy
        self.nearest_time = nearest_time
        self._data = data
        self._warnings: List[Dict[str, Any]] = []
    
    @abstractmethod
    def create_entry(self) -> BaseExportModel:
        """
        Erstellt ein Export-Model mit aggregierten Werten.
        
        Muss von Subklassen implementiert werden.
        """
        pass
    
    # ------------------------------------------------------------------
    # Validierung
    # ------------------------------------------------------------------
    def validate_range(
        self,
        field_name: str,
        value: Any,
        min_val_str: Optional[str],
        max_val_str: Optional[str]
    ) -> None:
        """
        Prüft, ob ein aggregierter Wert innerhalb der REDCap-Validierungsgrenzen liegt.
        Falls nicht, wird eine Warnung in self._warnings gespeichert.
        """
        warning = validate_value(
            value,
            min_val_str,
            max_val_str,
            field_name,
            self.record_id,
            self.redcap_event_name,
            self.redcap_repeat_instance,
            str(self.date)
        )
        if warning:
            self._warnings.append(warning)

    def get_warnings(self) -> List[Dict[str, Any]]:
        """Gibt alle während der Aggregation gesammelten Warnungen zurück."""
        return self._warnings

    def _process_registry(self, registry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standard-Prozess für die Aggregation einer Registry (Mapping).
        Aggregiert alle Felder in der Registry und validiert sie gegen min/max.
        
        Args:
            registry: Dictionary mit FieldDef-Objekten (z.B. LAB_REGISTRY)
            
        Returns:
            Dictionary mit aggregierten Werten für das Model-Payload
        """
        values: Dict[str, Any] = {}
        df_cache: Dict[str, pd.DataFrame] = {}

        for redcap_key, spec in registry.items():
            df = df_cache.setdefault(spec.source, self.get_source_data(spec.source))
            val = self.aggregate_value(df, spec.category, spec.pattern)
            values[redcap_key] = val
            self.validate_range(redcap_key, val, spec.min_val, spec.max_val)

        return values

    # ------------------------------------------------------------------
    # Hilfsfunktionen
    # ------------------------------------------------------------------
    def _to_float(self, v) -> Optional[float]:
        """Konvertiert heterogene Laborwerte robust zu float.

        Unterstützt u. a. Strings wie ">180", "<0,5", "  46.0 s".
        Nicht numerische Inhalte ("zu wenig Material") werden als None gewertet.
        """
        return _parse_float(v)
    
    def get_string_value(
        self,
        df: pd.DataFrame,
        category_pattern: str,
        param_pattern: str
    ) -> Optional[str]:
        """
        Holt einen String-Wert aus dem DataFrame.
        
        Args:
            df: Quelldaten
            category_pattern: Regex-Pattern für Kategorie
            param_pattern: Regex-Pattern für Parameter
            
        Returns:
            Erster gefundener String-Wert oder None
        """
        if df.empty:
            return None
        
        # Parameter-Filter
        param_mask = df["parameter"].str.contains(param_pattern, case=False, na=False, regex=True)
        
        # Category-Filter
        if "category" in df.columns and category_pattern != ".*":
            cat_mask = df["category"].str.contains(category_pattern, case=False, na=False, regex=True)
            mask = param_mask & cat_mask
        else:
            mask = param_mask
        
        filtered = df[mask]
        
        if filtered.empty:
            return None
        
        # Ersten nicht-leeren String-Wert zurückgeben
        for val in filtered["value"].dropna():
            str_val = str(val).strip()
            if str_val:
                return str_val
        
        return None

    def get_source_data(self, source: str) -> pd.DataFrame:
        """
        Holt Daten aus einer Quelle (Lab, Vitals, etc.).

        Args:
            source: Quell-Name (z.B. "lab", "vitals", "ecmo")

        Returns:
            DataFrame gefiltert auf den Tag und source_type
        """
        if self._data is not None:
            df = self._data
            if "source_type" in df.columns:
                from services.aggregators.mapping import SOURCE_MAPPING
                source_lower = source.lower()
                if source_lower in SOURCE_MAPPING:
                    target = SOURCE_MAPPING[source_lower]
                    if target == "__CONTAINS__":
                        mask = df["source_type"].str.upper().str.contains(source.upper(), na=False)
                    else:
                        mask = df["source_type"].isin(target)
                else:
                    mask = df["source_type"].str.lower().str.contains(source_lower, na=False, regex=False)
                df = df[mask]
        else:
            from state import get_data
            df = get_data(source)
        
        if df.empty:
            return pd.DataFrame()
        
        # Auf Tag filtern
        if "timestamp" in df.columns:
            return df[df["timestamp"].dt.date == self.date].copy()
        
        return df.copy()
    
    def aggregate_value(
        self,
        df: pd.DataFrame,
        category_pattern: str,
        param_pattern: str
    ) -> Optional[float]:
        """
        Aggregiert einen numerischen Wert aus dem DataFrame.
        
        Args:
            df: Quelldaten (bereits auf Tag gefiltert)
            category_pattern: Regex-Pattern für Kategorie (kann ".*" sein um alle zu akzeptieren)
            param_pattern: Regex-Pattern für Parameter
            
        Returns:
            Aggregierter Wert oder None
        """
        if df.empty:
            return None
        
        # Parameter-Filter immer anwenden
        param_mask = df["parameter"].str.contains(param_pattern, case=False, na=False, regex=True)
        
        # Category-Filter nur wenn Spalte existiert und Pattern nicht ".*" ist
        if "category" in df.columns and category_pattern != ".*":
            cat_mask = df["category"].str.contains(category_pattern, case=False, na=False, regex=True)
            mask = param_mask & cat_mask
        else:
            mask = param_mask
        
        filtered = df[mask]
        
        if filtered.empty:
            return None
        
        # Numerische Werte (robust parsen, z. B. ">180")
        parsed = filtered["value"].apply(self._to_float).dropna()
        if parsed.empty:
            return None
        
        # Strategie anwenden
        if self.value_strategy == "nearest" and self.nearest_time:
            return self._get_nearest_value(filtered, parsed)
        elif self.value_strategy == "median":
            return float(parsed.median())
        elif self.value_strategy == "mean":
            return float(parsed.mean())
        elif self.value_strategy == "first":
            return float(parsed.iloc[0])
        elif self.value_strategy == "last":
            return float(parsed.iloc[-1])
        
        # Default: median
        return float(parsed.median())
    
    def _get_nearest_value(
        self,
        df: pd.DataFrame,
        values: pd.Series
    ) -> Optional[float]:
        """Findet den Wert am nächsten zur Referenzzeit."""
        
        if self.nearest_time is None:
            return float(values.median())
        
        # Zeitdifferenz berechnen
        target_seconds = (
            self.nearest_time.hour * 3600 +
            self.nearest_time.minute * 60 +
            self.nearest_time.second
        )
        
        def time_diff(ts):
            if pd.isna(ts):
                return float('inf')
            s = ts.hour * 3600 + ts.minute * 60 + ts.second
            return abs(s - target_seconds)
        
        df = df.copy()
        df["_time_diff"] = df["timestamp"].dt.time.apply(time_diff)
        # Robuste Konvertierung
        df["_value_numeric"] = df["value"].apply(self._to_float)
        
        # Nächsten gültigen Wert finden
        valid = df.dropna(subset=["_value_numeric"])
        if valid.empty:
            return None
        
        nearest_idx = valid["_time_diff"].idxmin()
        return float(valid.loc[nearest_idx, "_value_numeric"])
    
    def get_all_day_values(
        self,
        df: pd.DataFrame,
        category_pattern: str,
        param_pattern: str
    ) -> List[Tuple[float, str]]:
        """
        Holt alle Werte eines Parameters für den Tag.
        
        Nützlich für UI-Anzeige (zeige alle verfügbaren Werte).
        
        Returns:
            Liste von (Wert, Uhrzeit-String) Tupeln
        """
        if df.empty:
            return []
        
        # Parameter-Filter immer anwenden
        param_mask = df["parameter"].str.contains(param_pattern, case=False, na=False, regex=True)
        
        # Category-Filter nur wenn Spalte existiert und Pattern nicht ".*" ist
        if "category" in df.columns and category_pattern != ".*":
            cat_mask = df["category"].str.contains(category_pattern, case=False, na=False, regex=True)
            mask = param_mask & cat_mask
        else:
            mask = param_mask
        
        filtered = df[mask]
        
        if filtered.empty:
            return []
        
        results = []
        for _, row in filtered.iterrows():
            val = self._to_float(row.get("value"))
            if val is None:
                continue
            time_str = row["timestamp"].strftime("%H:%M") if pd.notna(row["timestamp"]) else "?"
            results.append((val, time_str))
        
        results.sort(key=lambda x: x[1])
        return results

    def _check_ecmella(self) -> int:
        """Prüft ob sowohl ECMO als auch Impella am Tag aktiv sind."""
        ecmo_df = self.get_source_data("ecmo")
        impella_df = self.get_source_data("impella")
        return 1 if (not ecmo_df.empty and not impella_df.empty) else 0
