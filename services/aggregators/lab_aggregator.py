"""
Lab Aggregator - Laborwerte zu REDCap-Model.
"""

import logging

import pandas as pd
from typing import Optional, Dict
from datetime import date, time

from schemas.db_schemas.lab import LabModel, WithdrawalSite
from .base import BaseAggregator
from .mapping import LAB_REGISTRY

logger = logging.getLogger(__name__)


class LabAggregator(BaseAggregator):
    """Aggregiert Laborwerte zu einem LabModel."""

    INSTRUMENT_NAME = "labor"
    MODEL_CLASS = LabModel

    def __init__(
        self,
        date: date,
        record_id: str,
        redcap_event_name: str,
        redcap_repeat_instrument: str,
        redcap_repeat_instance: int,
        value_strategy: str = "median",
        nearest_time: Optional[time] = None,
        data: Optional[pd.DataFrame] = None
    ):
        super().__init__(
            date=date,
            record_id=record_id,
            redcap_event_name=redcap_event_name,
            redcap_repeat_instance=redcap_repeat_instance,
            value_strategy=value_strategy,
            nearest_time=nearest_time,
            data=data
        )
        self.redcap_repeat_instrument = redcap_repeat_instrument

    def create_entry(self) -> LabModel:
        """Erstellt ein LabModel mit aggregierten Werten."""

        values = self._process_registry(LAB_REGISTRY)
        ecmella = self._check_ecmella()

        payload = {
            "record_id": self.record_id,
            "redcap_event_name": self.redcap_event_name,
            "redcap_repeat_instrument": self.redcap_repeat_instrument,
            "redcap_repeat_instance": self.redcap_repeat_instance,
            "assess_time_point_labor": self.redcap_repeat_instance,
            "assess_date_labor": self.date,
            "date_assess_labor": self.date,
            "time_assess_labor": self.nearest_time,
            "art_site": WithdrawalSite.UNKNOWN,
            "na_post_2": 1,
            "ecmella_2": ecmella,
        }

        for field, value in values.items():
            if value is not None:
                payload[field] = value

        return LabModel.model_validate(payload)

    def create_lab_entry(self) -> LabModel:
        """Alias für create_entry (Rückwärtskompatibilität)."""
        return self.create_entry()
