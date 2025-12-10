"""
Impella Assessment Aggregator - Impella-Parameter zu REDCap-Model.

Aggregiert tägliche Impella-Daten:
- Flow (HZV in L/min)
- Purge-Flow (ml/h)
- Purge-Druck (mmHg)
- P-Level (aus Flußregelung extrahiert)

WICHTIG: Nur in impella_arm_2 verfügbar!
"""

import pandas as pd
from typing import Optional, Dict, Tuple
from datetime import date, time

from schemas.db_schemas.impella import ImpellaAssessmentModel
from .base import BaseAggregator


class ImpellaAggregator(BaseAggregator):
    """Aggregiert Impella-Daten zu einem ImpellaAssessmentModel."""

    INSTRUMENT_NAME = "impellaassessment_and_complications"
    MODEL_CLASS = ImpellaAssessmentModel

    # Mapping: Model-Feld -> (Source, Category-Pattern, Parameter-Pattern)
    # Impella-Parameter kommen aus source_type der "Impella" enthält
    FIELD_MAP: Dict[str, Tuple[str, str, str]] = {
        "imp_flow": ("Impella", ".*", r"^HZV"),  # HZV (l/min)
        "imp_purge_flow": ("Impella", ".*", r"Purgefluß|Purgefluss|Purge.*ml/h"),
        "imp_purge_pressure": ("Impella", ".*", r"Purgedruck"),
        # imp_level: Oft als "Flußregelung" gespeichert (z.B. "P8")
        # imp_rpm: Drehzahl (falls vorhanden)
    }

    def __init__(
        self,
        date: date,
        record_id: str,
        redcap_repeat_instance: int,
        value_strategy: str = "median",
        nearest_time: Optional[time] = None,
        data: Optional[pd.DataFrame] = None
    ):
        # ImpellaAssessment ist NUR in impella_arm_2 verfügbar!
        super().__init__(
            date=date,
            record_id=record_id,
            redcap_event_name="impella_arm_2",  # Immer impella_arm_2!
            redcap_repeat_instance=redcap_repeat_instance,
            value_strategy=value_strategy,
            nearest_time=nearest_time,
            data=data
        )

    def create_entry(self) -> ImpellaAssessmentModel:
        """Erstellt ein ImpellaAssessmentModel mit aggregierten Werten."""
        
        # Impella-Daten holen
        impella_df = self.get_source_data("impella")
        
        # Werte aggregieren
        values: Dict[str, Optional[float]] = {}
        
        for field, (source, category, parameter) in self.FIELD_MAP.items():
            values[field] = self.aggregate_value(impella_df, category, parameter)
        
        # P-Level extrahieren (nicht numerisch, daher speziell behandeln)
        p_level = self._get_p_level(impella_df)
        
        # Payload erstellen
        payload = {
            "record_id": self.record_id,
            "redcap_event_name": "impella_arm_2",  # Immer impella_arm_2!
            "redcap_repeat_instrument": "impellaassessment_and_complications",
            "redcap_repeat_instance": self.redcap_repeat_instance,
            "imp_compl_time_point": self.redcap_repeat_instance,
            "imp_compl_date": self.date,
        }
        
        # Werte hinzufügen (nur nicht-None)
        for field, value in values.items():
            if value is not None:
                payload[field] = value
        
        if p_level is not None:
            payload["imp_p_level"] = p_level
        
        return ImpellaAssessmentModel.model_validate(payload)

    def _get_p_level(self, df: pd.DataFrame) -> Optional[int]:
        """Extrahiert den P-Level aus Flußregelung.
        
        Werte wie "P8", "P9" werden zu 8, 9 konvertiert.
        """
        if df.empty:
            return None
        
        # Flußregelung finden
        mask = df["parameter"].str.contains(r"Flu.*regelung|Fluss.*regelung", case=False, na=False, regex=True)
        filtered = df[mask]
        
        if filtered.empty:
            return None
        
        # P-Level extrahieren (z.B. "P8" -> 8)
        import re
        for value in filtered["value"].dropna():
            match = re.search(r"P(\d+)", str(value), re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return None
