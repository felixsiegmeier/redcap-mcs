"""
Pre-Assessment Aggregator - Basis-Logik für Pre-Implantation Assessments.
"""

import pandas as pd
from typing import Optional, Dict, Tuple, Type, List
from datetime import date, time, datetime, timedelta
import re

from .base import BaseAggregator
from .mapping import (
    HEMODYNAMICS_FIELD_MAP,
    LAB_FIELD_MAP,
    MEDICATION_SPEC_MAP,
    NARCOTICS_SPEC_MAP,
    VASOACTIVE_SPEC_MAP,
    VENT_SPEC_MAP,
    HEMODYNAMICS_MEDICATION_MAP
)
from schemas.db_schemas.pre_assessment import (
    PreImpellaHVLabModel,
    PreImpellaMedicationModel,
    PreVAECLSHVLabModel,
    PreVAECLSMedicationModel
)
from schemas.db_schemas.hemodynamics import VentilationSpec, VentilationType


class PreDeviceAggregatorBase(BaseAggregator):
    """Basis-Aggregator für Pre-Assessments."""

    def __init__(
        self,
        anchor_datetime: datetime,
        record_id: str,
        data: Optional[pd.DataFrame] = None
    ):
        """
        Args:
            anchor_datetime: Der Implantationszeitpunkt (Anker).
            record_id: REDCap Record ID.
            data: Gesamter Daten-DataFrame.
        """
        # Wir rufen super().__init__ mit dem Datum der Ankerzeit auf.
        # redcap_event_name und repeat_instance sind für Pre-Assessments 
        # meist irrelevant, da sie kein repeating instrument sind.
        super().__init__(
            date=anchor_datetime.date(),
            record_id=record_id,
            redcap_event_name="", 
            redcap_repeat_instance=0,
            data=data
        )
        self.anchor_datetime = anchor_datetime

    def get_source_data(self, source: str) -> pd.DataFrame:
        """Holt die Daten für eine bestimmte Quelle ohne Tages-Filter (da Pre-Assessments über Tage gehen können)."""
        if self._data is None:
            return pd.DataFrame()
        
        from state import SOURCE_MAPPING
        source_lower = source.lower()
        
        # Mapping anwenden
        if source_lower in SOURCE_MAPPING:
            target = SOURCE_MAPPING[source_lower]
            if target == "__CONTAINS__":
                mask = self._data["source_type"].str.upper().str.contains(source.upper(), na=False)
            else:
                mask = self._data["source_type"].isin(target)
        else:
            mask = self._data["source_type"].str.lower().str.contains(source.lower(), na=False)
            
        return self._data[mask].copy()

    def _get_pre_window_data(
        self, 
        source_df: pd.DataFrame, 
        max_hours: int = 6
    ) -> pd.DataFrame:
        """Filtert Daten, die maximal X Stunden VOR der Ankerzeit liegen."""
        if source_df.empty:
            return pd.DataFrame()
            
        start_window = self.anchor_datetime - timedelta(hours=max_hours)
        
        # Filter: Zeitstempel muss zwischen [Anker - Xh] und [Anker] liegen
        mask = (source_df["timestamp"] >= start_window) & (source_df["timestamp"] <= self.anchor_datetime)
        return source_df[mask].copy()

    def _get_closest_pre_value(
        self, 
        df: pd.DataFrame, 
        category_pattern: str, 
        param_pattern: str,
        max_hours: int = 6
    ) -> Tuple[Optional[float], Optional[datetime]]:
        """Findet den Wert, der zeitlich am nächsten VOR der Ankerzeit liegt."""
        window_df = self._get_pre_window_data(df, max_hours)
        if window_df.empty:
            return None, None
            
        # Parameter/Kategorie Filter
        param_mask = window_df["parameter"].str.contains(param_pattern, case=False, na=False, regex=True)
        if "category" in window_df.columns and category_pattern != ".*":
            cat_mask = window_df["category"].str.contains(category_pattern, case=False, na=False, regex=True)
            mask = param_mask & cat_mask
        else:
            mask = param_mask
            
        filtered = window_df[mask].copy()
        if filtered.empty:
            return None, None
            
        # Numerische Konvertierung (robust, z. B. ">180")
        filtered["_val_num"] = filtered["value"].apply(self._to_float)
        filtered = filtered.dropna(subset=["_val_num"])
        if filtered.empty:
            return None, None
            
        # Nächsten Wert zur Ankerzeit finden (idxmax da t <= anchor)
        idx = filtered["timestamp"].idxmax()
        row = filtered.loc[idx]
        return float(row["_val_num"]), row["timestamp"]

    def _get_medication_pre_24h(
        self,
        med_df: pd.DataFrame,
        mapping: Dict[int, str],
        exclude_fer: bool = True
    ) -> Dict[int, int]:
        """Prüft Medikamente im 24h Fenster vor Implantation."""
        results = {drug_id: 0 for drug_id in mapping.keys()}
        window_df = self._get_pre_window_data(med_df, max_hours=24)
        
        if window_df.empty:
            return results
            
        for drug_id, pattern in mapping.items():
            mask = window_df["parameter"].str.contains(pattern, case=False, na=False, regex=True)
            if exclude_fer:
                fer_mask = ~window_df["parameter"].str.contains(r"\(FER\)|Fertigspritze", case=False, na=False, regex=True)
                mask = mask & fer_mask
            
            if mask.any():
                results[drug_id] = 1
                
        return results

    def create_entry(self):
        """Pre-Aggregatoren haben mehrere Entries (HV/Lab und Medication). 
        Diese Methode wird hier nur implementiert um die Abstraktion zu erfüllen.
        """
        return self.create_hv_lab_entry()


class PreImpellaAggregator(PreDeviceAggregatorBase):
    """Aggregator für Pre-Impella Assessment."""

    def create_hv_lab_entry(self) -> PreImpellaHVLabModel:
        """Erstellt das Pre-Impella HV-Lab Modell."""
        vitals_df = self.get_source_data("vitals")
        resp_df = self.get_source_data("respiratory")
        lab_df = self.get_source_data("lab")
        gcs_df = self.get_source_data("GCS (Jugendliche und Erwachsene)")
        
        payload = {
            "record_id": self.record_id,
            "redcap_event_name": "impella_arm_2",
            "redcap_repeat_instrument": None,
            "redcap_repeat_instance": None,
        }
        
        # 1. BGA & Labor (6h Fenster)
        # Wir sammeln die Zeitpunkte um das assessment_date/time zu setzen
        timestamps = []
        
        # BGA
        bga_fields = ["pco2", "p02", "ph", "hco3", "be", "k", "na", "sa02", "gluc", "lactate", "svo2"]
        key_alias = {"pco2": "pc02", "svo2": "sv02"}
        has_bga = False
        for field in bga_fields:
            map_key = key_alias.get(field, field)
            if map_key in LAB_FIELD_MAP:
                src, cat, pat = LAB_FIELD_MAP[map_key]
                val, ts = self._get_closest_pre_value(lab_df, cat, pat, max_hours=6)
                if val is not None:
                    payload[f"pre_{field}_i"] = val
                    timestamps.append(ts)
                    has_bga = True
        
        if has_bga:
            payload["pre_bga_i"] = 1
            # Nimm den Zeitstempel des letzten BGA-Wertes für das Assessment
            latest_ts = max(timestamps)
            payload["pre_assess_date_i"] = latest_ts.date()
            payload["pre_assess_time_i"] = latest_ts.time()
        else:
            payload["pre_bga_i"] = 0

        # 2. Beatmung (6h Fenster)
        vent_fields = ["fi02", "o2", "vent_peep", "vent_pip", "conv_vent_rate"]
        has_vent = False
        for field in vent_fields:
            if field in HEMODYNAMICS_FIELD_MAP:
                src, cat, pat = HEMODYNAMICS_FIELD_MAP[field]
                val, _ = self._get_closest_pre_value(resp_df, cat, pat, max_hours=6)
                if val is not None:
                    payload[f"pre_{field}_i"] = val
                    has_vent = True
        
        # Beatmungsmodus
        src, cat, pat = HEMODYNAMICS_FIELD_MAP["vent_spec"]
        vent_mode_str = self._get_closest_string_pre(resp_df, cat, pat, max_hours=6)
        if vent_mode_str:
            spec_val = self._map_ventilation_spec(vent_mode_str)
            if spec_val:
                payload["pre_vent_spec_i"] = spec_val
                has_vent = True

        if has_vent:
            payload["pre_vent_i"] = 1
            # Ableitung von pre_ventilation_i (Radio)
            # 5 Invasive, 1 Non invasive, 6 High Flow, 4 No ventilation
            if payload.get("pre_conv_vent_rate_i") is not None:
                payload["pre_ventilation_i"] = 5
                payload["pre_vent_type_i"] = 1 # Conventional
            elif payload.get("pre_vent_peep_i") is not None:
                payload["pre_ventilation_i"] = 1
            elif payload.get("pre_fi02_i") is not None:
                payload["pre_ventilation_i"] = 6
        else:
            payload["pre_vent_i"] = 0

        # 3. Hämodynamik (6h Fenster)
        hemo_fields = ["hr", "sys_bp", "dia_bp", "mean_bp", "cvp", "sp02", "pcwp", "sys_pap", "dia_pap", "mean_pap", "ci"]
        has_hemo = False
        for field in hemo_fields:
            if field in HEMODYNAMICS_FIELD_MAP:
                src, cat, pat = HEMODYNAMICS_FIELD_MAP[field]
                # CVP Mapping Fix
                alias = "cvd_i" if field == "cvp" else f"{field}_i"
                val, _ = self._get_closest_pre_value(vitals_df, cat, pat, max_hours=6)
                if val is not None:
                    payload[f"pre_{alias}"] = val
                    has_hemo = True
        
        if has_hemo:
            payload["pre_hemodynamics_i"] = 1
            # PAC Check
            pac_fields = ["pre_pcwp_i", "pre_sys_pap_i", "pre_dia_pap_i", "pre_mean_pap_i", "pre_ci_i"]
            if any(payload.get(f) is not None for f in pac_fields):
                payload["pre_pac_i"] = 1
            else:
                payload["pre_pac_i"] = 0
        else:
            payload["pre_hemodynamics_i"] = 0

        # 4. Neurologie (6h Fenster)
        src, cat, pat = HEMODYNAMICS_FIELD_MAP["gcs"]
        gcs_val, _ = self._get_closest_pre_value(gcs_df, cat, pat, max_hours=6)
        if gcs_val is not None:
            payload["pre_gcs_i"] = gcs_val
            payload["pre_neuro_i"] = 1
        else:
            payload["pre_neuro_i"] = 0

        # 5. Labor (6h mit Fallback auf 24h)
        lab_fields = ["wbc", "hb", "hct", "plt", "ptt", "quick", "inr", "ck", "got", "ldh", "crea", "urea", "alb", "crp", "pct", "act"]
        has_lab = False
        used_24h = False
        
        key_alias = {"alb": "albumin"}
        for field in lab_fields:
            map_key = key_alias.get(field, field)
            if map_key in LAB_FIELD_MAP:
                src, cat, pat = LAB_FIELD_MAP[map_key]
                # Erst 6h
                val, _ = self._get_closest_pre_value(lab_df, cat, pat, max_hours=6)
                if val is None:
                    # Fallback 24h
                    val, _ = self._get_closest_pre_value(lab_df, cat, pat, max_hours=24)
                    if val is not None:
                        used_24h = True
                
                if val is not None:
                    payload[f"pre_{field}_i"] = val
                    has_lab = True
                    # Control fields (measured?)
                    if field == "crp": payload["pre_crp_m_i"] = 1
                    if field == "pct": payload["pre_pct_m_i"] = 1
                    if field == "act": payload["pre_act_m_i"] = 1

        if has_lab:
            payload["pre_lab_results_i"] = 1
            payload["pre_lab_results_imp"] = 2 if used_24h else 1
        else:
            payload["pre_lab_results_i"] = 0

        return PreImpellaHVLabModel.model_validate(payload)

    def create_medication_entry(self) -> PreImpellaMedicationModel:
        """Erstellt das Pre-Impella Medikamenten-Modell."""
        med_df = self.get_source_data("medication")
        
        payload = {
            "record_id": self.record_id,
            "redcap_event_name": "impella_arm_2",
            "redcap_repeat_instrument": None,
            "redcap_repeat_instance": None,
        }
        
        # 1. Spezifische Medikation (24h)
        # Filter nur für IDs 1-8 (da 9=None, 10/11 nicht in Pre-Impella vorhanden)
        med_results = self._get_medication_pre_24h(med_df, {k: v for k, v in MEDICATION_SPEC_MAP.items() if k <= 8})
        for drug_id, val in med_results.items():
            payload[f"pre_med_i___{drug_id}"] = val
        
        # 'None' (9)
        if all(v == 0 for v in med_results.values()):
            payload["pre_med_i___9"] = 1
        else:
            payload["pre_med_i___9"] = 0
            
        # 2. Vasoaktive Substanzen (24h)
        vaso_results = self._get_medication_pre_24h(med_df, VASOACTIVE_SPEC_MAP)
        for drug_id, val in vaso_results.items():
            payload[f"pre_vasoactive_i___{drug_id}"] = val
            
        # 'None' (17)
        if all(v == 0 for v in vaso_results.values()):
            payload["pre_vasoactive_i___17"] = 1
        else:
            payload["pre_vasoactive_i___17"] = 0
            
        # Dosen der wichtigsten Katecholamine (closest in 24h)
        for field, pattern in HEMODYNAMICS_MEDICATION_MAP.items():
            val = self._get_medication_rate_pre(med_df, pattern, field, max_hours=24)
            if val is not None:
                payload[f"pre_{field}_i"] = val
                
        return PreImpellaMedicationModel.model_validate(payload)

    # --- Hilfsmethoden ---

    def _get_closest_string_pre(self, df, cat, pat, max_hours=6):
        window_df = self._get_pre_window_data(df, max_hours)
        if window_df.empty: return None
        mask = window_df["parameter"].str.contains(pat, case=False, na=False, regex=True)
        filtered = window_df[mask]
        if filtered.empty: return None
        idx = filtered["timestamp"].idxmax()
        return str(filtered.loc[idx, "value"])

    def _map_ventilation_spec(self, mode_str: str) -> Optional[int]:
        normalized = mode_str.upper().replace("-", "_").replace(" ", "_").strip()
        if normalized in VENT_SPEC_MAP:
            enum_name = VENT_SPEC_MAP[normalized]
            if enum_name:
                try:
                    return VentilationSpec[enum_name].value
                except KeyError: pass
        return None

    def _get_medication_rate_pre(self, med_df, pattern, field_name, max_hours=24):
        window_df = self._get_pre_window_data(med_df, max_hours)
        if window_df.empty: return None
        
        mask = window_df["parameter"].str.contains(pattern, case=False, na=False, regex=True)
        # Exclude bolus
        fer_mask = ~window_df["parameter"].str.contains(r"\(FER\)|Fertigspritze", case=False, na=False, regex=True)
        filtered = window_df[mask & fer_mask]
        if filtered.empty: return None
        
        # Closest to anchor
        idx = filtered["timestamp"].idxmax()
        row = filtered.loc[[idx]] # as df
        
        # Use existing rate calculation logic from HemodynamicsAggregator or similar
        # Since we are in PreAggregator, we might need to duplicate or move that logic.
        # For now, let's assume we can calculate it if weight is available.
        from .hemodynamics_aggregator import HemodynamicsAggregator
        # Mock a HemodynamicsAggregator to reuse its weight/conc logic
        mock_agg = HemodynamicsAggregator(date=self.anchor_datetime.date(), record_id=self.record_id, redcap_event_name="", redcap_repeat_instance=0, data=self._data)
        return mock_agg._get_medication_rate(row, pattern, field_name)


class PreVAECLSAggregator(PreDeviceAggregatorBase):
    """Aggregator für Pre-VA-ECLS Assessment."""

    def create_hv_lab_entry(self) -> PreVAECLSHVLabModel:
        """Erstellt das Pre-ECLS HV-Lab Modell."""
        vitals_df = self.get_source_data("vitals")
        resp_df = self.get_source_data("respiratory")
        lab_df = self.get_source_data("lab")
        gcs_df = self.get_source_data("GCS (Jugendliche und Erwachsene)")
        
        payload = {
            "record_id": self.record_id,
            "redcap_event_name": "ecls_arm_2",
            "redcap_repeat_instrument": None,
            "redcap_repeat_instance": None,
        }
        
        # 1. BGA & Labor (6h Fenster)
        timestamps = []
        bga_fields = ["pco2", "p02", "ph", "hco3", "be", "k", "na", "sa02", "gluc", "lactate", "svo2"]
        key_alias = {"pco2": "pc02", "svo2": "sv02"}
        has_bga = False
        for field in bga_fields:
            map_key = key_alias.get(field, field)
            if map_key in LAB_FIELD_MAP:
                src, cat, pat = LAB_FIELD_MAP[map_key]
                val, ts = self._get_closest_pre_value(lab_df, cat, pat, max_hours=6)
                if val is not None:
                    payload[f"pre_{field}"] = val
                    timestamps.append(ts)
                    has_bga = True
        
        if has_bga:
            payload["pre_bga"] = 1
            latest_ts = max(timestamps)
            payload["pre_assess_date"] = latest_ts.date()
            payload["pre_assess_time"] = latest_ts.time()
        else:
            payload["pre_bga"] = 0

        # 2. Beatmung (6h Fenster)
        vent_fields = ["fi02", "o2", "vent_peep", "vent_pip", "conv_vent_rate"]
        has_vent = False
        for field in vent_fields:
            if field in HEMODYNAMICS_FIELD_MAP:
                src, cat, pat = HEMODYNAMICS_FIELD_MAP[field]
                val, _ = self._get_closest_pre_value(resp_df, cat, pat, max_hours=6)
                if val is not None:
                    payload[f"pre_{field}"] = val
                    has_vent = True
        
        src, cat, pat = HEMODYNAMICS_FIELD_MAP["vent_spec"]
        vent_mode_str = self._get_closest_string_pre(resp_df, cat, pat, max_hours=6)
        if vent_mode_str:
            spec_val = self._map_ventilation_spec(vent_mode_str)
            if spec_val:
                payload["pre_vent_spec"] = spec_val
                has_vent = True

        if has_vent:
            payload["pre_vent"] = 1
            if payload.get("pre_conv_vent_rate") is not None:
                payload["pre_ventilation"] = 5
                payload["pre_vent_type"] = 1
            elif payload.get("pre_vent_peep") is not None:
                payload["pre_ventilation"] = 1
            elif payload.get("pre_fi02") is not None:
                payload["pre_ventilation"] = 6
        else:
            payload["pre_vent"] = 0

        # 3. Hämodynamik (6h Fenster)
        hemo_fields = ["hr", "sys_bp", "dia_bp", "mean_bp", "cvp", "sp02", "pcwp", "sys_pap", "dia_pap", "mean_pap", "ci"]
        has_hemo = False
        for field in hemo_fields:
            if field in HEMODYNAMICS_FIELD_MAP:
                src, cat, pat = HEMODYNAMICS_FIELD_MAP[field]
                alias = "cvd" if field == "cvp" else field
                val, _ = self._get_closest_pre_value(vitals_df, cat, pat, max_hours=6)
                if val is not None:
                    payload[f"pre_{alias}"] = val
                    has_hemo = True
        
        if has_hemo:
            payload["pre_hemodynamics"] = 1
            pac_fields = ["pre_pcwp", "pre_sys_pap", "pre_dia_pap", "pre_mean_pap", "pre_ci"]
            if any(payload.get(f) is not None for f in pac_fields):
                payload["pre_pac"] = 1
            else:
                payload["pre_pac"] = 0
        else:
            payload["pre_hemodynamics"] = 0

        # 4. Neurologie (6h Fenster)
        src, cat, pat = HEMODYNAMICS_FIELD_MAP["gcs"]
        gcs_val, _ = self._get_closest_pre_value(gcs_df, cat, pat, max_hours=6)
        if gcs_val is not None:
            payload["pre_gcs"] = gcs_val
            payload["pre_neuro"] = 1
        else:
            payload["pre_neuro"] = 0

        # 5. Labor (6h mit Fallback auf 24h)
        lab_fields = ["wbc", "hb", "hct", "plt", "ptt", "quick", "inr", "ck", "got", "ldh", "crea", "urea", "alb", "crp", "pct", "act"]
        has_lab = False
        used_24h = False
        
        key_alias = {"alb": "albumin"}
        for field in lab_fields:
            map_key = key_alias.get(field, field)
            if map_key in LAB_FIELD_MAP:
                src, cat, pat = LAB_FIELD_MAP[map_key]
                val, _ = self._get_closest_pre_value(lab_df, cat, pat, max_hours=6)
                if val is None:
                    val, _ = self._get_closest_pre_value(lab_df, cat, pat, max_hours=24)
                    if val is not None:
                        used_24h = True
                
                if val is not None:
                    payload[f"pre_{field}"] = val
                    has_lab = True
                    if field == "crp": payload["pre_crp_m"] = 1
                    if field == "pct": payload["pre_pct_m"] = 1
                    if field == "act": payload["pre_act_m"] = 1

        if has_lab:
            payload["pre_lab_results"] = 1
            payload["pre_lab_results_elso"] = 2 if used_24h else 1
        else:
            payload["pre_lab_results"] = 0

        return PreVAECLSHVLabModel.model_validate(payload)

    def create_medication_entry(self) -> PreVAECLSMedicationModel:
        """Erstellt das Pre-ECLS Medikamenten-Modell."""
        med_df = self.get_source_data("medication")
        payload = {
            "record_id": self.record_id,
            "redcap_event_name": "ecls_arm_2",
            "redcap_repeat_instrument": None,
            "redcap_repeat_instance": None,
        }
        
        # 1. Spezifische Medikation (24h)
        # Filter nur für IDs 1-8 (da 9=None, 10/11 nicht in Pre-ECLS vorhanden)
        med_results = self._get_medication_pre_24h(med_df, {k: v for k, v in MEDICATION_SPEC_MAP.items() if k <= 8})
        for drug_id, val in med_results.items():
            payload[f"pre_med___{drug_id}"] = val
        if all(v == 0 for v in med_results.values()):
            payload["pre_med___9"] = 1
        else:
            payload["pre_med___9"] = 0
            
        # 2. Vasoaktive Substanzen (24h)
        vaso_results = self._get_medication_pre_24h(med_df, VASOACTIVE_SPEC_MAP)
        for drug_id, val in vaso_results.items():
            payload[f"pre_vasoactive___{drug_id}"] = val
        if all(v == 0 for v in vaso_results.values()):
            payload["pre_vasoactive___17"] = 1
        else:
            payload["pre_vasoactive___17"] = 0
            
        for field, pattern in HEMODYNAMICS_MEDICATION_MAP.items():
            val = self._get_medication_rate_pre(med_df, pattern, field, max_hours=24)
            if val is not None:
                payload[f"pre_{field}"] = val
                
        return PreVAECLSMedicationModel.model_validate(payload)
    
    def _get_closest_string_pre(self, df, cat, pat, max_hours=6):
        # Same as in Impella, could be moved to base
        window_df = self._get_pre_window_data(df, max_hours)
        if window_df.empty: return None
        mask = window_df["parameter"].str.contains(pat, case=False, na=False, regex=True)
        filtered = window_df[mask]
        if filtered.empty: return None
        idx = filtered["timestamp"].idxmax()
        return str(filtered.loc[idx, "value"])

    def _map_ventilation_spec(self, mode_str: str) -> Optional[int]:
        # Same as in Impella
        normalized = mode_str.upper().replace("-", "_").replace(" ", "_").strip()
        if normalized in VENT_SPEC_MAP:
            enum_name = VENT_SPEC_MAP[normalized]
            if enum_name:
                try: return VentilationSpec[enum_name].value
                except KeyError: pass
        return None

    def _get_medication_rate_pre(self, med_df, pattern, field_name, max_hours=24):
        # Same as in Impella
        window_df = self._get_pre_window_data(med_df, max_hours)
        if window_df.empty: return None
        mask = window_df["parameter"].str.contains(pattern, case=False, na=False, regex=True)
        fer_mask = ~window_df["parameter"].str.contains(r"\(FER\)|Fertigspritze", case=False, na=False, regex=True)
        filtered = window_df[mask & fer_mask]
        if filtered.empty: return None
        idx = filtered["timestamp"].idxmax()
        row = filtered.loc[[idx]]
        from .hemodynamics_aggregator import HemodynamicsAggregator
        mock_agg = HemodynamicsAggregator(date=self.anchor_datetime.date(), record_id=self.record_id, redcap_event_name="", redcap_repeat_instance=0, data=self._data)
        return mock_agg._get_medication_rate(row, pattern, field_name)
