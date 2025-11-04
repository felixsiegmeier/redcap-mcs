from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, Optional, Tuple

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

    def __init__(self, provider: "StateProvider") -> None:
        self._provider = provider

    def _get_state(self) -> AppState:
        return self._provider.get_state()

    def has_parsed_data(self) -> bool:
        state = self._get_state()
        return state.parsed_data is not None

    def query_data(self, data_source: str, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Query parsed datasets with filter and aggregation options."""
        filters = filters or {}
        state = self._get_state()
        if not state.parsed_data:
            return pd.DataFrame()

        df: Optional[pd.DataFrame] = None

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

        if "timestamp" in filtered_df.columns:
            filtered_df["timestamp"] = pd.to_datetime(filtered_df["timestamp"], errors="coerce")

        def _apply_filter(frame: pd.DataFrame, column: str, value: Any) -> pd.DataFrame:
            if column not in frame.columns:
                return frame
            if isinstance(value, str):
                return frame[frame[column].astype(str).str.contains(value, na=False, case=False)]
            if isinstance(value, (list, tuple, set)):
                return frame[frame[column].isin(list(value))]
            if isinstance(value, date) and not isinstance(value, datetime):
                if pd.api.types.is_datetime64_any_dtype(frame[column]):
                    return frame[frame[column].dt.date == value]
                return frame[frame[column] == value]
            return frame[frame[column] == value]

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
                    start, end = end, start
                filtered_df = filtered_df[
                    (filtered_df["timestamp"] >= start) & (filtered_df["timestamp"] <= end)
                ]

        for key in ("parameter", "category", "source_header", "time_range"):
            value = filters.get(key)
            if value is not None:
                filtered_df = _apply_filter(filtered_df, key, value)

        known_keys = {
            "timestamp",
            "parameter",
            "category",
            "source_header",
            "time_range",
            "value_strategy",
            "nearest_time",
            "limit",
        }
        for key, value in filters.items():
            if key not in known_keys:
                filtered_df = _apply_filter(filtered_df, key, value)

        limit = filters.get("limit")
        if isinstance(limit, int) and limit >= 0:
            filtered_df = filtered_df.head(limit)

        value_strategy = filters.get("value_strategy")
        if value_strategy and not filtered_df.empty and "value" in filtered_df.columns:
            group_cols = [col for col in ("parameter", "category") if col in filtered_df.columns]

            if "timestamp" in filtered_df.columns:
                temp_df = filtered_df.copy()
                temp_df["date"] = temp_df["timestamp"].dt.date
                group_cols.insert(0, "date")
                filtered_df = temp_df

            def _aggregate_numeric(series: pd.Series, agg: str) -> float:
                numeric = pd.to_numeric(series, errors="coerce").dropna()
                if numeric.empty:
                    return float("nan")
                if agg == "median":
                    return float(numeric.median())
                if agg == "mean":
                    return float(numeric.mean())
                raise ValueError(f"Unsupported aggregation '{agg}'")

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
                if "date" in aggregated.columns:
                    if pd.api.types.is_datetime64_any_dtype(aggregated["date"]):
                        aggregated["date"] = aggregated["date"].dt.date
                    cols = ["date"] + [col for col in aggregated.columns if col != "date"]
                    aggregated = aggregated[cols]
                return aggregated.reset_index(drop=True)

            if isinstance(value_strategy, str) and value_strategy in {"first", "last"}:
                if "timestamp" in filtered_df.columns:
                    filtered_df = filtered_df.sort_values("timestamp")
                if group_cols:
                    grouped = filtered_df.groupby(group_cols, as_index=False)
                    result = grouped.first() if value_strategy == "first" else grouped.last()
                else:
                    result = (
                        filtered_df.iloc[[0]]
                        if value_strategy == "first"
                        else filtered_df.iloc[[-1]]
                    )
                return result.reset_index(drop=True)

            if isinstance(value_strategy, str) and value_strategy == "nearest":
                nearest_time = filters.get("nearest_time")
                if not isinstance(nearest_time, time):
                    logger.warning(
                        "nearest_time required for value_strategy='nearest', got %s",
                        type(nearest_time),
                    )
                    return filtered_df.reset_index(drop=True)

                if "timestamp" not in filtered_df.columns:
                    logger.warning("Nearest selection requires 'timestamp' column in data")
                    return filtered_df.reset_index(drop=True)

                temp_df = filtered_df.copy()
                temp_df["date"] = temp_df["timestamp"].dt.date

                def _find_nearest_value(df: pd.DataFrame) -> pd.Series:
                    if df.empty:
                        return pd.Series()
                    times = df["timestamp"].dt.time
                    anchor_seconds = (
                        nearest_time.hour * 3600
                        + nearest_time.minute * 60
                        + nearest_time.second
                    )
                    df_seconds = [
                        t.hour * 3600 + t.minute * 60 + t.second for t in times
                    ]
                    diffs = [abs(gs - anchor_seconds) for gs in df_seconds]
                    min_idx = diffs.index(min(diffs))
                    return df.iloc[min_idx]

                if temp_df.empty:
                    aggregated = pd.DataFrame()
                else:
                    nearest_row = _find_nearest_value(temp_df)
                    aggregated = pd.DataFrame([nearest_row])

                return aggregated

            logger.warning("Unknown value_strategy '%s' requested for %s", value_strategy, data_source)

        return filtered_df.reset_index(drop=True)

    def has_device_past_24h(self, device: str, date_value: datetime) -> bool:
        state = self._get_state()
        if not state.parsed_data:
            return False

        device_df = getattr(state.parsed_data, device, None)
        if not isinstance(device_df, pd.DataFrame) or device_df.empty:
            return False

        if "timestamp" not in device_df.columns:
            return False

        cutoff_time = date_value - timedelta(hours=24)
        timestamps = pd.to_datetime(device_df["timestamp"], errors="coerce").dropna()
        if timestamps.empty:
            return False

        return bool((timestamps >= cutoff_time).any())

    def has_mcs_records_past_24h(self, date_value: datetime) -> bool:
        for device in ("ecmo", "impella"):
            if self.has_device_past_24h(device, date_value):
                return True
        return False

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

    def get_device_time_ranges(self, device: str) -> list[DeviceTimeRange]:
        state = self._get_state()
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
                    time_ranges.append(
                        DeviceTimeRange(
                            device=category,
                            start=timestamps.min(),
                            end=timestamps.max(),
                        )
                    )
            return time_ranges
        except Exception:
            return []

    def get_time_of_mcs(self, date_value: datetime) -> int:
        state = self._get_state()
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

        days_since_start = (date_value - earliest_start).days
        return max(0, days_since_start)

    def get_selected_view(self):
        state = self._get_state()
        return state.selected_view

    def get_selected_time_range(self) -> Optional[Tuple[datetime, datetime]]:
        state = self._get_state()
        return state.selected_time_range

    def get_vitals_value(
        self,
        date_value: datetime,
        parameter: str,
        value_strategy: str = "median",
    ) -> Optional[float]:
        filtered = self.query_data(
            "vitals",
            {"timestamp": date_value, "parameter": parameter, "value_strategy": value_strategy},
        )
        if filtered.empty:
            return None
        if "value" in filtered.columns and not filtered.empty:
            return float(filtered["value"].iloc[0])
        return None

    def get_vasoactive_agents_df(self, date_value: datetime, agent: str) -> pd.DataFrame:
        state = self._get_state()
        if not state.parsed_data:
            return pd.DataFrame()

        medication_df = getattr(state.parsed_data, "medication", None)
        if medication_df is None or medication_df.empty:
            return pd.DataFrame()

        filtered = medication_df[
            (
                (medication_df["start"].dt.date == date_value)
                | (medication_df["stop"].dt.date == date_value)
            )
            & (medication_df["medication"].str.contains(agent, na=False))
        ]

        if filtered.empty:
            return pd.DataFrame()

        return filtered

    def get_respiratory_value(
        self,
        date_value: datetime,
        parameter: str,
        value_strategy: str = "median",
    ) -> Optional[float]:
        filtered = self.query_data(
            "respiratory",
            {"timestamp": date_value, "parameter": parameter, "value_strategy": value_strategy},
        )
        if filtered.empty:
            return None
        if "value" in filtered.columns and not filtered.empty:
            return float(filtered["value"].iloc[0])
        return None

    def get_respiration_type(self, date_value: datetime) -> Optional[str]:
        return None

    def get_lab_form(self):
        state = self._get_state()
        return state.lab_form
