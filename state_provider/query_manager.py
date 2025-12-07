from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, Optional, Tuple, List

import pandas as pd

from schemas.app_state_schemas.app_state import AppState

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing helper
    from .state_provider import StateProvider

logger = logging.getLogger(__name__)


@dataclass
class DeviceTimeRange:
    device: str
    start: datetime
    end: datetime

    def __iter__(self):
        return iter((self.device, self.start, self.end))


class QueryManager:
    """Encapsulates read-only access to application state and parsed data queries."""

    # Mapping from old data_source names to new CSV source_type values
    SOURCE_MAPPING = {
        "lab": ["Lab"],
        "vitals": ["Vitals", "Vitalparameter (manuell)"],
        "medication": ["Medikation", "Medication"],
        "ecmo": ["ECMO"],
        "impella": ["IMPELLA"],
        "crrt": ["HÄMOFILTER", "CRRT"],
        "respiratory": ["Beatmung", "Respiratory"],
        "fluidbalance": ["Fluidbalance", "Bilanz"],
        "nirs": ["NIRS"],
        "patient_info": ["PatientInfo"]
    }

    def __init__(self, provider: "StateProvider") -> None:
        self._provider = provider

    def _get_state(self) -> AppState:
        return self._provider.get_state()

    def has_parsed_data(self) -> bool:
        state = self._get_state()
        return state.data is not None and not state.data.empty

    def query_data(self, data_source: str, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Query parsed datasets with filter and aggregation options."""
        filters = filters or {}
        state = self._get_state()
        
        if state.data is None or state.data.empty:
            return pd.DataFrame()

        df = state.data
        
        # 1. Filter by Data Source
        if data_source == "devices":
            device_sources = self.SOURCE_MAPPING.get("ecmo", []) + \
                             self.SOURCE_MAPPING.get("impella", []) + \
                             self.SOURCE_MAPPING.get("crrt", [])
            filtered_df = df[df["source_type"].isin(device_sources)].copy()
        elif data_source in self.SOURCE_MAPPING:
            target_sources = self.SOURCE_MAPPING[data_source]
            filtered_df = df[df["source_type"].isin(target_sources)].copy()
        elif data_source == "all":
            filtered_df = df.copy()
        else:
            filtered_df = df[df["source_type"].str.lower() == data_source.lower()].copy()
            if filtered_df.empty:
                logger.warning("Unknown data source requested: %s", data_source)
                return pd.DataFrame()

        if filtered_df.empty:
            return pd.DataFrame()

        # 2. Apply Filters
        
        # Timestamp Filter
        timestamp_filter = filters.get("timestamp")
        if timestamp_filter is not None and "timestamp" in filtered_df.columns:
            if isinstance(timestamp_filter, datetime):
                target_date = timestamp_filter.date()
                filtered_df = filtered_df[filtered_df["timestamp"].dt.date == target_date]
            elif isinstance(timestamp_filter, date):
                filtered_df = filtered_df[filtered_df["timestamp"].dt.date == timestamp_filter]
            elif isinstance(timestamp_filter, (list, tuple)) and len(timestamp_filter) == 2:
                start, end = timestamp_filter
                if isinstance(start, datetime):
                    filtered_df = filtered_df[(filtered_df["timestamp"] >= start) & (filtered_df["timestamp"] <= end)]
                elif isinstance(start, date):
                    start_dt = datetime.combine(start, time.min)
                    end_dt = datetime.combine(end, time.max)
                    filtered_df = filtered_df[(filtered_df["timestamp"] >= start_dt) & (filtered_df["timestamp"] <= end_dt)]

        # Other Column Filters
        known_keys = {"timestamp", "value_strategy", "nearest", "limit", "nearest_time"}
        for col, val in filters.items():
            if col in known_keys:
                continue
            if col not in filtered_df.columns:
                continue
            
            if isinstance(val, (list, tuple, set)):
                filtered_df = filtered_df[filtered_df[col].isin(list(val))]
            else:
                if isinstance(val, str) and pd.api.types.is_string_dtype(filtered_df[col]):
                     filtered_df = filtered_df[filtered_df[col].astype(str).str.lower() == val.lower()]
                else:
                    filtered_df = filtered_df[filtered_df[col] == val]

        # 3. Value Strategy
        value_strategy = filters.get("value_strategy")
        if value_strategy:
            filtered_df = self._apply_value_strategy(filtered_df, value_strategy, filters)

        return filtered_df.reset_index(drop=True)

    def _apply_value_strategy(self, df: pd.DataFrame, strategy: Any, filters: Dict) -> pd.DataFrame:
        if df.empty:
            return df

        if isinstance(strategy, dict) and "nearest" in strategy:
            nearest_time = strategy["nearest"]
            if isinstance(nearest_time, time) and "timestamp" in df.columns:
                # Find nearest row to time for each parameter/category combination?
                # Or just one nearest row overall?
                # Assuming we want nearest for each parameter if multiple exist.
                
                # Helper to find nearest in a group
                def get_nearest(group):
                    times = group["timestamp"].dt.time
                    target_seconds = nearest_time.hour * 3600 + nearest_time.minute * 60 + nearest_time.second
                    
                    # Calculate diff in seconds
                    def time_diff(t):
                        s = t.hour * 3600 + t.minute * 60 + t.second
                        return abs(s - target_seconds)
                    
                    # This is slow but correct
                    min_diff = min(times.apply(time_diff))
                    # Filter rows with min_diff
                    # This is a bit complex for a lambda, let's simplify:
                    # Just sort by diff and take head(1)
                    group["_diff"] = times.apply(time_diff)
                    return group.sort_values("_diff").head(1).drop(columns=["_diff"])

                # Group by parameter if it exists, else just return nearest overall
                if "parameter" in df.columns:
                    return df.groupby("parameter", group_keys=False).apply(get_nearest)
                else:
                    return get_nearest(df.copy())

        elif strategy == "median":
             # Only for numeric values
             if "value" in df.columns:
                df["value_numeric"] = pd.to_numeric(df["value"], errors="coerce")
                if "parameter" in df.columns:
                    # Return median per parameter
                    # We need to preserve other columns? Usually aggregation loses detail.
                    # Let's return a DF with parameter and value.
                    res = df.groupby("parameter")["value_numeric"].median().reset_index()
                    res.rename(columns={"value_numeric": "value"}, inplace=True)
                    return res
                else:
                    val = df["value_numeric"].median()
                    return pd.DataFrame({"value": [val]})
        
        return df

    def has_device_past_24h(self, device: str, date_value: datetime) -> bool:
        df = self.query_data(device)
        if df.empty:
            return False
        
        cutoff = date_value - timedelta(hours=24)
        recent = df[(df["timestamp"] >= cutoff) & (df["timestamp"] <= date_value)]
        return not recent.empty

    def has_mcs_records_past_24h(self, date_value: datetime) -> bool:
        return self.has_device_past_24h("ecmo", date_value) or self.has_device_past_24h("impella", date_value)

    def get_record_id(self) -> Optional[str]:
        state = self._get_state()
        return state.record_id

    def get_value_strategy(self) -> str:
        state = self._get_state()
        return state.value_strategy

    def get_nearest_ecls_time(self) -> Optional[time]:
        state = self._get_state()
        return state.nearest_ecls_time

    def get_nearest_impella_time(self) -> Optional[time]:
        state = self._get_state()
        return state.nearest_impella_time

    def get_time_range(self) -> Optional[Tuple[datetime, datetime]]:
        state = self._get_state()
        return state.time_range

    def get_device_time_ranges(self, device: str) -> List[DeviceTimeRange]:
        df = self.query_data(device)
        if df.empty:
            return []
        
        start = df["timestamp"].min()
        end = df["timestamp"].max()
        return [DeviceTimeRange(device, start, end)]

    def get_time_of_mcs(self, date_value: datetime) -> int:
        # Simplified: return 0 as placeholder
        return 0

    def get_selected_view(self) -> Optional[Any]:
        state = self._get_state()
        return state.selected_view

    def get_selected_time_range(self) -> Optional[Tuple[datetime, datetime]]:
        state = self._get_state()
        return state.selected_time_range

    def get_vitals_value(self, date_value: datetime, parameter: str, value_strategy: str = "median") -> Optional[float]:
        df = self.query_data("vitals", {"timestamp": date_value, "parameter": parameter})
        if df.empty:
            return None
        
        vals = pd.to_numeric(df["value"], errors="coerce").dropna()
        if vals.empty:
            return None
            
        if value_strategy == "median":
            return float(vals.median())
        elif value_strategy == "mean":
            return float(vals.mean())
        elif value_strategy == "max":
            return float(vals.max())
        elif value_strategy == "min":
            return float(vals.min())
        
        return float(vals.iloc[0])

    def get_vasoactive_agents_df(self, date_value: datetime, agent: str) -> pd.DataFrame:
        # Adapted to new structure
        df = self.query_data("medication", {"timestamp": date_value})
        if df.empty:
            return pd.DataFrame()
        
        # Filter by agent name in 'parameter' or 'category' or 'value'?
        # Usually medication name is in 'parameter' or 'category'.
        # Let's check 'parameter' first.
        mask = df["parameter"].astype(str).str.contains(agent, case=False, na=False)
        return df[mask]

    def get_respiratory_value(self, date_value: datetime, parameter: str, value_strategy: str = "median") -> Optional[float]:
        df = self.query_data("respiratory", {"timestamp": date_value, "parameter": parameter})
        if df.empty:
            return None
            
        vals = pd.to_numeric(df["value"], errors="coerce").dropna()
        if vals.empty:
            return None
            
        if value_strategy == "median":
            return float(vals.median())
        
        return float(vals.iloc[0])

    def get_respiration_type(self, date_value: datetime) -> Optional[str]:
        df = self.query_data("respiratory", {"timestamp": date_value, "parameter": "Beatmungsmodus"})
        if not df.empty:
            return str(df.iloc[0]["value"])
        return None

    def get_lab_form(self) -> Optional[List[Any]]:
        state = self._get_state()
        return state.lab_form
