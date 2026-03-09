"""
Pump (ECMO) Aggregator - ECMO-Parameter zu REDCap-Model.
WICHTIG: Nur in ecls_arm_2 verfügbar!
"""

import logging

import pandas as pd
from typing import Optional, Dict
from datetime import date, time

from schemas.db_schemas.pump import PumpModel
from .base import BaseAggregator
from .mapping import PUMP_REGISTRY

logger = logging.getLogger(__name__)


class PumpAggregator(BaseAggregator):
    """Aggregiert ECMO-Pumpen-Daten zu einem PumpModel."""

    INSTRUMENT_NAME = "pump"
    MODEL_CLASS = PumpModel

    def __init__(
        self,
        date: date,
        record_id: str,
        redcap_repeat_instance: int,
        value_strategy: str = "median",
        nearest_time: Optional[time] = None,
        data: Optional[pd.DataFrame] = None
    ):
        super().__init__(
            date=date,
            record_id=record_id,
            redcap_event_name="ecls_arm_2",
            redcap_repeat_instance=redcap_repeat_instance,
            value_strategy=value_strategy,
            nearest_time=nearest_time,
            data=data
        )

    def create_entry(self) -> PumpModel:
        """Erstellt ein PumpModel mit aggregierten Werten."""

        values: Dict[str, Optional[float]] = {}
        df_cache: Dict[str, pd.DataFrame] = {}

        for redcap_key, spec in PUMP_REGISTRY.items():
            df = df_cache.setdefault(spec.source, self.get_source_data(spec.source))
            val = self.aggregate_value(df, spec.category, spec.pattern)
            values[redcap_key] = val
            self.validate_range(redcap_key, val, spec.min_val, spec.max_val)

        payload = {
            "record_id": self.record_id,
            "redcap_event_name": "ecls_arm_2",
            "redcap_repeat_instrument": "pump",
            "redcap_repeat_instance": self.redcap_repeat_instance,
            "ecls_compl_time_point": self.redcap_repeat_instance,
            "ecls_compl_date": self.date,
            "ecls_compl_na": 1,
        }

        for field, value in values.items():
            if value is not None:
                payload[field] = value

        return PumpModel.model_validate(payload)
