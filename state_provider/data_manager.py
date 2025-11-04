from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Type

from schemas.app_state_schemas.app_state import AppState, ParsedData
from schemas.parse_schemas.lab import LabModel as ParseLabModel
from schemas.parse_schemas.vitals import VitalsModel
from services.data_parser import DataParser
from services.utils import expand_date_range_to_bounds

if TYPE_CHECKING:  # pragma: no cover - typing helper guard
    from .state_provider import StateProvider


class DataManager:
    """Handles state mutation, parsing and write operations for the StateProvider."""

    def __init__(self, provider: "StateProvider", data_parser_cls: Type[DataParser] | None = None) -> None:
        self._provider = provider
        self._data_parser_cls = data_parser_cls or DataParser

    def update_state(self, **kwargs) -> None:
        state = self._provider.get_state()
        for key, value in kwargs.items():
            if hasattr(state, key):
                setattr(state, key, value)
        self._provider.save_state(state)

    def parse_data_to_state(self, file: str, delimiter: str = ";") -> AppState:
        state = self._provider.get_state()
        parser = self._data_parser_cls(file, delimiter)

        vitals = parser._parse_table_data("Vitaldaten", VitalsModel)
        respiratory = parser.parse_respiratory_data()
        lab = parser._parse_table_data("Labor", ParseLabModel, skip_first=True, clean_lab=True)
        ecmo = parser.parse_from_all_patient_data("ECMO")
        impella = parser.parse_from_all_patient_data("IMPELLA")
        crrt = parser.parse_from_all_patient_data("HÄMOFILTER")
        medication = parser.parse_medication_logic()
        nirs = parser.parse_nirs_logic()
        time_range = parser.get_date_range_from_df(vitals)

        time_range_dt = expand_date_range_to_bounds(time_range)

        fluidbalance = parser.parse_fluidbalance_logic()
        all_patient_data = parser.parse_all_patient_data()

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
            all_patient_data=all_patient_data,
        )

        ecmo_ranges = self._provider.query_manager.get_device_time_ranges("ecmo")  # type: ignore[attr-defined]
        if ecmo_ranges:
            earliest_start = min(range_.start for range_ in ecmo_ranges)
            state.nearest_ecls_time = earliest_start.time()

        impella_ranges = self._provider.query_manager.get_device_time_ranges("impella")  # type: ignore[attr-defined]
        if impella_ranges:
            earliest_start = min(range_.start for range_ in impella_ranges)
            state.nearest_impella_time = earliest_start.time()

        state.time_range = time_range_dt
        state.selected_time_range = time_range_dt
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
