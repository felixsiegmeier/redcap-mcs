from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Type
import pandas as pd

from schemas.app_state_schemas.app_state import AppState

if TYPE_CHECKING:  # pragma: no cover - typing helper guard
    from .state_provider import StateProvider


class DataManager:
    """Handles state mutation, parsing and write operations for the StateProvider."""

    def __init__(self, provider: "StateProvider") -> None:
        self._provider = provider

    def update_state(self, **kwargs) -> None:
        state = self._provider.get_state()
        for key, value in kwargs.items():
            if hasattr(state, key):
                setattr(state, key, value)
        self._provider.save_state(state)

    def parse_data_to_state(self, df: Any) -> AppState:
        state = self._provider.get_state()
        
        # Ensure timestamp is datetime
        if "timestamp" in df.columns:
             df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        
        state.data = df
        
        if not df.empty and "timestamp" in df.columns:
            time_range_dt = (df["timestamp"].min(), df["timestamp"].max())
            print(f"Data time range: {time_range_dt[0]} - {time_range_dt[1]}")
            state.time_range = time_range_dt
            state.selected_time_range = time_range_dt
        
        # Update device times if available
        # Note: This relies on query_manager working with the new state.data
        try:
            ecmo_ranges = self._provider.query_manager.get_device_time_ranges("ecmo")
            if ecmo_ranges:
                earliest_start = min(range_.start for range_ in ecmo_ranges)
                state.nearest_ecls_time = earliest_start.time()

            impella_ranges = self._provider.query_manager.get_device_time_ranges("impella")
            if impella_ranges:
                earliest_start = min(range_.start for range_ in impella_ranges)
                state.nearest_impella_time = earliest_start.time()
        except Exception as e:
            print(f"Warning: Could not calculate device times: {e}")

        state.last_updated = datetime.now()

        self._provider.save_state(state)
        return state

    def reset_state(self) -> None:
        self._provider.save_state(AppState())

    def set_selected_time_range(self, start_date, end_date) -> None:
        print(f"Setting selected time range: {start_date} - {end_date}")
        state = self._provider.get_state()
        state.selected_time_range = (start_date, end_date)
        self._provider.save_state(state)

    def update_lab_form_field(self, index: int, field: str, value: Any) -> None:
        state = self._provider.get_state()
        if state.lab_form is None or index >= len(state.lab_form):
            return

        setattr(state.lab_form[index], field, value)

        if field == "pct":
            setattr(state.lab_form[index], "post_pct", 1.0 if value is not None else 0.0)
        elif field == "crp":
            setattr(state.lab_form[index], "post_crp", 1.0 if value is not None else 0.0)
        elif field == "act":
            setattr(state.lab_form[index], "post_act", 1.0 if value is not None else 0.0)
        elif field in ["fhb", "haptoglobin", "bili"]:
            fhb_val = getattr(state.lab_form[index], "fhb", None)
            hapt_val = getattr(state.lab_form[index], "haptoglobin", None)
            bili_val = getattr(state.lab_form[index], "bili", None)
            hemolysis_val = 1.0 if (fhb_val is not None) or (hapt_val is not None) or (bili_val is not None) else 0.0
            setattr(state.lab_form[index], "hemolysis", hemolysis_val)

        self._provider.save_state(state)
