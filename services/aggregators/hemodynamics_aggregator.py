"""
Hemodynamics Aggregator - Vitalwerte und Medikation zu REDCap-Model.

Aggregiert täglich:
- Vitalzeichen (HR, BP, CVP, SpO2, NIRS)
- Beatmungsparameter (FiO2, PEEP, PIP)
- Katecholamine (Noradrenalin, Adrenalin, Dobutamin, etc.)

WICHTIG: Katecholamine werden von ml/h zu µg/kg/min umgerechnet!
- Gewicht wird aus PatientInfo extrahiert
- Konzentration wird aus dem Perfusor-Namen geparst
"""

import re
import pandas as pd
from typing import Optional, Dict, Tuple
from datetime import date, time

from schemas.db_schemas.hemodynamics import HemodynamicsModel
from .base import BaseAggregator


class HemodynamicsAggregator(BaseAggregator):
    """Aggregiert Hämodynamik-Daten zu einem HemodynamicsModel."""

    INSTRUMENT_NAME = "hemodynamics_ventilation_medication"
    MODEL_CLASS = HemodynamicsModel

    # Mapping: Model-Feld -> (Source, Category-Pattern, Parameter-Pattern)
    # Vitals-Parameter kommen aus "Vitals" source_type
    # Respiratory-Parameter kommen aus "Respiratory" source_type
    FIELD_MAP: Dict[str, Tuple[str, str, str]] = {
        # ==================== Vitals ====================
        "hr": ("Vitals", ".*", r"^HF\s*\["),
        "sys_bp": ("Vitals", ".*", r"^ABPs\s*\[|^ARTs\s*\["),
        "dia_bp": ("Vitals", ".*", r"^ABPd\s*\[|^ARTd\s*\["),
        "mean_bp": ("Vitals", ".*", r"^ABPm\s*\[|^ARTm\s*\["),
        "cvp": ("Vitals", ".*", r"^ZVDm\s*\["),
        "ci": ("Vitals", ".*", r"^HZV"),  # HZV (l/min) - CI wenn normiert
        # NIRS
        "nirs_left_c": ("Vitals", ".*", r"NIRS Channel 1 RSO2|NIRS.*Channel.*1"),
        "nirs_right_c": ("Vitals", ".*", r"NIRS Channel 2 RSO2|NIRS.*Channel.*2"),
        
        # ==================== Respiratory ====================
        "fi02": ("Respiratory", ".*", r"^FiO2\s*\[%\]"),
        "vent_peep": ("Respiratory", ".*", r"^PEEP\s*\["),
        "vent_pip": ("Respiratory", ".*", r"^Ppeak\s*\[|^insp.*Spitzendruck"),
        "conv_vent_rate": ("Respiratory", ".*", r"mand.*Atemfrequenz|^mand\. Atemfrequenz"),
        "sp02": ("Respiratory", ".*", r"^SpO2"),  # Falls vorhanden
        
        # ==================== Neurologie ====================
        "rass": ("Richmond", ".*", r"^Summe Richmond-Agitation-Sedation"),
        "gcs": ("GCS", ".*", r"^Summe GCS2"),
    }
    
    # Medikamente: Spezielle Behandlung da sie anders strukturiert sind
    # (aus Medication source_type, Parameter enthält Medikamentennamen)
    # WICHTIG: Regex so gestalten dass Epinephrin nicht Norepinephrin matcht!
    MEDICATION_MAP: Dict[str, str] = {
        "norepinephrine": r"(?<!o)Norepinephrin|^Arterenol",  # Norepinephrin aber nicht "Epinephrin" allein
        "epinephrine": r"(?<!Nor)Epinephrin|^Suprarenin",     # Epinephrin aber nicht in "Norepinephrin"
        "dobutamine": r"Dobutamin",
        "milrinone": r"Milrinone|Corotrop",
        "vasopressin": r"Vasopressin|Empressin",
    }

    def __init__(
        self,
        date: date,
        record_id: str,
        redcap_event_name: str,
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

    def create_entry(self) -> HemodynamicsModel:
        """Erstellt ein HemodynamicsModel mit aggregierten Werten."""
        
        # Daten holen
        vitals_df = self.get_source_data("vitals")
        resp_df = self.get_source_data("respiratory")
        med_df = self.get_source_data("medication")
        rass_df = self.get_source_data("Richmond-Agitation-Sedation")
        gcs_df = self.get_source_data("GCS (Jugendliche und Erwachsene)")
        
        # Werte aggregieren
        values: Dict[str, Optional[float]] = {}
        
        for field, (source, category, parameter) in self.FIELD_MAP.items():
            if source == "Vitals":
                values[field] = self.aggregate_value(vitals_df, category, parameter)
            elif source == "Respiratory":
                values[field] = self.aggregate_value(resp_df, category, parameter)
            elif source == "Richmond":
                values[field] = self.aggregate_value(rass_df, category, parameter)
            elif source == "GCS":
                values[field] = self.aggregate_value(gcs_df, category, parameter)
        
        # Medikamente aggregieren (mit Umrechnung zu µg/kg/min)
        for field, pattern in self.MEDICATION_MAP.items():
            values[field] = self._get_medication_rate(med_df, pattern, field)
        
        # ECMELLA prüfen
        ecmella = self._check_ecmella()
        
        # Payload erstellen
        payload = {
            "record_id": self.record_id,
            "redcap_event_name": self.redcap_event_name,
            "redcap_repeat_instrument": "hemodynamics_ventilation_medication",
            "redcap_repeat_instance": self.redcap_repeat_instance,
            "assess_time_point": self.redcap_repeat_instance,
            "assess_date_hemo": self.date,
            "na_post": 1,
            "ecmella": ecmella,
        }
        
        # Werte hinzufügen (nur nicht-None)
        for field, value in values.items():
            if value is not None:
                payload[field] = value
        
        # Abgeleitete Felder werden automatisch vom Model-Validator gesetzt
        return HemodynamicsModel.model_validate(payload)

    def _get_medication_rate(
        self,
        df: pd.DataFrame,
        pattern: str,
        field_name: str = ""
    ) -> Optional[float]:
        """Holt die Laufrate eines Medikaments und rechnet zu µg/kg/min um.
        
        Für Katecholamine:
        - Extrahiert Rate in ml/h
        - Parst Konzentration aus Perfusor-Namen (z.B. "5 mg / 50 ml")
        - Holt Gewicht aus PatientInfo
        - Rechnet um: µg/kg/min = (ml/h × µg/ml) / (60 × kg)
        
        Für Vasopressin:
        - REDCap erwartet IU/h
        - Perfusor ist 40 IE / 40 ml = 1 IE/ml
        - Also: IU/h = ml/h × 1 = ml/h (direkt übernehmen)
        
        IGNORIERT: Fertigspritzen "(FER)" - das sind Bolusgaben, keine kontinuierlichen Infusionen!
        """
        if df.empty:
            return None
        
        # Filtern nach Medikamentenname im Parameter
        mask = df["parameter"].str.contains(pattern, case=False, na=False, regex=True)
        filtered = df[mask]
        
        if filtered.empty:
            return None
        
        # Fertigspritzen für Bolusgaben ausschließen!
        if "parameter" in filtered.columns:
            fer_mask = ~filtered["parameter"].str.contains(r"\(FER\)|Fertigspritze", case=False, na=False, regex=True)
            filtered = filtered[fer_mask]
            
            if filtered.empty:
                return None
        
        # Rate in ml/h holen
        if "rate" in filtered.columns:
            rates = pd.to_numeric(filtered["rate"], errors="coerce").dropna()
            if rates.empty:
                return None
            rate_ml_h = float(rates.median())
        else:
            values = pd.to_numeric(filtered["value"], errors="coerce").dropna()
            if values.empty:
                return None
            rate_ml_h = float(values.median())
        
        # Vasopressin: REDCap erwartet IU/h, Perfusor ist 1 IE/ml
        if field_name == "vasopressin":
            # 40 IE / 40 ml = 1 IE/ml, also ml/h = IE/h
            return round(rate_ml_h, 2)
        
        # Für Katecholamine: Umrechnung zu µg/kg/min
        # Konzentration aus Perfusor-Namen extrahieren
        conc_ug_ml = self._extract_concentration(filtered, field_name)
        if conc_ug_ml is None:
            return None
        
        # Gewicht holen
        weight_kg = self._get_patient_weight()
        if weight_kg is None:
            return None
        
        # Umrechnung: µg/kg/min = (ml/h × µg/ml) / (60 × kg)
        ug_kg_min = (rate_ml_h * conc_ug_ml) / (60 * weight_kg)
        
        return round(ug_kg_min, 4)
    
    def _extract_concentration(self, df: pd.DataFrame, field_name: str) -> Optional[float]:
        """Extrahiert die Konzentration in µg/ml aus dem Perfusor-Namen.
        
        Unterstützte Formate:
        - "Norepinephrin Perfusor 5 mg / 50 ml" -> 100 µg/ml
        - "Norepinephrin Perfusor 10 mg / 50 ml" -> 200 µg/ml
        - "Dobutamin-hameln 5mg/ml 250mg" -> verdünnt auf 250mg/50ml = 5000 µg/ml
        
        IGNORIERT:
        - "1:100 (FER)" -> Fertigspritze für Bolusgaben, keine kontinuierliche Infusion!
        """
        # Standard-Konzentrationen als Fallback
        default_concentrations = {
            "norepinephrine": 100.0,   # 5 mg / 50 ml = 100 µg/ml
            "epinephrine": 200.0,      # 10 mg / 50 ml = 200 µg/ml
            "dobutamine": 5000.0,      # 250 mg / 50 ml = 5000 µg/ml
            "milrinone": 200.0,        # 10 mg / 50 ml = 200 µg/ml (typisch)
        }
        
        # Versuche Konzentration aus Parameter zu parsen
        for param in df["parameter"].dropna():
            # Fertigspritzen für Bolusgaben überspringen!
            if "(FER)" in param or "Fertigspritze" in param.lower():
                continue
            
            # Pattern 1: "X mg / Y ml" (Standard-Perfusor)
            match = re.search(r"(\d+(?:[,\.]\d+)?)\s*mg\s*/\s*(\d+)\s*ml", param, re.IGNORECASE)
            if match:
                mg = float(match.group(1).replace(",", "."))
                ml = float(match.group(2))
                return (mg * 1000) / ml  # Umrechnung mg -> µg
            
            # Pattern 2: "Xmg/ml" direkte Angabe
            match = re.search(r"(\d+(?:[,\.]\d+)?)\s*mg/ml", param, re.IGNORECASE)
            if match:
                mg_per_ml = float(match.group(1).replace(",", "."))
                # Dobutamin kommt als Fertiglösung, wird auf 250mg/50ml verdünnt
                if field_name == "dobutamine":
                    return 5000.0  # 250 mg / 50 ml = 5000 µg/ml (Standard)
                return mg_per_ml * 1000  # Umrechnung mg -> µg
        
        # Fallback auf Standard-Konzentrationen
        return default_concentrations.get(field_name)
    
    def _get_patient_weight(self) -> Optional[float]:
        """Holt das Patientengewicht aus den Daten."""
        if self._data is None or self._data.empty:
            from state import get_data
            full_df = get_data()
        else:
            full_df = self._data
        
        if full_df.empty:
            return None
        
        # Gewicht aus PatientInfo oder Grösse/Gewicht
        weight_mask = (
            (full_df["source_type"].str.contains("PatientInfo|Grösse/Gewicht", case=False, na=False)) &
            (full_df["parameter"].str.contains(r"^Gewicht(?:\s*/\s*kg)?$", case=False, na=False, regex=True))
        )
        weight_df = full_df[weight_mask]
        
        if weight_df.empty:
            return None
        
        # Ersten numerischen Wert nehmen
        for val in weight_df["value"]:
            try:
                weight = float(str(val).replace(",", "."))
                if 20 < weight < 300:  # Plausibilitätsprüfung
                    return weight
            except (ValueError, TypeError):
                continue
        
        return None

    def _check_ecmella(self) -> int:
        """Prüft ob sowohl ECMO als auch Impella am Tag aktiv sind."""
        ecmo_df = self.get_source_data("ecmo")
        impella_df = self.get_source_data("impella")
        
        has_ecmo = not ecmo_df.empty
        has_impella = not impella_df.empty
        
        return 1 if (has_ecmo and has_impella) else 0
