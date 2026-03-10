"""
Pre-Assessment Aggregator - Pre-Implantation Assessments für Impella und VA-ECLS.
"""

import logging

import pandas as pd
from typing import Optional, Dict, Tuple, List, Any
from datetime import date, time, datetime, timedelta

logger = logging.getLogger(__name__)

from .base import BaseAggregator
from .mapping import (
    HEMODYNAMICS_MEDICATION_MAP,
    MEDICATION_SPEC_MAP,
    NARCOTICS_SPEC_MAP,
    VASOACTIVE_SPEC_MAP,
    VENT_SPEC_MAP,
    SOURCE_MAPPING,
    # Pre-Impella Registries
    PRE_IMPELLA_BGA_REGISTRY,
    PRE_IMPELLA_VENT_REGISTRY,
    PRE_IMPELLA_VENT_SPEC_REGISTRY,
    PRE_IMPELLA_HEMO_REGISTRY,
    PRE_IMPELLA_GCS_REGISTRY,
    PRE_IMPELLA_LAB_REGISTRY,
    # Pre-VAECLS Registries
    PRE_VAECLS_BGA_REGISTRY,
    PRE_VAECLS_VENT_REGISTRY,
    PRE_VAECLS_VENT_SPEC_REGISTRY,
    PRE_VAECLS_HEMO_REGISTRY,
    PRE_VAECLS_GCS_REGISTRY,
    PRE_VAECLS_LAB_REGISTRY,
)
from schemas.db_schemas.pre_assessment import (
    PreImpellaHVLabModel,
    PreImpellaMedicationModel,
    PreVAECLSHVLabModel,
    PreVAECLSMedicationModel,
)
from schemas.db_schemas.hemodynamics import VentilationSpec


class PreDeviceAggregatorBase(BaseAggregator):
    """Basis-Aggregator für Pre-Assessments."""

    def __init__(
        self,
        anchor_datetime: datetime,
        record_id: str,
        data: Optional[pd.DataFrame] = None
    ):
        super().__init__(
            date=anchor_datetime.date(),
            record_id=record_id,
            redcap_event_name="",
            redcap_repeat_instance=None,
            data=data
        )
        self.anchor_datetime = anchor_datetime

    def get_source_data(self, source: str) -> pd.DataFrame:
        """Holt Daten ohne Tages-Filter (Pre-Assessments können mehrere Tage umfassen)."""
        if self._data is None:
            return pd.DataFrame()
        source_lower = source.lower()
        if source_lower in SOURCE_MAPPING:
            target = SOURCE_MAPPING[source_lower]
            if target == "__CONTAINS__":
                mask = self._data["source_type"].str.upper().str.contains(source.upper(), na=False)
            else:
                mask = self._data["source_type"].isin(target)
        else:
            mask = self._data["source_type"].str.lower().str.contains(source_lower, na=False, regex=False)
        return self._data[mask].copy()

    def _get_pre_window_data(self, source_df: pd.DataFrame, max_hours: int = 6) -> pd.DataFrame:
        """Filtert Daten innerhalb von max_hours VOR der Ankerzeit."""
        if source_df.empty:
            return pd.DataFrame()
        start_window = self.anchor_datetime - timedelta(hours=max_hours)
        mask = (source_df["timestamp"] >= start_window) & (source_df["timestamp"] <= self.anchor_datetime)
        return source_df[mask].copy()

    def _get_closest_pre_value(
        self,
        df: pd.DataFrame,
        category_pattern: str,
        param_pattern: str,
        max_hours: int = 6
    ) -> Tuple[Optional[float], Optional[datetime]]:
        """Findet den zeitlich nächsten Wert VOR der Ankerzeit."""
        window_df = self._get_pre_window_data(df, max_hours)
        if window_df.empty:
            return None, None

        param_mask = window_df["parameter"].str.contains(param_pattern, case=False, na=False, regex=True)
        if "category" in window_df.columns and category_pattern != ".*":
            cat_mask = window_df["category"].str.contains(category_pattern, case=False, na=False, regex=True)
            mask = param_mask & cat_mask
        else:
            mask = param_mask

        filtered = window_df[mask].copy()
        if filtered.empty:
            return None, None

        filtered["_val_num"] = filtered["value"].apply(self._to_float)
        filtered = filtered.dropna(subset=["_val_num"])
        if filtered.empty:
            return None, None

        idx = filtered["timestamp"].idxmax()
        row = filtered.loc[idx]
        return float(row["_val_num"]), row["timestamp"]

    def _get_closest_string_pre(
        self, df: pd.DataFrame, category_pattern: str, param_pattern: str, max_hours: int = 6
    ) -> Optional[str]:
        """Findet den zeitlich nächsten String-Wert VOR der Ankerzeit."""
        window_df = self._get_pre_window_data(df, max_hours)
        if window_df.empty:
            return None
        mask = window_df["parameter"].str.contains(param_pattern, case=False, na=False, regex=True)
        filtered = window_df[mask]
        if filtered.empty:
            return None
        idx = filtered["timestamp"].idxmax()
        return str(filtered.loc[idx, "value"])

    def _map_ventilation_spec(self, mode_str: str) -> Optional[int]:
        normalized = mode_str.upper().replace("-", "_").replace(" ", "_").strip()
        if normalized in VENT_SPEC_MAP:
            enum_name = VENT_SPEC_MAP[normalized]
            if enum_name:
                try:
                    return VentilationSpec[enum_name].value
                except KeyError:
                    pass
        return None

    def _get_medication_pre_24h(
        self,
        med_df: pd.DataFrame,
        mapping: Dict[int, str],
        exclude_fer: bool = True
    ) -> Dict[int, int]:
        """Prüft Medikamente im 24h-Fenster vor Implantation."""
        results = {drug_id: 0 for drug_id in mapping}
        window_df = self._get_pre_window_data(med_df, max_hours=24)
        if window_df.empty:
            return results
        for drug_id, pattern in mapping.items():
            mask = window_df["parameter"].str.contains(pattern, case=False, na=False, regex=True)
            if exclude_fer:
                mask &= ~window_df["parameter"].str.contains(
                    r"\(FER\)|Fertigspritze", case=False, na=False, regex=True
                )
            if mask.any():
                results[drug_id] = 1
        return results

    def _get_medication_rate_pre(self, med_df, pattern, field_name, max_hours=24):
        window_df = self._get_pre_window_data(med_df, max_hours)
        if window_df.empty:
            return None
        mask = window_df["parameter"].str.contains(pattern, case=False, na=False, regex=True)
        fer_mask = ~window_df["parameter"].str.contains(
            r"\(FER\)|Fertigspritze", case=False, na=False, regex=True
        )
        filtered = window_df[mask & fer_mask]
        if filtered.empty:
            return None
        idx = filtered["timestamp"].idxmax()
        row = filtered.loc[[idx]]
        from .hemodynamics_aggregator import HemodynamicsAggregator
        mock_agg = HemodynamicsAggregator(
            date=self.anchor_datetime.date(), record_id=self.record_id,
            redcap_event_name="", redcap_repeat_instance=0, data=self._data
        )
        return mock_agg._get_medication_rate(row, pattern, field_name)

    def _process_pre_registry(self, registry: Dict[str, Any], max_hours: int = 6) -> Tuple[Dict[str, Any], List[datetime]]:
        """
        Prozessiert eine Registry für Pre-Assessment Felder.
        Nutzt _get_closest_pre_value, validiert die Ranges und sammelt Timestamps.
        """
        values = {}
        timestamps = []
        df_cache = {}
        
        for redcap_key, spec in registry.items():
            df = df_cache.setdefault(spec.source, self.get_source_data(spec.source))
            val, ts = self._get_closest_pre_value(df, spec.category, spec.pattern, max_hours=max_hours)
            if val is not None:
                values[redcap_key] = val
                self.validate_range(redcap_key, val, spec.min_val, spec.max_val)
                if ts:
                    timestamps.append(ts)
        return values, timestamps

    def create_entry(self):
        return self.create_hv_lab_entry()


# =============================================================================
# Pre-Impella
# =============================================================================

class PreImpellaAggregator(PreDeviceAggregatorBase):
    """Aggregator für Pre-Impella Assessment."""

    def __init__(
        self,
        anchor_datetime: datetime,
        record_id: str,
        data=None,
        ecmella_same_session: Optional[bool] = None,
        redcap_event_name: str = "impella_arm_2"
    ):
        super().__init__(anchor_datetime=anchor_datetime, record_id=record_id, data=data)
        self.ecmella_same_session = ecmella_same_session
        self._event_name = redcap_event_name

    def create_hv_lab_entry(self) -> PreImpellaHVLabModel:
        """Erstellt das Pre-Impella HV-Lab Modell."""
        base = {
            "record_id": self.record_id,
            "redcap_event_name": self._event_name,
            "redcap_repeat_instrument": None,
            "redcap_repeat_instance": None,
        }

        if self.ecmella_same_session:
            logger.info("ECMELLA 2.0: Pre-Impella HV-Lab Parameter entfallen (pre_ecmella_2_0_2=1).")
            base["pre_ecmella_2_0_2"] = 1
            return PreImpellaHVLabModel.model_validate(base)

        base["pre_ecmella_2_0_2"] = 0
        payload = base
        df_cache: Dict[str, pd.DataFrame] = {}

        def get_df(source: str) -> pd.DataFrame:
            return df_cache.setdefault(source, self.get_source_data(source))

        # 1. BGA (6h)
        timestamps: List[datetime] = []
        bga_vals, bga_ts = self._process_pre_registry(PRE_IMPELLA_BGA_REGISTRY, max_hours=6)
        payload.update(bga_vals)
        timestamps.extend(bga_ts)
        has_bga = bool(bga_vals)

        if has_bga:
            payload["pre_bga_i"] = 1
            if payload.get("pre_svo2_i") is not None:
                payload["pre_svo2_m_i"] = 1
            latest_ts = max(timestamps)
            payload["pre_assess_date_i"] = latest_ts.date()
            payload["pre_assess_time_i"] = latest_ts.time()
        else:
            payload["pre_bga_i"] = 0

        if payload.get("pre_svo2_i") is None:
            payload["pre_svo2_m_i"] = 0

        # 2. Beatmung (6h)
        vent_vals, _ = self._process_pre_registry(PRE_IMPELLA_VENT_REGISTRY, max_hours=6)
        payload.update(vent_vals)
        has_vent = bool(vent_vals)

        # Beatmungsmodus (String → Integer)
        for redcap_key, spec in PRE_IMPELLA_VENT_SPEC_REGISTRY.items():
            mode_str = self._get_closest_string_pre(get_df(spec.source), spec.category, spec.pattern, max_hours=6)
            if mode_str:
                spec_val = self._map_ventilation_spec(mode_str)
                if spec_val:
                    payload[redcap_key] = spec_val
                    has_vent = True

        if has_vent:
            payload["pre_vent_i"] = 1
            if payload.get("pre_conv_vent_rate_i") is not None:
                payload["pre_ventilation_i"] = 5
                payload["pre_vent_type_i"] = 1
            elif payload.get("pre_vent_peep_i") is not None:
                payload["pre_ventilation_i"] = 1
            elif payload.get("pre_fi02_i") is not None:
                payload["pre_ventilation_i"] = 6
        else:
            payload["pre_vent_i"] = 0

        # 3. Hämodynamik (6h)
        hemo_vals, _ = self._process_pre_registry(PRE_IMPELLA_HEMO_REGISTRY, max_hours=6)
        payload.update(hemo_vals)
        has_hemo = bool(hemo_vals)

        if has_hemo:
            payload["pre_hemodynamics_i"] = 1
            pac_fields = ["pre_pcwp_i", "pre_sys_pap_i", "pre_dia_pap_i", "pre_mean_pap_i", "pre_ci_i"]
            payload["pre_pac_i"] = 1 if any(payload.get(f) is not None for f in pac_fields) else 0
        else:
            payload["pre_hemodynamics_i"] = 0

        # 4. Neurologie / GCS (6h)
        for redcap_key, spec in PRE_IMPELLA_GCS_REGISTRY.items():
            val, _ = self._get_closest_pre_value(get_df(spec.source), spec.category, spec.pattern, max_hours=6)
            if val is not None:
                payload[redcap_key] = val
                self.validate_range(redcap_key, val, spec.min_val, spec.max_val)
                payload["pre_neuro_i"] = 1
                break
        else:
            payload["pre_neuro_i"] = 0

        # 5. Labor (6h, Fallback 24h)
        has_lab = False
        used_24h = False
        for redcap_key, spec in PRE_IMPELLA_LAB_REGISTRY.items():
            df = get_df(spec.source)
            val, _ = self._get_closest_pre_value(df, spec.category, spec.pattern, max_hours=6)
            if val is None:
                val, _ = self._get_closest_pre_value(df, spec.category, spec.pattern, max_hours=24)
                if val is not None:
                    used_24h = True
            if val is not None:
                payload[redcap_key] = val
                self.validate_range(redcap_key, val, spec.min_val, spec.max_val)
                has_lab = True
                if redcap_key == "pre_crp_i":   payload["pre_crp_m_i"] = 1
                if redcap_key == "pre_pct_i":   payload["pre_pct_m_i"] = 1
                if redcap_key == "pre_act_i":   payload["pre_act_m_i"] = 1
                if redcap_key == "pre_trop_i":  payload["pre_trop_m_i"] = 1

        hemolysis_fields = ["pre_fhb_i", "pre_hapto_i", "pre_bili_i"]
        payload["pre_hemolysis_i"] = 1 if any(payload.get(f) is not None for f in hemolysis_fields) else 0

        if has_lab:
            payload["pre_lab_results_i"] = 1
            payload["pre_lab_results_imp"] = 2 if used_24h else 1
        else:
            payload["pre_lab_results_i"] = 0

        return PreImpellaHVLabModel.model_validate(payload)

    def create_medication_entry(self) -> PreImpellaMedicationModel:
        """Erstellt das Pre-Impella Medikamenten-Modell."""
        base = {
            "record_id": self.record_id,
            "redcap_event_name": self._event_name,
            "redcap_repeat_instrument": None,
            "redcap_repeat_instance": None,
        }

        if self.ecmella_same_session:
            logger.info("ECMELLA 2.0: Pre-Impella Medikamenten-Parameter entfallen (pre_ecmella_2_0=1).")
            base["pre_ecmella_2_0"] = 1
            return PreImpellaMedicationModel.model_validate(base)

        base["pre_ecmella_2_0"] = 0
        payload = base
        med_df = self.get_source_data("medication")

        med_results = self._get_medication_pre_24h(med_df, {k: v for k, v in MEDICATION_SPEC_MAP.items() if k <= 8})
        for drug_id, val in med_results.items():
            payload[f"pre_med_i___{drug_id}"] = val
        payload["pre_med_i___9"] = 0 if any(med_results.values()) else 1

        vaso_results = self._get_medication_pre_24h(med_df, VASOACTIVE_SPEC_MAP)
        for drug_id, val in vaso_results.items():
            payload[f"pre_vasoactive_i___{drug_id}"] = val
        payload["pre_vasoactive_i___17"] = 0 if any(vaso_results.values()) else 1

        for field, pattern in HEMODYNAMICS_MEDICATION_MAP.items():
            val = self._get_medication_rate_pre(med_df, pattern, field, max_hours=24)
            if val is not None:
                payload[f"pre_{field}_i"] = val

        return PreImpellaMedicationModel.model_validate(payload)


# =============================================================================
# Pre-VA-ECLS
# =============================================================================

class PreVAECLSAggregator(PreDeviceAggregatorBase):
    """Aggregator für Pre-VA-ECLS Assessment."""

    def __init__(
        self,
        anchor_datetime: datetime,
        record_id: str,
        data=None,
        redcap_event_name: str = "ecls_arm_2"
    ):
        super().__init__(anchor_datetime=anchor_datetime, record_id=record_id, data=data)
        self._event_name = redcap_event_name

    def create_hv_lab_entry(self) -> PreVAECLSHVLabModel:
        """Erstellt das Pre-ECLS HV-Lab Modell."""
        payload = {
            "record_id": self.record_id,
            "redcap_event_name": self._event_name,
            "redcap_repeat_instrument": None,
            "redcap_repeat_instance": None,
        }
        df_cache: Dict[str, pd.DataFrame] = {}

        def get_df(source: str) -> pd.DataFrame:
            return df_cache.setdefault(source, self.get_source_data(source))

        # 1. BGA (6h)
        timestamps = []
        has_bga = False
        for redcap_key, spec in PRE_VAECLS_BGA_REGISTRY.items():
            val, ts = self._get_closest_pre_value(get_df(spec.source), spec.category, spec.pattern, max_hours=6)
            if val is not None:
                payload[redcap_key] = val
                self.validate_range(redcap_key, val, spec.min_val, spec.max_val)
                timestamps.append(ts)
                has_bga = True
                if redcap_key == "pre_svo2":
                    payload["pre_svo2_m"] = 1

        if has_bga:
            payload["pre_bga"] = 1
            latest_ts = max(timestamps)
            payload["pre_assess_date"] = latest_ts.date()
            payload["pre_assess_time"] = latest_ts.time()
        else:
            payload["pre_bga"] = 0

        if payload.get("pre_svo2") is None:
            payload["pre_svo2_m"] = 0

        # 2. Beatmung (6h)
        has_vent = False
        for redcap_key, spec in PRE_VAECLS_VENT_REGISTRY.items():
            val, _ = self._get_closest_pre_value(get_df(spec.source), spec.category, spec.pattern, max_hours=6)
            if val is not None:
                payload[redcap_key] = val
                self.validate_range(redcap_key, val, spec.min_val, spec.max_val)
                has_vent = True

        for redcap_key, spec in PRE_VAECLS_VENT_SPEC_REGISTRY.items():
            mode_str = self._get_closest_string_pre(get_df(spec.source), spec.category, spec.pattern, max_hours=6)
            if mode_str:
                spec_val = self._map_ventilation_spec(mode_str)
                if spec_val:
                    payload[redcap_key] = spec_val
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

        # 3. Hämodynamik (6h)
        has_hemo = False
        for redcap_key, spec in PRE_VAECLS_HEMO_REGISTRY.items():
            val, _ = self._get_closest_pre_value(get_df(spec.source), spec.category, spec.pattern, max_hours=6)
            if val is not None:
                payload[redcap_key] = val
                self.validate_range(redcap_key, val, spec.min_val, spec.max_val)
                has_hemo = True

        if has_hemo:
            payload["pre_hemodynamics"] = 1
            pac_fields = ["pre_pcwp", "pre_sys_pap", "pre_dia_pap", "pre_mean_pap", "pre_ci"]
            payload["pre_pac"] = 1 if any(payload.get(f) is not None for f in pac_fields) else 0
        else:
            payload["pre_hemodynamics"] = 0

        # 4. Neurologie / GCS (6h)
        for redcap_key, spec in PRE_VAECLS_GCS_REGISTRY.items():
            val, _ = self._get_closest_pre_value(get_df(spec.source), spec.category, spec.pattern, max_hours=6)
            if val is not None:
                payload[redcap_key] = val
                self.validate_range(redcap_key, val, spec.min_val, spec.max_val)
                payload["pre_neuro"] = 1
                break
        else:
            payload["pre_neuro"] = 0

        # 5. Labor (6h, Fallback 24h)
        has_lab = False
        used_24h = False
        for redcap_key, spec in PRE_VAECLS_LAB_REGISTRY.items():
            df = get_df(spec.source)
            val, _ = self._get_closest_pre_value(df, spec.category, spec.pattern, max_hours=6)
            if val is None:
                val, _ = self._get_closest_pre_value(df, spec.category, spec.pattern, max_hours=24)
                if val is not None:
                    used_24h = True
            if val is not None:
                payload[redcap_key] = val
                self.validate_range(redcap_key, val, spec.min_val, spec.max_val)
                has_lab = True
                if redcap_key == "pre_crp":   payload["pre_crp_m"] = 1
                if redcap_key == "pre_pct":   payload["pre_pct_m"] = 1
                if redcap_key == "pre_act":   payload["pre_act_m"] = 1
                if redcap_key == "pre_trop":  payload["pre_trop_m"] = 1

        hemolysis_fields = ["pre_fhb", "pre_hapto", "pre_bili"]
        payload["pre_hemolysis"] = 1 if any(payload.get(f) is not None for f in hemolysis_fields) else 0

        if has_lab:
            payload["pre_lab_results"] = 1
            payload["pre_lab_results_elso"] = 2 if used_24h else 1
        else:
            payload["pre_lab_results"] = 0

        return PreVAECLSHVLabModel.model_validate(payload)

    def create_medication_entry(self) -> PreVAECLSMedicationModel:
        """Erstellt das Pre-ECLS Medikamenten-Modell."""
        payload = {
            "record_id": self.record_id,
            "redcap_event_name": self._event_name,
            "redcap_repeat_instrument": None,
            "redcap_repeat_instance": None,
        }
        med_df = self.get_source_data("medication")

        med_results = self._get_medication_pre_24h(med_df, {k: v for k, v in MEDICATION_SPEC_MAP.items() if k <= 8})
        for drug_id, val in med_results.items():
            payload[f"pre_med___{drug_id}"] = val
        payload["pre_med___9"] = 0 if any(med_results.values()) else 1

        vaso_results = self._get_medication_pre_24h(med_df, VASOACTIVE_SPEC_MAP)
        for drug_id, val in vaso_results.items():
            payload[f"pre_vasoactive___{drug_id}"] = val
        payload["pre_vasoactive___17"] = 0 if any(vaso_results.values()) else 1

        for field, pattern in HEMODYNAMICS_MEDICATION_MAP.items():
            val = self._get_medication_rate_pre(med_df, pattern, field, max_hours=24)
            if val is not None:
                payload[f"pre_{field}"] = val

        return PreVAECLSMedicationModel.model_validate(payload)
