import streamlit as st
from schemas.app_state_schemas.app_state import AppState, ParsedData, Views
from datetime import datetime, date, timedelta, time
import pandas as pd
from typing import Any, Callable, Dict, Optional, Tuple, Union, List
# from schemas.db_schemas.vitals import VentilationType  # not yet defined in db schema
import logging
from dataclasses import dataclass

# Import der neuen DataParser Klasse
from services.data_parser import DataParser
from schemas.parse_schemas.vitals import VitalsModel
from schemas.parse_schemas.lab import LabModel as ParseLabModel
from schemas.db_schemas.lab import LabModel

logger = logging.getLogger(__name__)

@dataclass
class DeviceTimeRange:
    device: str
    start: datetime
    end: datetime

    def __iter__(self):
        return iter((self.device, self.start, self.end))

class StateProvider: 
    def __init__(self, data_parser: Optional[DataParser] = None):
        self._state_key = "app_state"
        self.data_parser = data_parser
    
    def get_state(self) -> AppState:
        if self._state_key not in st.session_state:
            st.session_state[self._state_key] = AppState()
        return st.session_state[self._state_key]
    
    def save_state(self, state: AppState) -> None:
        st.session_state[self._state_key] = state
    
    def update_state(self, **kwargs) -> None:
        state = self.get_state()
        for key, value in kwargs.items():
            if hasattr(state, key):
                setattr(state, key, value)
        self.save_state(state)
    
    def parse_data_to_state(self, file: str, delimiter: str = ";") -> AppState:
        state = self.get_state()
        
        # Verwende DataParser für alle Parsing-Operationen
        parser = DataParser(file, delimiter)
        
        # Parse alle Datentypen mit dem DataParser
        vitals = parser._parse_table_data("Vitaldaten", VitalsModel)
        respiratory = parser.parse_respiratory_data()
        lab = parser._parse_table_data("Labor", ParseLabModel, skip_first=True, clean_lab=True)
        ecmo = parser.parse_from_all_patient_data('ECMO')
        impella = parser.parse_from_all_patient_data('IMPELLA')
        crrt = parser.parse_from_all_patient_data('HÄMOFILTER')
        medication = parser.parse_medication_logic()
        nirs = parser.parse_nirs_logic()
        time_range = parser.get_date_range_from_df(vitals)
        # Convert date tuple to datetime tuple
        if time_range and time_range[0] and time_range[1]:
            time_range_dt = (datetime.combine(time_range[0], datetime.min.time()), 
                           datetime.combine(time_range[1], datetime.max.time()))
        else:
            time_range_dt = None
        fluidbalance = parser.parse_fluidbalance_logic()
        all_patient_data = parser.parse_all_patient_data()
        
        # Aktualisiere State mit geparsten Daten
        state.parsed_data = ParsedData(
            crrt=crrt,
            ecmo=ecmo,
            impella=impella,
            lab=lab,
            medication=medication,
            respiratory=respiratory,
            vitals=vitals,
            fluidbalance=fluidbalance,
            nirs=nirs,
            all_patient_data=all_patient_data
        )
        
        # Set implant times from device time ranges
        ecmo_ranges = self.get_device_time_ranges('ecmo')
        if ecmo_ranges:
            earliest_start = min(range.start for range in ecmo_ranges)
            state.nearest_ecls_time = earliest_start.time()
        
        impella_ranges = self.get_device_time_ranges('impella')
        if impella_ranges:
            earliest_start = min(range.start for range in impella_ranges)
            state.nearest_impella_time = earliest_start.time()
        
        state.time_range = time_range_dt
        state.selected_time_range = time_range_dt
        state.last_updated = datetime.now()
        
        self.save_state(state)
        return state
    
    def reset_state(self) -> None:
        """Setzt den State auf einen neuen, leeren AppState zurück."""
        st.session_state[self._state_key] = AppState()
    
    def has_parsed_data(self) -> bool:
        state = self.get_state()
        return state.parsed_data is not None

    def query_data(self, data_source: str, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        Generalisierte Methode zum Abfragen von geparsten Daten mit Filtern und Aggregation.

        Diese Methode ermöglicht das flexible Abfragen von geparsten medizinischen Daten aus verschiedenen Quellen.
        Sie unterstützt sowohl vordefinierte Filter (wie timestamp, parameter, category) als auch beliebige
        zusätzliche Spaltenfilter, um eine maximale Flexibilität zu gewährleisten, ohne die bestehende API zu brechen.

        Parameter:
        - data_source (str): Der Name der Datenquelle (z.B. "medication", "lab", "devices").
    - filters (Optional[Dict[str, Any]]): Ein Dictionary mit Filtern. Bekannte Schlüssel:
            * "timestamp": Einzelnes datetime-Objekt (für Datum) oder Liste/Tupel [start, end] für Zeitbereich.
            * "parameter": Filter für die 'parameter'-Spalte (String oder Liste).
            * "category": Filter für die 'category'-Spalte (String oder Liste).
            * "source_header": Filter für die 'source_header'-Spalte (String oder Liste).
            * "time_range": Filter für die 'time_range'-Spalte (String oder Liste).
            * "limit": Integer, um die Anzahl der Ergebnisse zu begrenzen (z.B. 100 für die ersten 100 Zeilen).
            * "value_strategy": Aggregation/Strategie ("median", "mean", "first", "last", "nearest") für numerische Werte.
            * "nearest_time": datetime.time-Objekt, das nur bei value_strategy="nearest" verwendet wird, um den Wert am nächsten an dieser Zeit zu finden.
            * Beliebige weitere Schlüssel werden als direkte Spaltenfilter behandelt (z.B. "medication": "Aspirin").

        Rückgabewert:
        - pd.DataFrame: Gefilterte und optional aggregierte Daten. Leerer DataFrame, wenn keine Daten vorhanden.

        Beispiele:
        - query_data("medication", {"parameter": "Aspirin"})  # Filtert nach Parameter
        - query_data("lab", {"timestamp": [start_date, end_date]})  # Zeitbereich
        - query_data("devices", {"medication": "Heparin", "limit": 50})  # Zusätzlicher Spaltenfilter + Limit
        - query_data("vitals", {"parameter": "HR", "value_strategy": "median"})  # Aggregation
        - query_data("vitals", {"parameter": "HR", "value_strategy": "nearest", "nearest_time": time(12,0)})  # Wert am nächsten an 12:00        Hinweise:
        - Filter werden sequentiell angewendet: Zuerst bekannte Filter, dann unbekannte Spaltenfilter, dann Limit, dann Aggregation.
        - Bei unbekannten Spaltenfiltern wird die Spalte ignoriert, wenn sie nicht existiert.
        - Aggregation erfordert eine 'value'-Spalte und funktioniert nur bei numerischen Werten.
        - Diese Erweiterung ermöglicht z.B. direkte Filterung nach "medication" ohne Nachbearbeitung.
        """
        filters = filters or {}
        state = self.get_state()
        if not state.parsed_data:
            return pd.DataFrame()

        df: Optional[pd.DataFrame] = None

        # Datenquelle laden: Spezielle Behandlung für "devices" (kombiniert alle Patientendaten)
        if data_source == "devices":
            all_patient_data = getattr(state.parsed_data, "all_patient_data", {}) or {}
            device_frames: list[pd.DataFrame] = []
            for source_header, categories in all_patient_data.items():
                if not isinstance(categories, dict):
                    continue
                for category, category_df in categories.items():
                    if isinstance(category_df, pd.DataFrame) and not category_df.empty:
                        current = category_df.copy()
                        current["source_header"] = source_header
                        current["category"] = category
                        device_frames.append(current)
            df = pd.concat(device_frames, ignore_index=True) if device_frames else pd.DataFrame()
        # Für andere Datenquellen: Direkt aus parsed_data holen
        elif hasattr(state.parsed_data, data_source):
            candidate = getattr(state.parsed_data, data_source)
            if isinstance(candidate, pd.DataFrame):
                df = candidate
            else:
                df = pd.DataFrame()
        else:
            logger.warning("Unknown data source requested: %s", data_source)
            return pd.DataFrame()

        if df is None or df.empty:
            return pd.DataFrame()

        filtered_df = df.copy()

        # Timestamp-Spalte in datetime konvertieren, falls vorhanden
        if "timestamp" in filtered_df.columns:
            filtered_df["timestamp"] = pd.to_datetime(filtered_df["timestamp"], errors="coerce")

        # Hilfsfunktion zum Anwenden von Filtern auf Spalten
        def _apply_filter(frame: pd.DataFrame, column: str, value: Any) -> pd.DataFrame:
            if column not in frame.columns:
                return frame  # Spalte existiert nicht -> keine Filterung
            if isinstance(value, str):
                # String-Filter: Case-insensitive Contains-Suche
                return frame[frame[column].astype(str).str.contains(value, na=False, case=False)]
            if isinstance(value, (list, tuple, set)):
                # Listen-Filter: Prüfen, ob Wert in der Liste ist
                return frame[frame[column].isin(list(value))]
            # Spezielle Behandlung für date-Objekte: Vergleiche mit datetime-Spalten über .dt.date
            if isinstance(value, date) and not isinstance(value, datetime):
                if pd.api.types.is_datetime64_any_dtype(frame[column]):
                    return frame[frame[column].dt.date == value]
                else:
                    return frame[frame[column] == value]
            # Andere Typen: Exakte Übereinstimmung (z.B. Zahlen, datetime)
            return frame[frame[column] == value]

        # 1. Timestamp-Filter anwenden (spezielle Logik für Datum oder Bereich)
        timestamp_filter = filters.get("timestamp")
        if timestamp_filter is not None and "timestamp" in filtered_df.columns:
            if isinstance(timestamp_filter, datetime):
                target_date = timestamp_filter.date()
                filtered_df = filtered_df[filtered_df["timestamp"].dt.date == target_date]
            elif isinstance(timestamp_filter, date):
                filtered_df = filtered_df[filtered_df["timestamp"].dt.date == timestamp_filter]
            elif (
                isinstance(timestamp_filter, (list, tuple))
                and len(timestamp_filter) == 2
                and all(isinstance(item, datetime) for item in timestamp_filter)
            ):
                start, end = timestamp_filter
                if start > end:
                    start, end = end, start  # Sicherstellen, dass start <= end
                filtered_df = filtered_df[
                    (filtered_df["timestamp"] >= start) & (filtered_df["timestamp"] <= end)
                ]

        # 2. Bekannte Filter anwenden (parameter, category, source_header, time_range)
        for key in ("parameter", "category", "source_header", "time_range"):
            value = filters.get(key)
            if value is not None:
                filtered_df = _apply_filter(filtered_df, key, value)

        # 3. Unbekannte Filter als direkte Spaltenfilter anwenden
        # Bekannte Schlüssel, die bereits behandelt wurden oder später behandelt werden
        known_keys = {"timestamp", "parameter", "category", "source_header", "time_range", "value_strategy", "nearest_time", "limit"}
        # Alle anderen Schlüssel in filters als Spaltenfilter interpretieren
        for key, value in filters.items():
            if key not in known_keys:
                filtered_df = _apply_filter(filtered_df, key, value)

        # 4. Limit anwenden, falls angegeben
        limit = filters.get("limit")
        if isinstance(limit, int) and limit >= 0:
            filtered_df = filtered_df.head(limit)

        # 5. Aggregation (value_strategy) anwenden, falls angegeben
        value_strategy = filters.get("value_strategy")
        if value_strategy and not filtered_df.empty and "value" in filtered_df.columns:
            # Gruppierungsspalten bestimmen (parameter, category und date falls vorhanden)
            group_cols = [col for col in ("parameter", "category") if col in filtered_df.columns]
            
            # Wenn timestamp vorhanden ist, füge date als Gruppierungsspalte hinzu
            if "timestamp" in filtered_df.columns:
                # Erstelle temporäre date-Spalte für Gruppierung
                temp_df = filtered_df.copy()
                temp_df["date"] = temp_df["timestamp"].dt.date
                group_cols.insert(0, "date")  # date zuerst
                filtered_df = temp_df

            # Hilfsfunktion für numerische Aggregation
            def _aggregate_numeric(series: pd.Series, agg: str) -> float:
                numeric = pd.to_numeric(series, errors="coerce").dropna()
                if numeric.empty:
                    return float("nan")
                if agg == "median":
                    return float(numeric.median())
                if agg == "mean":
                    return float(numeric.mean())
                raise ValueError(f"Unsupported aggregation '{agg}'")

            # Median oder Mean: Numerische Aggregation
            if isinstance(value_strategy, str) and value_strategy in {"median", "mean"}:
                if group_cols:
                    aggregated = (
                        filtered_df.groupby(group_cols)["value"]
                        .apply(lambda s: _aggregate_numeric(s, value_strategy))
                        .reset_index(name="value")
                    )
                else:
                    aggregated = pd.DataFrame(
                        {"value": [_aggregate_numeric(filtered_df["value"], value_strategy)]}
                    )
                # Wenn date hinzugefügt wurde, stelle sicher dass es datetime.date ist und setze als erste Spalte
                if "date" in aggregated.columns:
                    # Stelle sicher, dass date datetime.date ist (groupby kann es schon konvertiert haben)
                    if pd.api.types.is_datetime64_any_dtype(aggregated["date"]):
                        aggregated["date"] = aggregated["date"].dt.date
                    # Setze date als erste Spalte
                    cols = ["date"] + [col for col in aggregated.columns if col != "date"]
                    aggregated = aggregated[cols]
                return aggregated.reset_index(drop=True)

            # First oder Last: Zeitbasierte Auswahl (sortiert nach timestamp)
            if isinstance(value_strategy, str) and value_strategy in {"first", "last"}:
                if "timestamp" in filtered_df.columns:
                    filtered_df = filtered_df.sort_values("timestamp")
                if group_cols:
                    grouped = filtered_df.groupby(group_cols, as_index=False)
                    result = grouped.first() if value_strategy == "first" else grouped.last()
                else:
                    result = filtered_df.iloc[[0]] if value_strategy == "first" else filtered_df.iloc[[-1]]
                return result.reset_index(drop=True)

            # Nearest: Wert am nächsten an einem Anker-Zeitpunkt
            if isinstance(value_strategy, str) and value_strategy == "nearest":
                nearest_time = filters.get("nearest_time")
                if not isinstance(nearest_time, time):
                    logger.warning("nearest_time required for value_strategy='nearest', got %s", type(nearest_time))
                    return filtered_df.reset_index(drop=True)
                
                # Stelle sicher, dass timestamp-Spalte vorhanden ist
                if "timestamp" not in filtered_df.columns:
                    logger.warning("Nearest selection requires 'timestamp' column in data")
                    return filtered_df.reset_index(drop=True)
                
                # Temporäres DataFrame mit date-Spalte für tägliche Gruppierung
                temp_df = filtered_df.copy()
                temp_df["date"] = temp_df["timestamp"].dt.date
                
                # Da nearest pro Tag aggregiert, und gefilterte Daten nur einen Tag haben, direkt den nächsten Wert finden
                def _find_nearest_value(df: pd.DataFrame) -> pd.Series:
                    if df.empty:
                        return pd.Series()  # Leere Series für empty case
                    
                    # Extrahiere Uhrzeiten und berechne Differenzen in Sekunden
                    times = df["timestamp"].dt.time
                    anchor_seconds = nearest_time.hour * 3600 + nearest_time.minute * 60 + nearest_time.second
                    df_seconds = [t.hour * 3600 + t.minute * 60 + t.second for t in times]
                    diffs = [abs(gs - anchor_seconds) for gs in df_seconds]
                    
                    # Index des minimalen Abstands
                    min_idx = diffs.index(min(diffs))
                    
                    # Rückgabe der kompletten Zeile
                    return df.iloc[min_idx]
                
                if temp_df.empty:
                    aggregated = pd.DataFrame()
                else:
                    nearest_row = _find_nearest_value(temp_df)
                    aggregated = pd.DataFrame([nearest_row])
                
                return aggregated

            logger.warning("Unknown value_strategy '%s' requested for %s", value_strategy, data_source)

        # Rückgabe des gefilterten DataFrames (ohne Aggregation)
        return filtered_df.reset_index(drop=True)

    def has_device_past_24h(self, device: str, date: datetime) -> bool:
        """Prüft, ob für das angegebene Device Daten in den letzten 24 Stunden vorliegen."""

        state = self.get_state()
        if not state.parsed_data:
            return False

        device_df = getattr(state.parsed_data, device, None)
        if not isinstance(device_df, pd.DataFrame) or device_df.empty:
            return False

        if "timestamp" not in device_df.columns:
            return False

        cutoff_time = date - timedelta(hours=24)
        timestamps = pd.to_datetime(device_df["timestamp"], errors="coerce").dropna()
        if timestamps.empty:
            return False

        return bool((timestamps >= cutoff_time).any())

    def has_mcs_records_past_24h(self, date: datetime) -> bool:
        """Prüft, ob ECMO- oder Impella-Daten in den letzten 24 Stunden vorhanden sind."""

        for device in ("ecmo", "impella"):
            if self.has_device_past_24h(device, date):
                return True
        return False

    def get_record_id(self) -> str | None:
        state = self.get_state()
        return state.record_id

    def get_value_strategy(self) -> str:
        state = self.get_state()
        return state.value_strategy

    def get_nearest_ecls_time(self) -> time | None:
        state = self.get_state()
        return state.nearest_ecls_time

    def get_nearest_impella_time(self) -> time | None:
        state = self.get_state()
        return state.nearest_impella_time

    def get_time_range(self) -> Optional[Tuple]:
        state = self.get_state()
        return state.time_range

    def get_device_time_ranges(self, device: str) -> list[DeviceTimeRange]:
        state = self.get_state()
        if not state.parsed_data:
            return []

        device_df = self.query_data(device)
        if not isinstance(device_df, pd.DataFrame) or device_df.empty:
            return []

        try:
            time_ranges = []
            for category in device_df["category"].unique():
                category_df = device_df[device_df["category"] == category]
                timestamps = pd.to_datetime(category_df["timestamp"], errors="coerce").dropna()
                if not timestamps.empty:
                    time_ranges.append(DeviceTimeRange(
                        device=category,
                        start=timestamps.min(),
                        end=timestamps.max()
                    ))
            return time_ranges
        except Exception:
            return []

    def get_time_of_mcs(self, date: datetime) -> int:
        """
        Berechnet die Anzahl der Tage seit dem Start des MCS (ECMO oder Impella).
        Gibt die Tage seit dem frühesten Startdatum zurück.
        """
        state = self.get_state()
        if not state.parsed_data:
            return 0

        earliest_start = None
        
        for device in ("ecmo", "impella"):
            try:
                device_df = getattr(state.parsed_data, device, None)
                if device_df is not None and not device_df.empty:
                    ts = pd.to_datetime(device_df["timestamp"], errors="coerce").dropna()
                    if not ts.empty:
                        device_start = ts.min()
                        if earliest_start is None or device_start < earliest_start:
                            earliest_start = device_start
            except Exception:
                continue

        if earliest_start is None:
            return 0
            
        # Berechne Tage seit MCS-Start
        days_since_start = (date - earliest_start).days
        return max(0, days_since_start)  # Negative Werte vermeiden

    def get_selected_view(self) -> Optional[Views]:
        state = self.get_state()
        return state.selected_view

    def set_selected_time_range(self, start_date, end_date) -> None:
        print(f"Setting selected time range: {start_date} - {end_date}")
        state = self.get_state()
        state.selected_time_range = (start_date, end_date)
        self.save_state(state)

    def get_selected_time_range(self) -> Optional[Tuple[datetime, datetime]]:
        state = self.get_state()
        return state.selected_time_range

    def get_vitals_value(self, date: datetime, parameter: str, value_strategy: str = "median") -> Optional[float]:
        """Deprecated: Use query_data('vitals', {'timestamp': date, 'parameter': parameter, 'value_strategy': value_strategy}) instead."""
        filtered = self.query_data('vitals', {'timestamp': date, 'parameter': parameter, 'value_strategy': value_strategy})
        if filtered.empty:
            return None
        # Assuming selection returns aggregated value
        if 'value' in filtered.columns and not filtered.empty:
            return float(filtered['value'].iloc[0])
        return None

    def get_vasoactive_agents_df(self, date: datetime, agent: str) -> pd.DataFrame:
        state = self.get_state()
        if not state.parsed_data:
            return pd.DataFrame()

        medication_df = getattr(state.parsed_data, "medication", None)
        if medication_df is None or medication_df.empty:
            return pd.DataFrame()

        filtered = medication_df[
            ((medication_df["start"].dt.date == date) | (medication_df["stop"].dt.date == date))
            & (medication_df["medication"].str.contains(agent, na=False))
        ]

        if filtered.empty:
            return pd.DataFrame()

        return filtered

    def get_respiratory_value(self, date: datetime, parameter: str, value_strategy: str = "median") -> Optional[float]:
        """Deprecated: Use query_data('respiratory', {'timestamp': date, 'parameter': parameter, 'value_strategy': value_strategy}) instead."""
        filtered = self.query_data('respiratory', {'timestamp': date, 'parameter': parameter, 'value_strategy': value_strategy})
        if filtered.empty:
            return None
        if 'value' in filtered.columns and not filtered.empty:
            return float(filtered['value'].iloc[0])
        return None

    def get_respiration_type(self, date: datetime) -> Optional[str]:
        pass
        # Hier weiter machen => evtl. anhand Vorhandensein Tubus, Beatmungseinstellungen (vorhandensein), HFNC-Vorhandensein

    def get_lab_form(self) -> Optional[List[LabModel]]:
        """Gibt die lab_form Liste zurück."""
        state = self.get_state()
        return state.lab_form

    def update_lab_form_field(self, index: int, field: str, value: Any) -> None:
        """Aktualisiert ein Feld in lab_form und berechnet abhängige Felder."""
        state = self.get_state()
        if state.lab_form is None or index >= len(state.lab_form):
            return
        
        setattr(state.lab_form[index], field, value)
        
        # Dynamische Berechnung der abhängigen Felder
        if field == "pct":
            setattr(state.lab_form[index], "post_pct", 1.0 if value is not None else 0.0)
        elif field == "crp":
            setattr(state.lab_form[index], "post_crp", 1.0 if value is not None else 0.0)
        elif field == "act":
            setattr(state.lab_form[index], "post_act", 1.0 if value is not None else 0.0)
        elif field in ["fhb", "haptoglobin", "bili"]:
            # Prüfe, ob mindestens einer der Hämolyseparameter einen Wert hat
            fhb_val = getattr(state.lab_form[index], "fhb", None)
            hapt_val = getattr(state.lab_form[index], "haptoglobin", None)
            bili_val = getattr(state.lab_form[index], "bili", None)
            hemolysis_val = 1.0 if (fhb_val is not None) or (hapt_val is not None) or (bili_val is not None) else 0.0
            setattr(state.lab_form[index], "hemolysis", hemolysis_val)
        
        self.save_state(state)

state_provider = StateProvider()