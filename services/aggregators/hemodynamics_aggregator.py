"""
Hemodynamics Aggregator - Vitalwerte, Beatmung und Medikation zu REDCap-Model.

WICHTIG: Katecholamine werden von ml/h zu µg/kg/min umgerechnet (benötigt Gewicht).
"""

import logging
import re

import pandas as pd
from typing import Optional, Dict, Tuple
from datetime import date, time

logger = logging.getLogger(__name__)

from schemas.db_schemas.hemodynamics import (
    HemodynamicsModel,
    VentilationSpec,
    Anticoagulation,
)
from .base import BaseAggregator
from .mapping import (
    HEMODYNAMICS_REGISTRY,
    HEMODYNAMICS_MEDICATION_MAP,
    TRANSFUSION_REGISTRY,
    VASOACTIVE_SPEC_MAP,
    VENT_SPEC_MAP,
    ANTICOAGULANT_MAP,
    ANTIPLATELET_MAP,
    ANTIBIOTIC_MAP,
    MEDICATION_SPEC_MAP,
    NARCOTICS_SPEC_MAP,
)


class HemodynamicsAggregator(BaseAggregator):
    """Aggregiert Hämodynamik-Daten zu einem HemodynamicsModel."""

    INSTRUMENT_NAME = "hemodynamics_ventilation_medication"
    MODEL_CLASS = HemodynamicsModel

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

        med_df = self.get_source_data("medication")

        # Registry-Felder aggregieren (Source-DFs werden gecacht)
        values: Dict[str, Optional[float]] = {}
        df_cache: Dict[str, pd.DataFrame] = {}

        for redcap_key, spec in HEMODYNAMICS_REGISTRY.items():
            df = df_cache.setdefault(spec.source, self.get_source_data(spec.source))

            if redcap_key == "vent_spec":
                # String-Wert → Integer via VENT_SPEC_MAP
                mode_str = self.get_string_value(df, spec.category, spec.pattern)
                if mode_str:
                    values["vent_spec"] = self._map_ventilation_spec(mode_str)
            else:
                values[redcap_key] = self.aggregate_value(df, spec.category, spec.pattern)

        # Katecholamine (separate Raten-Berechnung)
        for field, pattern in HEMODYNAMICS_MEDICATION_MAP.items():
            values[field] = self._get_medication_rate(med_df, pattern, field)

        # Enterale Ernährung prüfen
        nutrition_spec___1 = 0
        if not med_df.empty and "category" in med_df.columns:
            if med_df["category"].str.contains(r"\bSonden\b", case=False, na=False, regex=True).any():
                nutrition_spec___1 = 1

        ecmella = self._check_ecmella()

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

        rass_score = None
        for field, value in values.items():
            if value is not None:
                if field == "rass":
                    rass_score = int(value)
                else:
                    payload[field] = value

        model = HemodynamicsModel.model_validate(payload)

        if rass_score is not None:
            model.set_rass_score(rass_score)

        self._set_medication_checkboxes(model, med_df, VASOACTIVE_SPEC_MAP, "vasoactive_spec", exclude_fer=True)

        if not med_df.empty:
            for key, pattern in ANTICOAGULANT_MAP.items():
                if med_df["parameter"].str.contains(pattern, case=False, na=False, regex=True).any():
                    model.iv_ac_spec = Anticoagulation(key)

        self._set_medication_checkboxes(model, med_df, ANTIPLATELET_MAP,   "post_antiplat_spec")
        self._set_medication_checkboxes(model, med_df, ANTIBIOTIC_MAP,     "antibiotic_spec")
        self._set_medication_checkboxes(model, med_df, MEDICATION_SPEC_MAP, "medication", exclude_fer=True)

        meds_flags = [getattr(model, f"medication___{i}") for i in [1, 2, 3, 4, 5, 6, 7, 8, 10, 11]]
        model.medication___9 = 0 if any(v for v in meds_flags) else 1

        self._set_medication_checkboxes(model, med_df, NARCOTICS_SPEC_MAP, "narcotics_spec", exclude_fer=True)
        self._set_transfusion(model, med_df)

        model.set_derived_fields()

        return model

    # ------------------------------------------------------------------
    # Hilfsmethoden
    # ------------------------------------------------------------------

    def _set_medication_checkboxes(
        self,
        model: HemodynamicsModel,
        med_df: pd.DataFrame,
        mapping: Dict[int, str],
        field_prefix: str,
        exclude_fer: bool = True
    ) -> None:
        if med_df.empty:
            return
        for drug_id, pattern in mapping.items():
            mask = med_df["parameter"].str.contains(pattern, case=False, na=False, regex=True)
            if exclude_fer:
                mask &= ~med_df["parameter"].str.contains(
                    r"\(FER\)|Fertigspritze", case=False, na=False, regex=True
                )
            setattr(model, f"{field_prefix}___{drug_id}", 1 if mask.any() else 0)

    def _set_transfusion(self, model: HemodynamicsModel, med_df: pd.DataFrame) -> None:
        for redcap_key, spec in TRANSFUSION_REGISTRY.items():
            if redcap_key in ("ppsb_t", "at3_t", "fxiii_t"):
                continue
            if med_df.empty:
                continue
            cat_df = med_df[med_df["category"].str.contains(spec.category, case=False, na=False, regex=True)]
            if cat_df.empty:
                continue
            prod_df = cat_df[cat_df["parameter"].str.contains(spec.pattern, case=False, na=False, regex=True)]
            if prod_df.empty:
                continue
            if redcap_key in ("thromb_t", "ery_t", "ffp_t"):
                setattr(model, redcap_key, len(prod_df))

    def _get_medication_rate(
        self,
        df: pd.DataFrame,
        pattern: str,
        field_name: str = ""
    ) -> Optional[float]:
        """Holt Laufrate und rechnet zu µg/kg/min um (Vasopressin: IU/h)."""
        if df.empty:
            return None

        mask = df["parameter"].str.contains(pattern, case=False, na=False, regex=True)
        filtered = df[mask]
        if filtered.empty:
            return None

        # Fertigspritzen ausschließen
        fer_mask = ~filtered["parameter"].str.contains(
            r"\(FER\)|Fertigspritze", case=False, na=False, regex=True
        )
        filtered = filtered[fer_mask]
        if filtered.empty:
            return None

        # Rate in ml/h
        if "rate" in filtered.columns:
            rates = pd.to_numeric(filtered["rate"], errors="coerce").dropna()
            rate_ml_h = float(rates.median()) if not rates.empty else None
        else:
            values = pd.to_numeric(filtered["value"], errors="coerce").dropna()
            rate_ml_h = float(values.median()) if not values.empty else None

        if rate_ml_h is None:
            return None

        # Vasopressin: REDCap erwartet IU/h (Perfusor 1 IE/ml)
        if field_name == "vasopressin":
            return round(rate_ml_h, 2)

        conc_ug_ml = self._extract_concentration(filtered, field_name)
        if conc_ug_ml is None:
            return None

        weight_kg = self._get_patient_weight()
        if weight_kg is None:
            logger.warning(
                "Patientengewicht fehlt – Medikamentendosierung '%s' kann nicht berechnet werden.",
                field_name,
            )
            return None

        ug_kg_min = (rate_ml_h * conc_ug_ml) / (60 * weight_kg)
        return round(ug_kg_min, 4)

    def _extract_concentration(self, df: pd.DataFrame, field_name: str) -> Optional[float]:
        """Extrahiert Konzentration in µg/ml aus dem Perfusor-Namen."""
        default_concentrations = {
            "norepinephrine": 100.0,
            "epinephrine":    200.0,
            "dobutamine":    5000.0,
            "milrinone":      200.0,
        }
        for param in df["parameter"].dropna():
            if "(FER)" in param or "Fertigspritze" in param.lower():
                continue
            m = re.search(r"(\d+(?:[,\.]\d+)?)\s*mg\s*/\s*(\d+)\s*ml", param, re.IGNORECASE)
            if m:
                return (float(m.group(1).replace(",", ".")) * 1000) / float(m.group(2))
            m = re.search(r"(\d+(?:[,\.]\d+)?)\s*mg/ml", param, re.IGNORECASE)
            if m:
                if field_name == "dobutamine":
                    return 5000.0
                return float(m.group(1).replace(",", ".")) * 1000
        return default_concentrations.get(field_name)

    def _get_patient_weight(self) -> Optional[float]:
        """Gewicht aus State (manuell) oder PatientInfo-Daten."""
        try:
            from state import get_state
            state = get_state()
            if state.patient_weight is not None:
                return state.patient_weight
        except (ImportError, RuntimeError, AttributeError):
            pass

        full_df = self._data if self._data is not None else None
        if full_df is None:
            try:
                from state import get_data
                full_df = get_data()
            except Exception:
                return None

        if full_df is None or full_df.empty:
            return None

        weight_mask = (
            full_df["source_type"].str.contains("PatientInfo|Grösse/Gewicht", case=False, na=False) &
            full_df["parameter"].str.contains(r"^Gewicht(?:\s*/\s*kg)?$", case=False, na=False, regex=True)
        )
        for val in full_df[weight_mask]["value"]:
            try:
                w = float(str(val).replace(",", "."))
                if 20 < w < 300:
                    return w
            except (ValueError, TypeError):
                continue
        return None

    def _map_ventilation_spec(self, mode_str: str) -> Optional[int]:
        """Mappt Beatmungsmodus-String zu VentilationSpec Integer."""
        normalized = mode_str.upper().replace("-", "_").replace(" ", "_").strip()
        if normalized in VENT_SPEC_MAP:
            enum_name = VENT_SPEC_MAP[normalized]
            if enum_name is None:
                return None
            try:
                return VentilationSpec[enum_name].value
            except KeyError:
                pass
        try:
            return VentilationSpec[normalized].value
        except KeyError:
            pass
        logger.warning("Unbekannter Beatmungsmodus '%s' (normalisiert: '%s')", mode_str, normalized)
        return None
