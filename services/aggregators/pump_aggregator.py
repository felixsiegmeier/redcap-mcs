"""
Pump (ECMO) Aggregator - ECMO-Parameter zu REDCap-Model.

Aggregiert tägliche ECMO-Pumpendaten:
- Drehzahl (RPM)
- Blutfluss (L/min)
- Gasfluss (L/min)
- FiO2 (%)

WICHTIG: Nur in ecls_arm_2 verfügbar!
"""

import pandas as pd
from typing import Optional, Dict, Tuple
from datetime import date, time

from schemas.db_schemas.pump import PumpModel
from .base import BaseAggregator


class PumpAggregator(BaseAggregator):
    """Aggregiert ECMO-Pumpen-Daten zu einem PumpModel."""

    INSTRUMENT_NAME = "pump"
    MODEL_CLASS = PumpModel

    # Mapping: Model-Feld -> (Source, Category-Pattern, Parameter-Pattern)
    # ECMO-Parameter kommen aus source_type mit "ECMO" im Namen
    FIELD_MAP: Dict[str, Tuple[str, str, str]] = {
        "ecls_rpm": ("ECMO", ".*", r"^Drehzahl"),
        "ecls_pf": ("ECMO", ".*", r"^Blutfluss arteriell|^Blutfluss.*l/min"),
        "ecls_gf": ("ECMO", ".*", r"^Gasfluss"),
        "ecls_fi02": ("ECMO", ".*", r"^FiO2"),
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
        # Pump ist NUR in ecls_arm_2 verfügbar!
        super().__init__(
            date=date,
            record_id=record_id,
            redcap_event_name="ecls_arm_2",  # Immer ecls_arm_2!
            redcap_repeat_instance=redcap_repeat_instance,
            value_strategy=value_strategy,
            nearest_time=nearest_time,
            data=data
        )

    def create_entry(self) -> PumpModel:
        """Erstellt ein PumpModel mit aggregierten Werten."""
        
        # ECMO-Daten holen (source_type enthält "ECMO")
        ecmo_df = self.get_source_data("ecmo")
        
        # Werte aggregieren
        values: Dict[str, Optional[float]] = {}
        
        for field, (source, category, parameter) in self.FIELD_MAP.items():
            values[field] = self.aggregate_value(ecmo_df, category, parameter)
        
        # Payload erstellen
        payload = {
            "record_id": self.record_id,
            "redcap_event_name": "ecls_arm_2",  # Immer ecls_arm_2!
            "redcap_repeat_instrument": "pump",
            "redcap_repeat_instance": self.redcap_repeat_instance,
            "ecls_compl_time_point": self.redcap_repeat_instance,
            "ecls_compl_date": self.date,
            "ecls_compl_na": 1,  # Default: keine Komplikationen
        }
        
        # Werte hinzufügen (nur nicht-None)
        for field, value in values.items():
            if value is not None:
                payload[field] = value
        
        return PumpModel.model_validate(payload)
