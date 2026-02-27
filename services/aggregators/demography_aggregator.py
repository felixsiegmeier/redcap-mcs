import pandas as pd
from typing import Optional, Dict, Tuple
from datetime import date

from .base import BaseAggregator
from schemas.db_schemas.demography import DemographyModel
from .mapping import DEMOGRAPHY_FIELD_MAP

class DemographyAggregator(BaseAggregator):
    """
    Aggregator für demographische Stammdaten.
    
    Diese Daten sind statisch und werden meist dem 'baseline_arm_2' Event
    und der Instanz 1 zugeordnet.
    """

    INSTRUMENT_NAME = "demography"
    MODEL_CLASS = DemographyModel
    FIELD_MAP = DEMOGRAPHY_FIELD_MAP

    def __init__(
        self,
        date: date,
        record_id: str,
        redcap_event_name: str = "baseline_arm_2",
        redcap_repeat_instance: int = 1,
        data: Optional[pd.DataFrame] = None,
        **kwargs
    ):
        # Wir rufen den super-init mit den Standard-REDCap Werten auf
        super().__init__(
            date=date,
            record_id=record_id,
            redcap_event_name=redcap_event_name,
            redcap_repeat_instance=redcap_repeat_instance,
            data=data,
            **kwargs
        )

    def create_entry(self) -> DemographyModel:
        """Erstellt das DemographyModel aus PatientInfo oder State."""
        
        # Für Demographie ignorieren wir die Tages-Filterung der Basisklasse,
        # da Stammdaten oft keinen oder nur einen Aufnahme-Zeitstempel haben.
        if self._data is not None:
            mask = self._data["source_type"].str.lower().str.contains("patientinfo", na=False)
            patientinfo_df = self._data[mask].copy()
        else:
            from state import get_data
            patientinfo_df = get_data("PatientInfo")

        values = {}

        # 1. Aus Rohdaten extrahieren
        for field, (source, category, parameter) in self.FIELD_MAP.items():
            if source == "PatientInfo":
                if field == "birthdate":
                    # Datum ist ein String
                    val_str = self.get_string_value(patientinfo_df, category, parameter)
                    if val_str:
                        values[field] = self._parse_date(val_str)
                else:
                    # Gewicht/Größe sind numerisch
                    val = self.aggregate_value(patientinfo_df, category, parameter)
                    if val is not None:
                        values[field] = val

        # 2. Gewicht-Spezialbehandlung (UI-Eingabe hat Vorrang)
        try:
            from state import get_state
            state = get_state()
            if state.patient_weight is not None:
                values["weight"] = state.patient_weight
            elif values.get("weight") is not None:
                # Wenn wir ein Gewicht gefunden haben, spiegeln wir es in den State
                # für andere Aggregatoren (z.B. Hämodynamik)
                state.patient_weight = values["weight"]
        except Exception:
            # Falls State nicht verfügbar (z.B. in Tests), ignorieren
            pass

        # 3. Payload für Pydantic vorbereiten
        payload = {
            "record_id": self.record_id,
            "redcap_event_name": self.redcap_event_name,
            "redcap_repeat_instrument": self.INSTRUMENT_NAME,
            "redcap_repeat_instance": self.redcap_repeat_instance,
        }

        # Gefundene Werte hinzufügen
        for field, value in values.items():
            if value is not None:
                payload[field] = value

        # Validierung und Instanziierung
        return DemographyModel.model_validate(payload)

    def _parse_date(self, date_str: str) -> Optional[date]:
        """Konvertiert Datums-String (DD.MM.YYYY oder YYYY-MM-DD) zu date Objekt."""
        if not date_str:
            return None
        
        import re
        from datetime import datetime
        
        # DD.MM.YYYY
        if re.match(r"^\d{1,2}\.\d{1,2}\.\d{4}$", date_str):
            try:
                return datetime.strptime(date_str, "%d.%m.%Y").date()
            except ValueError:
                pass
        
        # DD/MM/YYYY
        if re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", date_str):
            try:
                return datetime.strptime(date_str, "%d/%m/%Y").date()
            except ValueError:
                pass

        # YYYY-MM-DD (ISO)
        if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            try:
                return datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                pass
                
        return None