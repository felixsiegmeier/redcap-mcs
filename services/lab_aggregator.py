"""
Lab Aggregator - Laborwerte zu REDCap-Model.

Aggregiert tägliche Laborwerte (Blutgase, Blutbild, Gerinnung, etc.)
zu einem LabModel für den REDCap-Export.

Die _FIELD_MAP definiert für jedes REDCap-Feld:
- Kategorie-Pattern (z.B. "Blutgase arteriell")
- Parameter-Pattern (z.B. "^PCO2" für pCO2-Werte)

Unterstützte Aggregations-Strategien: median, mean, nearest, first, last.
"""

import pandas as pd
from typing import Optional, Dict, Tuple
from datetime import date, time

from state import get_data
from schemas.db_schemas.lab import LabModel, WithdrawalSite
from .aggregators.base import BaseAggregator
from .aggregators.mapping import LAB_FIELD_MAP


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
        """Erstellt ein LabModel mit aggregierten Werten.
        
        Alias für create_lab_entry für Kompatibilität mit BaseAggregator.
        """
        return self.create_lab_entry()

    def create_lab_entry(self) -> LabModel:
        """Erstellt ein LabModel mit aggregierten Werten."""
        
        # Alle Labor-Daten für den Tag holen
        lab_df = self.get_source_data("lab")
        
        # Werte aggregieren
        values: Dict[str, Optional[float]] = {}
        for field, (category, parameter) in self.FIELD_MAP.items():
            if category == "__ACT__":
                # ACT: Spezialfall - hat eigenen source_type
                values[field] = self._get_act_value()
            else:
                values[field] = self.aggregate_value(lab_df, category, parameter)
        
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

    def _get_act_value(self) -> Optional[float]:
        """Holt ACT-Wert aus dem separaten ACT source_type."""
        # ACT hat eigenen source_type
        act_df = self.get_source_data("ACT")
        
        if act_df.empty:
            return None
        
        # Numerische Werte
        values = pd.to_numeric(act_df["value"], errors="coerce").dropna()
        if values.empty:
            return None
        
        # Strategie anwenden (hier nutzen wir die Logik aus BaseAggregator)
        # Da act_df bereits auf Tag und Source gefiltert ist, können wir aggregate_value nutzen
        # Wir müssen nur sicherstellen dass das Pattern passt
        return self.aggregate_value(act_df, ".*", r"^ACT")

    def _check_ecmella(self) -> int:
        """Prüft ob sowohl ECMO als auch Impella am Tag aktiv sind."""
        ecmo_df = self.get_source_data("ecmo")
        impella_df = self.get_source_data("impella")
        
        return 1 if (not ecmo_df.empty and not impella_df.empty) else 0
