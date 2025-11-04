import pandas as pd
from typing import Optional, Dict, Tuple
from datetime import datetime, date, time

from schemas.db_schemas.lab import LabModel, WithdrawalSite
from state_provider.state_provider_class import StateProvider, state_provider

class LabAggregator:
    """Aggregiert Laborwerte zu einem LabModel mittels StateProvider.query_data.

    Hinweise zur Wertestrategie (value_strategy):
    - "median", "mean", "first", "last", "nearest" werden direkt als value_strategy an query_data übergeben.
    - Bei "nearest" wird nearest_time verwendet, um den Wert am nächsten an dieser Zeit zu finden.
    """

    def __init__(
        self, state_provider: StateProvider, 
        date: date, 
        record_id: str, 
        redcap_event_name: str,
        redcap_repeat_instrument: str, 
        redcap_repeat_instance: int,
        value_strategy: Optional[str] = None, 
        nearest_time: Optional[time] = None
        ) -> None:
        self.state_provider = state_provider
        self.date = date
        self.record_id = record_id
        self.redcap_event_name = redcap_event_name
        self.redcap_repeat_instrument = redcap_repeat_instrument
        self.redcap_repeat_instance = redcap_repeat_instance
        self.assess_time_point_labor = redcap_repeat_instance
        self.value_strategy = value_strategy or "median"
        self.nearest_time = nearest_time

    # Mapping: LabModel-Feld -> (Kategorie, Parameter)
    _FIELD_MAP: Dict[str, Tuple[str, str]] = {
        # Blutgase arteriell
        "pc02": ("Blutgase arteriell", "PCO2"),
        "p02": ("Blutgase arteriell", "PO2"),
        "ph": ("Blutgase arteriell", "PH"),
        "hco3": ("Blutgase arteriell", "HCO3"),
        "be": ("Blutgase arteriell", "ABEc"),
        "sa02": ("Blutgase arteriell", "O2-SAETTIGUNG"),
        "k": ("Blutgase arteriell", "KALIUM"),
        "na": ("Blutgase arteriell", "NATRIUM"),
        "gluc": ("Blutgase arteriell", "GLUCOSE"),
        "lactate": ("Blutgase arteriell", "LACTAT"),
        # Blutgase venös
        "sv02": ("Blutgase venös", "O2-SAETTIGUNG"),
        # Hämatologie & Gerinnung
        "wbc": ("Blutbild", "WBC"),
        "hb": ("Blutbild", "HB"),
        "hct": ("Blutbild", "HCT"),
        "plt": ("Blutbild", "PLT"),
        "ptt": ("Gerinnung", "PTT"),
        "quick": ("Gerinnung", "TPZ"),
        "inr": ("Gerinnung", "INR"),
        # Organsystem-Labore / Enzyme etc.
        "ck": ("Enzyme", "CK"),
        "ckmb": ("Enzyme", "CK-MB"),
        "ggt": ("Enzyme", "GGT"),
        "ldh": ("Enzyme", "LDH"),
        "lipase": ("Enzyme", "LIPASE"),
        "fhb": ("Blutbild", "FREIES HB"),
        "pct": ("Klinische Chemie", "PROCALCITONIN"),
        "bili": ("Klinische Chemie", "BILI"),
        "crea": ("Klinische Chemie", "KREATININ"),
        "urea": ("Klinische Chemie", "HARNSTOFF"),
        "cc": ("Klinische Chemie", "GFRKREA"),
    }

    def _get_lab_value(self, category: str, parameter: str) -> Optional[float]:
        filters: Dict = {
            "timestamp": self.date,
            "category": category,
            "parameter": parameter,
            "value_strategy": self.value_strategy,
        }
        if self.value_strategy == "nearest" and self.nearest_time:
            filters["nearest_time"] = self.nearest_time

        df = self.state_provider.query_data("lab", filters)
        if df is None or df.empty or "value" not in df.columns:
            return None

        # value in float wandeln
        try:
            val = pd.to_numeric(df["value"].iloc[0], errors="coerce")
        except Exception:
            return None
        return None if pd.isna(val) else float(val)

    def create_lab_entry(self) -> LabModel:

        values: Dict[str, Optional[float]] = {}
        for field, (category, parameter) in self._FIELD_MAP.items():
            values[field] = self._get_lab_value(category, parameter)

        # Nutzlast zusammenbauen und per model_validate validieren
        impella_df = self.state_provider.query_data("impella", {"timestamp": self.date})
        ecmo_df = self.state_provider.query_data("ecmo", {"timestamp": self.date})

        def _has_value(df: Optional[pd.DataFrame]) -> bool:
            return (
            df is not None
            and not df.empty
            )

        payload: Dict[str, object] = {
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
            "ecmella_2": 1 if (_has_value(impella_df) and _has_value(ecmo_df)) else 0,
        }

        for field, value in values.items():
            if value is not None:
                payload[field] = value

        # Berechne post_* und hemolysis basierend auf vorhandenen Werten
        payload["post_pct"] = 1 if values.get("pct") is not None else 0
        payload["post_crp"] = 1 if values.get("crp") is not None else 0
        payload["post_act"] = 1 if values.get("act") is not None else 0
        payload["hemolysis"] = 1 if (values.get("fhb") is not None or values.get("haptoglobin") is not None or values.get("bili") is not None) else 0

        return LabModel.model_validate(payload)


def create_lab_entry(record_date: date, redcap_event_name: str, redcap_repeat_instrument: str, redcap_repeat_instance: int, value_strategy: str = "median", nearest_time: Optional[time] = None) -> LabModel:
    """Kompatibilitäts-Wrapper für Views: erstellt ein LabModel für das gegebene Datum.

    - Ermittelt record_id aus dem globalen State (selected_patient_id), fällt andernfalls auf "unknown" zurück.
    - Verwendet StateProvider.query_data mit value_strategy und optional nearest_time.
    - Unterstützt nearest_time, wenn value_strategy "nearest" ist.
    """
    state = state_provider.get_state()
    record_id = getattr(state, "selected_patient_id", None) or "unknown"
    aggregator = LabAggregator(state_provider, record_date, record_id, redcap_event_name=redcap_event_name, redcap_repeat_instrument=redcap_repeat_instrument, redcap_repeat_instance=redcap_repeat_instance, value_strategy=value_strategy, nearest_time=nearest_time)
    return aggregator.create_lab_entry()