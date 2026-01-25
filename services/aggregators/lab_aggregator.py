"""
Lab Aggregator - Laborwerte zu REDCap-Model.

Aggregiert tägliche Laborwerte (Blutgase, Blutbild, Gerinnung, etc.)
zu einem LabModel für den REDCap-Export.

Die FIELD_MAP definiert für jedes REDCap-Feld:
- Source-Type (z.B. "Lab" oder "ACT")
- Kategorie-Pattern (z.B. "Blutgase arteriell")
- Parameter-Pattern (z.B. "^PCO2" für pCO2-Werte)

Unterstützte Aggregations-Strategien: median, mean, nearest, first, last.
"""

import pandas as pd
from typing import Optional, Dict
from datetime import date, time

from schemas.db_schemas.lab import LabModel, WithdrawalSite
from .base import BaseAggregator
from .mapping import LAB_FIELD_MAP


class LabAggregator(BaseAggregator):
    """Aggregiert Laborwerte zu einem LabModel."""

    INSTRUMENT_NAME = "labor"
    MODEL_CLASS = LabModel
    FIELD_MAP = LAB_FIELD_MAP

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

        # Werte aggregieren, Daten pro Source nur einmal ziehen
        values: Dict[str, Optional[float]] = {}
        data_by_source: Dict[str, pd.DataFrame] = {}
        for field, (source, category, parameter) in self.FIELD_MAP.items():
            source_key = source.lower()
            if source_key not in data_by_source:
                data_by_source[source_key] = self.get_source_data(source)
            values[field] = self.aggregate_value(data_by_source[source_key], category, parameter)

        # ECMELLA prüfen (ECMO + Impella gleichzeitig)
        ecmella = self._check_ecmella()
        
        # Payload erstellen
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
        
        # Werte hinzufügen
        for field, value in values.items():
            if value is not None:
                payload[field] = value
        
        # Abgeleitete Felder werden automatisch vom Model-Validator gesetzt
        return LabModel.model_validate(payload)

    def create_lab_entry(self) -> LabModel:
        """Alias für create_entry (Rückwärtskompatibilität)."""
        return self.create_entry()

    def _check_ecmella(self) -> int:
        """Prüft ob sowohl ECMO als auch Impella am Tag aktiv sind."""
        ecmo_df = self.get_source_data("ecmo")
        impella_df = self.get_source_data("impella")
        
        return 1 if (not ecmo_df.empty and not impella_df.empty) else 0
