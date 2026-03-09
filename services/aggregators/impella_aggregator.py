"""
Impella Assessment Aggregator - Impella-Parameter zu REDCap-Model.
WICHTIG: Nur in impella_arm_2 verfügbar!
"""

import logging
import re

import pandas as pd
from typing import Optional, Dict
from datetime import date, time

from schemas.db_schemas.impella import ImpellaAssessmentModel
from .base import BaseAggregator
from .mapping import IMPELLA_REGISTRY

logger = logging.getLogger(__name__)


class ImpellaAggregator(BaseAggregator):
    """Aggregiert Impella-Daten zu einem ImpellaAssessmentModel."""

    INSTRUMENT_NAME = "impellaassessment_and_complications"
    MODEL_CLASS = ImpellaAssessmentModel

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
            redcap_event_name="impella_arm_2",
            redcap_repeat_instance=redcap_repeat_instance,
            value_strategy=value_strategy,
            nearest_time=nearest_time,
            data=data
        )

    def create_entry(self) -> ImpellaAssessmentModel:
        """Erstellt ein ImpellaAssessmentModel mit aggregierten Werten."""

        impella_df = self.get_source_data("impella")

        values: Dict[str, Optional[float]] = {}
        for redcap_key, spec in IMPELLA_REGISTRY.items():
            val = self.aggregate_value(impella_df, spec.category, spec.pattern)
            values[redcap_key] = val
            self.validate_range(redcap_key, val, spec.min_val, spec.max_val)

        p_level = self._get_p_level(impella_df)

        payload = {
            "record_id": self.record_id,
            "redcap_event_name": "impella_arm_2",
            "redcap_repeat_instrument": "impellaassessment_and_complications",
            "redcap_repeat_instance": self.redcap_repeat_instance,
            "imp_compl_time_point": self.redcap_repeat_instance,
            "imp_compl_date": self.date,
        }

        for field, value in values.items():
            if value is not None:
                payload[field] = value

        if p_level is not None:
            payload["imp_p_level"] = p_level

        return ImpellaAssessmentModel.model_validate(payload)

    def _get_p_level(self, df: pd.DataFrame) -> Optional[int]:
        """Extrahiert den P-Level aus Flußregelung (z.B. 'P8' → 8)."""
        if df.empty:
            return None
        mask = df["parameter"].str.contains(r"Flu.*regelung|Fluss.*regelung", case=False, na=False, regex=True)
        for value in df[mask]["value"].dropna():
            match = re.search(r"P(\d+)", str(value), re.IGNORECASE)
            if match:
                return int(match.group(1))
        return None
