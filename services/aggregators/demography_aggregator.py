import logging
import re

import pandas as pd
from typing import Optional
from datetime import date

from .base import BaseAggregator
from schemas.db_schemas.demography import DemographyModel
from .mapping import DEMOGRAPHY_REGISTRY

logger = logging.getLogger(__name__)


class DemographyAggregator(BaseAggregator):
    """Aggregator für demographische Stammdaten (baseline_arm_2)."""

    INSTRUMENT_NAME = "demography"
    MODEL_CLASS = DemographyModel

    def __init__(
        self,
        date: date,
        record_id: str,
        redcap_event_name: str = "baseline_arm_2",
        data: Optional[pd.DataFrame] = None,
        **kwargs
    ):
        super().__init__(
            date=date,
            record_id=record_id,
            redcap_event_name=redcap_event_name,
            redcap_repeat_instance=None,
            data=data,
            **kwargs
        )

    def create_entry(self) -> DemographyModel:
        """Erstellt das DemographyModel aus PatientInfo oder State."""

        # PatientInfo direkt holen (ohne Tages-Filter, da Stammdaten)
        if self._data is not None:
            mask = self._data["source_type"].str.lower().str.contains("patientinfo", na=False)
            patientinfo_df = self._data[mask].copy()
        else:
            from state import get_data
            patientinfo_df = get_data("PatientInfo")

        values = {}

        for redcap_key, spec in DEMOGRAPHY_REGISTRY.items():
            if redcap_key == "birthdate":
                val_str = self.get_string_value(patientinfo_df, spec.category, spec.pattern)
                if val_str:
                    values[redcap_key] = self._parse_date(val_str)
            else:
                val = self.aggregate_value(patientinfo_df, spec.category, spec.pattern)
                if val is not None:
                    values[redcap_key] = val

        # Gewicht: UI-Eingabe hat Vorrang, gefundener Wert wird in State gespiegelt
        try:
            from state import get_state
            state = get_state()
            if state.patient_weight is not None:
                values["weight"] = state.patient_weight
            elif values.get("weight") is not None:
                state.patient_weight = values["weight"]
        except Exception:
            pass

        payload = {
            "record_id": self.record_id,
            "redcap_event_name": self.redcap_event_name,
            **{k: v for k, v in values.items() if v is not None},
        }

        return DemographyModel.model_validate(payload)

    def _parse_date(self, date_str: str) -> Optional[date]:
        """Konvertiert Datums-String (DD.MM.YYYY oder YYYY-MM-DD) zu date."""
        if not date_str:
            return None
        from datetime import datetime
        for fmt, pat in [
            ("%d.%m.%Y", r"^\d{1,2}\.\d{1,2}\.\d{4}$"),
            ("%d/%m/%Y", r"^\d{1,2}/\d{1,2}/\d{4}$"),
            ("%Y-%m-%d", r"^\d{4}-\d{2}-\d{2}$"),
        ]:
            if re.match(pat, date_str):
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    pass
        return None
