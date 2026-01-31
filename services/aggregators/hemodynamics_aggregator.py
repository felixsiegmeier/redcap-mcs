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
from unicodedata import category

import pandas as pd
from typing import Optional, Dict, Tuple
from datetime import date, time

from schemas.db_schemas.hemodynamics import (
    HemodynamicsModel,
    VentilationSpec,
    Anticoagulation,
)
from .base import BaseAggregator
from .mapping import (
    HEMODYNAMICS_FIELD_MAP, 
    HEMODYNAMICS_MEDICATION_MAP, 
    VASOACTIVE_SPEC_MAP,
    VENT_SPEC_MAP,
    ANTICOAGULANT_MAP,
    ANTIPLATELET_MAP,
    ANTIBIOTIC_MAP,
    TRANSFUSION_FIELD_MAP
)


class HemodynamicsAggregator(BaseAggregator):
    """Aggregiert Hämodynamik-Daten zu einem HemodynamicsModel."""

    INSTRUMENT_NAME = "hemodynamics_ventilation_medication"
    MODEL_CLASS = HemodynamicsModel

    # Zentrales Mapping: Beatmungsmodus-String -> VentilationSpec Enum-Name oder None (ignorieren)
    VENT_SPEC_MAP = VENT_SPEC_MAP

    # Mapping: Model-Feld -> (Source, Category-Pattern, Parameter-Pattern)
    FIELD_MAP = HEMODYNAMICS_FIELD_MAP
    
    # Medikamente: Spezielle Behandlung da sie anders strukturiert sind
    MEDICATION_MAP = HEMODYNAMICS_MEDICATION_MAP
    
    # Mapping: vasoactive_spec Checkbox-ID -> Medikamentenname Pattern (Regex)
    VASOACTIVE_SPEC_MAP = VASOACTIVE_SPEC_MAP

    # Mapping für Antikoagulation
    ANTICOAGULANT_MAP = ANTICOAGULANT_MAP

    # Mapping für Antithrombozytäre Therapie
    ANTIPLATELET_MAP = ANTIPLATELET_MAP

    # Mapping für Antibiotika / Antimykotika
    ANTIBIOTIC_MAP = ANTIBIOTIC_MAP

    # Mapping für Transfusion/ Blutprodukte
    TRANSFUSION_FIELD_MAP = TRANSFUSION_FIELD_MAP

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
                # vent_spec braucht String-Wert und Mapping zu Integer
                if field == "vent_spec":
                    vent_mode_str = self._get_string_value(resp_df, category, parameter)
                    if vent_mode_str:
                        values[field] = self._map_ventilation_spec(vent_mode_str)
                else:
                    values[field] = self.aggregate_value(resp_df, category, parameter)
            elif source == "Richmond":
                values[field] = self.aggregate_value(rass_df, category, parameter)
            elif source == "GCS":
                values[field] = self.aggregate_value(gcs_df, category, parameter)
        
        # Katecholamine/Medikamente aggregieren (mit Umrechnung zu µg/kg/min)
        for field, pattern in self.MEDICATION_MAP.items():
            values[field] = self._get_medication_rate(med_df, pattern, field)
        
        # Ernährung prüfen (enteral über Kategorie "Sonden")
        nutrition_spec___1 = 0
        if not med_df.empty and "category" in med_df.columns:
            has_enteral = med_df["category"].str.contains(
                r"\bSonden\b",
                case=False,
                na=False,
                regex=True,
            ).any()
            if has_enteral:
                nutrition_spec___1 = 1

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
            "nutrition_spec___1": nutrition_spec___1,
        }
        
        # Werte hinzufügen (nur nicht-None)
        rass_score = None  # Speichere RASS separat
        for field, value in values.items():
            if value is not None:
                # RASS wird separat behandelt (PrivateAttr)
                if field == "rass":
                    rass_score = int(value)
                else:
                    payload[field] = value
        
        # Model erstellen
        model = HemodynamicsModel.model_validate(payload)
        
        # RASS-Score setzen und zu Checkboxen konvertieren
        if rass_score is not None:
            model.set_rass_score(rass_score)
        
        # Vasoactive Spec Checkboxen setzen (prüft alle Medikamente am Tag)
        self._set_medication_checkboxes(
            model, 
            med_df, 
            self.VASOACTIVE_SPEC_MAP, 
            "vasoactive_spec", 
            exclude_fer=True
        )
        
        # Antikoagulation prüfen (Radio-Button / Int)
        if not med_df.empty:
            for key, pattern in self.ANTICOAGULANT_MAP.items():
                if med_df["parameter"].str.contains(pattern, case=False, na=False, regex=True).any():
                    model.iv_ac_spec = Anticoagulation(key)
        
        # Antiplatelet Therapie prüfen
        self._set_medication_checkboxes(
            model, 
            med_df, 
            self.ANTIPLATELET_MAP, 
            "antiplat_therapy_spec"
        )

        # Antibiotika prüfen
        self._set_medication_checkboxes(
            model, 
            med_df, 
            self.ANTIBIOTIC_MAP, 
            "antibiotic_spec"
        )

        # Transfusionen prüfen
        self._set_transfusion(
            model = model,
            med_df = med_df,
            mapping = self.TRANSFUSION_FIELD_MAP,
        )
        
        # Finale Validierung/Berechnung abgeleiteter Felder triggern
        model.set_derived_fields()
        
        return model

    def _set_medication_checkboxes(
        self,
        model: HemodynamicsModel,
        med_df: pd.DataFrame,
        mapping: Dict[int, str],
        field_prefix: str,
        exclude_fer: bool = True
    ) -> None:
        """Generische Methode zum Setzen von Medikamenten-Checkboxen.
        
        Args:
            model: Das zu befüllende HemodynamicsModel
            med_df: DataFrame mit Medikamentendaten
            mapping: Dictionary mit ID -> Regex-Pattern
            field_prefix: Präfix des REDCap-Feldes (z.B. 'vasoactive_spec')
            exclude_fer: Ob Fertigspritzen (Bolus) ignoriert werden sollen
        """
        if med_df.empty:
            return
            
        for drug_id, pattern in mapping.items():
            mask = med_df["parameter"].str.contains(pattern, case=False, na=False, regex=True)
            
            if exclude_fer:
                fer_mask = ~med_df["parameter"].str.contains(r"\(FER\)|Fertigspritze", case=False, na=False, regex=True)
                mask = mask & fer_mask
                
            has_medication = mask.any()
            setattr(model, f"{field_prefix}___{drug_id}", 1 if has_medication else 0)

        # Spezialfall vasoactive_med: Muss manuell gesetzt werden, da kein model_validator 
        # für die Checkboxen existiert (im Gegensatz zu Antibiotika/Antiplatelets)
        # Update: model.set_derived_fields() übernimmt das jetzt.
        pass
        
        # Abgeleitete Felder für Checkboxen manuell setzen
        # Update: model.set_derived_fields() übernimmt das jetzt.
        pass

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
        
        WARNUNG: Benötigt Patientengewicht aus der CSV. Wenn nicht vorhanden → None + Warnung
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
            # Gewicht fehlt → Warnung und None zurückgeben
            print(f"⚠️ WARNING: Patientengewicht nicht in Daten vorhanden. "
                  f"Medikamentendosierung '{field_name}' kann nicht berechnet werden (µg/kg/min benötigt Gewicht).")
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
        """Holt das Patientengewicht aus den Daten oder dem State.
        
        Priorität:
        1. Manuell eingegeben im State (patient_weight)
        2. Aus den Daten (PatientInfo)
        """
        # Erst im State prüfen (manuell eingegeben)
        try:
            from state import get_state
            state = get_state()
            if state.patient_weight is not None:
                return state.patient_weight
        except:
            pass
        
        # Dann in den Daten suchen
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

    def _get_string_value(
        self,
        df: pd.DataFrame,
        category_pattern: str,
        param_pattern: str
    ) -> Optional[str]:
        """Holt einen String-Wert aus dem DataFrame (für vent_spec, etc.).
        
        Args:
            df: Quelldaten (bereits auf Tag gefiltert)
            category_pattern: Regex-Pattern für Kategorie
            param_pattern: Regex-Pattern für Parameter
            
        Returns:
            Erster gefundener String-Wert oder None
        """
        if df.empty:
            return None
        
        # Parameter-Filter
        param_mask = df["parameter"].str.contains(param_pattern, case=False, na=False, regex=True)
        
        # Category-Filter nur wenn Spalte existiert und Pattern nicht ".*" ist
        if "category" in df.columns and category_pattern != ".*":
            cat_mask = df["category"].str.contains(category_pattern, case=False, na=False, regex=True)
            mask = param_mask & cat_mask
        else:
            mask = param_mask
        
        filtered = df[mask]
        
        if filtered.empty:
            return None
        
        # Ersten nicht-leeren String-Wert zurückgeben
        for val in filtered["value"].dropna():
            str_val = str(val).strip()
            if str_val:
                return str_val
        
        return None

    def _map_ventilation_spec(self, mode_str: str) -> Optional[int]:
        """Mappt Beatmungsmodus-String zu VentilationSpec Integer.
        
        Args:
            mode_str: String vom Beatmungsgerät (z.B. "CPAP", "BiLevel", "SIMV-PC")
        
        Returns:
            Integer-Wert für REDCap oder None bei unbekanntem Modus
        """
        # Normalisieren: uppercase, Bindestriche zu Unterstrichen
        normalized = mode_str.upper().replace("-", "_").replace(" ", "_").strip()
        
        # Prüfe ob Modus explizit auf None gemappt ist (z.B. STANDBY)
        if normalized in self.VENT_SPEC_MAP:
            enum_name = self.VENT_SPEC_MAP[normalized]
            if enum_name is None:
                return None  # Explizit ignorieren
            try:
                return VentilationSpec[enum_name].value
            except KeyError:
                pass
        
        # Versuche direkten Enum-Namen
        try:
            return VentilationSpec[normalized].value
        except KeyError:
            pass
        
        # Unbekannter Modus
        print(f"Warning: Unknown ventilation mode '{mode_str}' (normalized: '{normalized}')")
        return None

    def _check_ecmella(self) -> int:
        """Prüft ob sowohl ECMO als auch Impella am Tag aktiv sind."""
        ecmo_df = self.get_source_data("ecmo")
        impella_df = self.get_source_data("impella")
        
        has_ecmo = not ecmo_df.empty
        has_impella = not impella_df.empty
        
        return 1 if (has_ecmo and has_impella) else 0

    def _set_transfusion(
        self,
        model: HemodynamicsModel,
        med_df: pd.DataFrame,
        mapping: Dict[str, Tuple[str, str, str]]
    ) -> None:
        for key, value in mapping.items():
            if key in ("ppsb_t", "at3_t", "fxiii_t"):
                # Skip until reliable parsing is defined for these products.
                continue
            if med_df.empty:
                continue
            category_df = med_df[med_df["category"].str.contains(value[1], case=False, na=False, regex=True)]
            if category_df.empty:
                continue
            product_df = category_df[category_df["parameter"].str.contains(value[2], case=False, na=False, regex=True)]
            if product_df.empty:
                continue
            if key in  ["thromb_t","ery_t","ffp_t"]:
                setattr(model, key, len(product_df))
