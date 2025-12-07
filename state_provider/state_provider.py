import streamlit as st
from datetime import datetime, time
from typing import Any, Dict, List, Optional, Tuple

from pandas import DataFrame

from schemas.app_state_schemas.app_state import AppState, Views
from schemas.db_schemas.lab import LabModel

from .data_manager import DataManager
from .query_manager import DeviceTimeRange, QueryManager


class StateProvider:
    """Central access point for application state, delegating to query and data managers."""

    def __init__(self) -> None:
        self._state_key = "app_state"
        self.query_manager = QueryManager(self)
        self.data_manager = DataManager(self)

    def get_state(self) -> AppState:
        if self._state_key not in st.session_state:
            st.session_state[self._state_key] = AppState()
        return st.session_state[self._state_key]

    def save_state(self, state: AppState) -> None:
        st.session_state[self._state_key] = state

    def update_state(self, **kwargs) -> None:
        self.data_manager.update_state(**kwargs)

    def parse_data_to_state(self, df: DataFrame) -> AppState:
        return self.data_manager.parse_data_to_state(df)

    def reset_state(self) -> None:
        self.data_manager.reset_state()

    def has_parsed_data(self) -> bool:
        return self.query_manager.has_parsed_data()

    def query_data(self, data_source: str, filters: Optional[Dict[str, Any]] = None) -> DataFrame:
        return self.query_manager.query_data(data_source, filters)

    def has_device_past_24h(self, device: str, date_value: datetime) -> bool:
        return self.query_manager.has_device_past_24h(device, date_value)

    def has_mcs_records_past_24h(self, date_value: datetime) -> bool:
        return self.query_manager.has_mcs_records_past_24h(date_value)

    def get_record_id(self) -> Optional[str]:
        return self.query_manager.get_record_id()

    def get_value_strategy(self) -> str:
        return self.query_manager.get_value_strategy()

    def get_nearest_ecls_time(self) -> Optional[time]:
        return self.query_manager.get_nearest_ecls_time()

    def get_nearest_impella_time(self) -> Optional[time]:
        return self.query_manager.get_nearest_impella_time()

    def get_time_range(self) -> Optional[Tuple[datetime, datetime]]:
        return self.query_manager.get_time_range()

    def get_device_time_ranges(self, device: str) -> List[DeviceTimeRange]:
        return self.query_manager.get_device_time_ranges(device)

    def get_time_of_mcs(self, date_value: datetime) -> int:
        return self.query_manager.get_time_of_mcs(date_value)

    def get_selected_view(self) -> Optional[Views]:
        return self.query_manager.get_selected_view()

    def set_selected_time_range(self, start_date, end_date) -> None:
        self.data_manager.set_selected_time_range(start_date, end_date)

    def get_selected_time_range(self) -> Optional[Tuple[datetime, datetime]]:
        return self.query_manager.get_selected_time_range()

    def get_vitals_value(self, date_value: datetime, parameter: str, value_strategy: str = "median") -> Optional[float]:
        return self.query_manager.get_vitals_value(date_value, parameter, value_strategy)

    def get_vasoactive_agents_df(self, date_value: datetime, agent: str) -> DataFrame:
        return self.query_manager.get_vasoactive_agents_df(date_value, agent)

    def get_respiratory_value(self, date_value: datetime, parameter: str, value_strategy: str = "median") -> Optional[float]:
        return self.query_manager.get_respiratory_value(date_value, parameter, value_strategy)

    def get_respiration_type(self, date_value: datetime) -> Optional[str]:
        return self.query_manager.get_respiration_type(date_value)

    def get_lab_form(self) -> Optional[List[LabModel]]:
        return self.query_manager.get_lab_form()

    def update_lab_form_field(self, index: int, field: str, value: Any) -> None:
        self.data_manager.update_lab_form_field(index, field, value)


state_provider = StateProvider()