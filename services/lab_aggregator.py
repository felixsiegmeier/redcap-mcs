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


class LabAggregator:
    """Aggregiert Laborwerte zu einem LabModel."""

    # Mapping: LabModel-Feld -> (Kategorie-Pattern, Parameter-Pattern)
    # Parameter-Pattern werden mit str.contains() gesucht (case-insensitive)
    # um Einheiten wie "[mmHg]" zu ignorieren
    _FIELD_MAP: Dict[str, Tuple[str, str]] = {
        # Blutgase arteriell
        # Wichtig: PCO2 (nicht CO2) um "HCO3" auszuschließen
        "pc02": ("Blutgase arteriell", r"^PCO2"),
        "p02": ("Blutgase arteriell", r"^PO2"),
        "ph": ("Blutgase arteriell", r"^PH$|^PH "),  # Exakt PH, nicht "PH AT PT. TEMP"
        "hco3": ("Blutgase arteriell", r"^HCO3"),
        "be": ("Blutgase arteriell", r"^ABEc"),
        "sa02": ("Blutgase arteriell", r"^O2-SAETTIGUNG"),
        "k": ("Blutgase arteriell", r"^KALIUM"),
        "na": ("Blutgase arteriell", r"^NATRIUM"),
        "gluc": ("Blutgase arteriell", r"^GLUCOSE"),
        "lactate": ("Blutgase arteriell", r"^LACTAT"),
        # Blutgase venös - für SvO2
        "sv02": ("Blutgase venös", r"^O2-SAETTIGUNG"),
        # Hämatologie / Blutbild
        "wbc": ("Blutbild", r"^WBC"),
        "hb": ("Blutbild", r"^HB \(HGB\)|^HB\b"),  # HB (HGB) oder exakt HB
        "hct": ("Blutbild", r"^HCT"),
        "plt": ("Blutbild", r"^PLT"),
        "fhb": ("Blutbild|Klinische Chemie", r"^FREIES HB"),
        # Gerinnung
        "ptt": ("Gerinnung", r"^PTT"),
        "quick": ("Gerinnung", r"^TPZ"),  # TPZ = Quick in %
        "inr": ("Gerinnung", r"^INR"),
        # ACT: Spezialfall - wird in separater Methode behandelt, da eigener source_type
        "act": ("__ACT__", r"^ACT"),  # Marker für Spezialbehandlung
        # Enzyme
        "ck": ("Enzyme", r"^CK \[|^CK$"),  # CK, aber nicht CK-MB
        "ckmb": ("Enzyme", r"^CK-MB"),
        "ggt": ("Enzyme", r"^GGT"),
        "ldh": ("Enzyme", r"^LDH"),
        "lipase": ("Enzyme", r"^LIPASE"),
        "got": ("Enzyme", r"^GOT"),
        "alat": ("Enzyme", r"^GPT"),  # GPT = ALAT
        # Klinische Chemie
        "pct": ("Klinische Chemie|Proteine", r"^PROCALCITONIN"),
        "crp": ("Klinische Chemie|Proteine", r"^CRP"),
        "bili": ("Klinische Chemie", r"^BILI"),
        "crea": ("Klinische Chemie|Retention", r"^KREATININ"),
        "urea": ("Klinische Chemie|Retention", r"^HARNSTOFF"),
        "cc": ("Klinische Chemie|Retention", r"^GFRKREA"),
        "albumin": ("Klinische Chemie|Proteine", r"^ALBUMIN"),
        "hapto": ("Klinische Chemie|Proteine", r"^HAPTOGLOBIN"),
    }

    def __init__(
        self,
        date: date,
        record_id: str,
        redcap_event_name: str,
        redcap_repeat_instrument: str,
        redcap_repeat_instance: int,
        value_strategy: str = "median",
        nearest_time: Optional[time] = None
    ):
        self.date = date
        self.record_id = record_id
        self.redcap_event_name = redcap_event_name
        self.redcap_repeat_instrument = redcap_repeat_instrument
        self.redcap_repeat_instance = redcap_repeat_instance
        self.value_strategy = value_strategy
        self.nearest_time = nearest_time

    def create_lab_entry(self) -> LabModel:
        """Erstellt ein LabModel mit aggregierten Werten."""
        
        # Alle Labor-Daten für den Tag holen
        lab_df = self._get_lab_data_for_day()
        
        # Werte aggregieren
        values: Dict[str, Optional[float]] = {}
        for field, (category, parameter) in self._FIELD_MAP.items():
            if category == "__ACT__":
                # ACT: Spezialfall - hat eigenen source_type
                values[field] = self._get_act_value()
            else:
                values[field] = self._get_value(lab_df, category, parameter)
        
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

    def _get_lab_data_for_day(self) -> pd.DataFrame:
        """Holt alle Labor-Daten für den angegebenen Tag."""
        df = get_data("lab")
        if df.empty:
            return pd.DataFrame()
        
        # Auf Tag filtern
        return df[df["timestamp"].dt.date == self.date].copy()

    def _get_value(
        self,
        df: pd.DataFrame,
        category: str,
        parameter: str
    ) -> Optional[float]:
        """Holt einen aggregierten Wert für einen Parameter.
        
        Args:
            df: DataFrame mit Labor-Daten
            category: Kategorie-Pattern (kann | für OR enthalten)
            parameter: Parameter-Pattern (Regex, case-insensitive)
        """
        
        if df.empty:
            return None
        
        # Filtern mit Regex für beide Felder
        mask = (
            df["category"].str.contains(category, case=False, na=False, regex=True) &
            df["parameter"].str.contains(parameter, case=False, na=False, regex=True)
        )
        filtered = df[mask]
        
        if filtered.empty:
            return None
        
        # Numerische Werte
        values = pd.to_numeric(filtered["value"], errors="coerce").dropna()
        if values.empty:
            return None
        
        # Strategie anwenden
        if self.value_strategy == "nearest" and self.nearest_time:
            return self._get_nearest_value(filtered, values)
        elif self.value_strategy == "median":
            return float(values.median())
        elif self.value_strategy == "mean":
            return float(values.mean())
        elif self.value_strategy == "first":
            return float(values.iloc[0])
        elif self.value_strategy == "last":
            return float(values.iloc[-1])
        
        # Default: median
        return float(values.median())

    def _get_nearest_value(
        self,
        df: pd.DataFrame,
        values: pd.Series
    ) -> Optional[float]:
        """Findet den Wert am nächsten zur Referenzzeit."""
        
        if self.nearest_time is None:
            return float(values.median())
        
        # Zeitdifferenz berechnen
        target_seconds = (
            self.nearest_time.hour * 3600 +
            self.nearest_time.minute * 60 +
            self.nearest_time.second
        )
        
        def time_diff(ts):
            if pd.isna(ts):
                return float('inf')
            s = ts.hour * 3600 + ts.minute * 60 + ts.second
            return abs(s - target_seconds)
        
        df = df.copy()
        df["_time_diff"] = df["timestamp"].dt.time.apply(time_diff)
        df["_value_numeric"] = pd.to_numeric(df["value"], errors="coerce")
        
        # Nächsten gültigen Wert finden
        valid = df.dropna(subset=["_value_numeric"])
        if valid.empty:
            return None
        
        nearest_idx = valid["_time_diff"].idxmin()
        return float(valid.loc[nearest_idx, "_value_numeric"])

    def _get_act_value(self) -> Optional[float]:
        """Holt ACT-Wert aus dem separaten ACT source_type."""
        from state import get_state
        
        state = get_state()
        if state.data is None:
            return None
        
        df = state.data
        
        # ACT hat eigenen source_type
        mask = (
            (df["source_type"] == "ACT") &
            (df["timestamp"].dt.date == self.date)
        )
        filtered = df[mask]
        
        if filtered.empty:
            return None
        
        # Numerische Werte (ACT-Wert aus "value" oder "parameter" extrahieren)
        values = pd.to_numeric(filtered["value"], errors="coerce").dropna()
        if values.empty:
            return None
        
        # Strategie anwenden
        if self.value_strategy == "median":
            return float(values.median())
        elif self.value_strategy == "mean":
            return float(values.mean())
        elif self.value_strategy == "first":
            return float(values.iloc[0])
        elif self.value_strategy == "last":
            return float(values.iloc[-1])
        
        return float(values.median())

    def _check_ecmella(self) -> int:
        """Prüft ob sowohl ECMO als auch Impella am Tag aktiv sind."""
        ecmo_df = get_data("ecmo")
        impella_df = get_data("impella")
        
        has_ecmo = not ecmo_df.empty and not ecmo_df[
            ecmo_df["timestamp"].dt.date == self.date
        ].empty
        
        has_impella = not impella_df.empty and not impella_df[
            impella_df["timestamp"].dt.date == self.date
        ].empty
        
        return 1 if (has_ecmo and has_impella) else 0
