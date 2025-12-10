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

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Tuple, Type
from datetime import date, time
import pandas as pd

from schemas.db_schemas.base import BaseExportModel


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
        redcap_repeat_instance: int,
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
    
    @abstractmethod
    def create_entry(self) -> BaseExportModel:
        """
        Erstellt ein Export-Model mit aggregierten Werten.
        
        Muss von Subklassen implementiert werden.
        """
        pass
    
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
            # Wenn Daten direkt übergeben wurden, nach source_type filtern
            if "source_type" in df.columns:
                # source_type kann verschieden benannt sein - case-insensitive match
                mask = df["source_type"].str.lower().str.contains(source.lower(), na=False)
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
        
        # Numerische Werte
        values = pd.to_numeric(filtered["value"], errors="coerce").dropna()
        if values.empty:
            return None
        
        # Strategie anwenden
        if self.value_strategy == "nearest" and self.nearest_time:
            return self._get_nearest_value(filtered, values)
        elif self.value_strategy == "median":
            return float(values.median())
        elif self.value_strategy == "mean":
            return float(values.mean())
        elif self.value_strategy == "first":
            return float(values.iloc[0])
        elif self.value_strategy == "last":
            return float(values.iloc[-1])
        
        # Default: median
        return float(values.median())
    
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
        df["_value_numeric"] = pd.to_numeric(df["value"], errors="coerce")
        
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
            try:
                val = float(row["value"])
                time_str = row["timestamp"].strftime("%H:%M") if pd.notna(row["timestamp"]) else "?"
                results.append((val, time_str))
            except (ValueError, TypeError):
                continue
        
        results.sort(key=lambda x: x[1])
        return results
