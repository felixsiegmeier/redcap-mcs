"""
REDCap Pre-Assessment Instrument Models.

Enthält Modelle für:
- preimpella_hemodynamics_ventilation_labor
- preimpella
- prevaecls_hemodynamics_ventilation_labor
- prevaecls
"""

from pydantic import Field
from typing import Optional, ClassVar
from datetime import date, time
from enum import IntEnum

from .base import BaseExportModel
from .hemodynamics import VentilationMode, VentilationType, VentilationSpec


class PreHVLabBaseModel(BaseExportModel):
    """Gemeinsame Basis für Pre-HV-Lab Modelle."""
    
    # Zeitpunkt (REDCap Felder werden in Subklassen definiert)
    # pre_assess_date: Optional[date]
    # pre_assess_time: Optional[time]

    # BGA
    # pre_pco2: Optional[float]
    # ...

    class Config:
        populate_by_name = True


class PreImpellaHVLabModel(PreHVLabBaseModel):
    """Instrument: preimpella_hemodynamics_ventilation_labor"""
    
    INSTRUMENT_NAME: ClassVar[str] = "preimpella_hemodynamics_ventilation_labor"
    INSTRUMENT_LABEL: ClassVar[str] = "Pre-Impella Hämodynamik/Beatmung/Labor"
    
    redcap_repeat_instrument: Optional[str] = Field(None, alias="redcap_repeat_instrument")
    redcap_repeat_instance: Optional[int] = Field(None, alias="redcap_repeat_instance")
    
    pre_bga_i: Optional[int] = Field(None, alias="pre_bga_i")
    pre_assess_date_i: Optional[date] = Field(None, alias="pre_assess_date_i")
    pre_assess_time_i: Optional[time] = Field(None, alias="pre_assess_time_i")
    
    pre_pco2_i: Optional[float] = Field(None, alias="pre_pco2_i")
    pre_p02_i: Optional[float] = Field(None, alias="pre_p02_i")
    pre_ph_i: Optional[float] = Field(None, alias="pre_ph_i")
    pre_hco3_i: Optional[float] = Field(None, alias="pre_hco3_i")
    pre_be_i: Optional[float] = Field(None, alias="pre_be_i")
    pre_k_i: Optional[float] = Field(None, alias="pre_k_i")
    pre_na_i: Optional[float] = Field(None, alias="pre_na_i")
    pre_sa02_i: Optional[float] = Field(None, alias="pre_sa02_i")
    pre_gluc_i: Optional[float] = Field(None, alias="pre_gluc_i")
    pre_lactate_i: Optional[float] = Field(None, alias="pre_lactate_i")
    pre_svo2_m_i: Optional[int] = Field(None, alias="pre_svo2_m_i")
    pre_svo2_i: Optional[float] = Field(None, alias="pre_svo2_i")
    
    pre_vent_i: Optional[int] = Field(None, alias="pre_vent_i")
    pre_ventilation_i: Optional[int] = Field(None, alias="pre_ventilation_i")
    pre_02l_i: Optional[float] = Field(None, alias="pre_02l_i")
    pre_fi02_i: Optional[float] = Field(None, alias="pre_fi02_i")
    pre_vent_spec_i: Optional[int] = Field(None, alias="pre_vent_spec_i")
    pre_vent_type_i: Optional[int] = Field(None, alias="pre_vent_type_i")
    pre_hfv_rate_i: Optional[float] = Field(None, alias="pre_hfv_rate_i")
    pre_conv_vent_rate_i: Optional[float] = Field(None, alias="pre_conv_vent_rate_i")
    pre_vent_map_i: Optional[float] = Field(None, alias="pre_vent_map_i")
    pre_vent_pip_i: Optional[float] = Field(None, alias="pre_vent_pip_i")
    pre_vent_peep_i: Optional[float] = Field(None, alias="pre_vent_peep_i")
    
    pre_hemodynamics_i: Optional[int] = Field(None, alias="pre_hemodynamics_i")
    pre_hr_i: Optional[float] = Field(None, alias="pre_hr_i")
    pre_sys_bp_i: Optional[float] = Field(None, alias="pre_sys_bp_i")
    pre_dia_bp_i: Optional[float] = Field(None, alias="pre_dia_bp_i")
    pre_mean_bp_i: Optional[float] = Field(None, alias="pre_mean_bp_i")
    pre_cvd_i: Optional[float] = Field(None, alias="pre_cvd_i")
    pre_sp02_i: Optional[float] = Field(None, alias="pre_sp02_i")
    pre_temp_i: Optional[float] = Field(None, alias="pre_temp_i")
    pre_pac_i: Optional[int] = Field(None, alias="pre_pac_i")
    pre_pcwp_i: Optional[float] = Field(None, alias="pre_pcwp_i")
    pre_sys_pap_i: Optional[float] = Field(None, alias="pre_sys_pap_i")
    pre_dia_pap_i: Optional[float] = Field(None, alias="pre_dia_pap_i")
    pre_mean_pap_i: Optional[float] = Field(None, alias="pre_mean_pap_i")
    pre_ci_i: Optional[float] = Field(None, alias="pre_ci_i")
    
    pre_neuro_i: Optional[int] = Field(None, alias="pre_neuro_i")
    pre_gcs_i: Optional[float] = Field(None, alias="pre_gcs_i")
    
    pre_lab_results_i: Optional[int] = Field(None, alias="pre_lab_results_i")
    pre_lab_results_imp: Optional[int] = Field(None, alias="pre_lab_results_imp")
    pre_wbc_i: Optional[float] = Field(None, alias="pre_wbc_i")
    pre_hb_i: Optional[float] = Field(None, alias="pre_hb_i")
    pre_hct_i: Optional[float] = Field(None, alias="pre_hct_i")
    pre_plt_i: Optional[float] = Field(None, alias="pre_plt_i")
    pre_ptt_i: Optional[float] = Field(None, alias="pre_ptt_i")
    pre_quick_i: Optional[float] = Field(None, alias="pre_quick_i")
    pre_inr_i: Optional[float] = Field(None, alias="pre_inr_i")
    pre_act_m_i: Optional[int] = Field(None, alias="pre_act_m_i")
    pre_act_i: Optional[float] = Field(None, alias="pre_act_i")
    pre_ck_i: Optional[float] = Field(None, alias="pre_ck_i")
    pre_got_i: Optional[float] = Field(None, alias="pre_got_i")
    pre_ldh_i: Optional[float] = Field(None, alias="pre_ldh_i")
    pre_crea_i: Optional[float] = Field(None, alias="pre_crea_i")
    pre_urea_i: Optional[float] = Field(None, alias="pre_urea_i")
    pre_alb_i: Optional[float] = Field(None, alias="pre_alb_i")
    pre_crp_m_i: Optional[int] = Field(None, alias="pre_crp_m_i")
    pre_crp_i: Optional[float] = Field(None, alias="pre_crp_i")
    pre_pct_m_i: Optional[int] = Field(None, alias="pre_pct_m_i")
    pre_pct_i: Optional[float] = Field(None, alias="pre_pct_i")


class PreImpellaMedicationModel(BaseExportModel):
    """Instrument: preimpella"""
    
    INSTRUMENT_NAME: ClassVar[str] = "preimpella"
    INSTRUMENT_LABEL: ClassVar[str] = "Pre-Impella"
    
    redcap_repeat_instrument: Optional[str] = Field(None, alias="redcap_repeat_instrument")
    redcap_repeat_instance: Optional[int] = Field(None, alias="redcap_repeat_instance")
    
    pre_med_i___1: Optional[int] = Field(0, alias="pre_med_i___1")
    pre_med_i___2: Optional[int] = Field(0, alias="pre_med_i___2")
    pre_med_i___3: Optional[int] = Field(0, alias="pre_med_i___3")
    pre_med_i___4: Optional[int] = Field(0, alias="pre_med_i___4")
    pre_med_i___5: Optional[int] = Field(0, alias="pre_med_i___5")
    pre_med_i___6: Optional[int] = Field(0, alias="pre_med_i___6")
    pre_med_i___7: Optional[int] = Field(0, alias="pre_med_i___7")
    pre_med_i___8: Optional[int] = Field(0, alias="pre_med_i___8")
    pre_med_i___9: Optional[int] = Field(0, alias="pre_med_i___9")
    
    pre_vasoactive_i___1: Optional[int] = Field(0, alias="pre_vasoactive_i___1")
    pre_vasoactive_i___2: Optional[int] = Field(0, alias="pre_vasoactive_i___2")
    pre_vasoactive_i___3: Optional[int] = Field(0, alias="pre_vasoactive_i___3")
    pre_vasoactive_i___4: Optional[int] = Field(0, alias="pre_vasoactive_i___4")
    pre_vasoactive_i___5: Optional[int] = Field(0, alias="pre_vasoactive_i___5")
    pre_vasoactive_i___6: Optional[int] = Field(0, alias="pre_vasoactive_i___6")
    pre_vasoactive_i___7: Optional[int] = Field(0, alias="pre_vasoactive_i___7")
    pre_vasoactive_i___8: Optional[int] = Field(0, alias="pre_vasoactive_i___8")
    pre_vasoactive_i___9: Optional[int] = Field(0, alias="pre_vasoactive_i___9")
    pre_vasoactive_i___10: Optional[int] = Field(0, alias="pre_vasoactive_i___10")
    pre_vasoactive_i___11: Optional[int] = Field(0, alias="pre_vasoactive_i___11")
    pre_vasoactive_i___12: Optional[int] = Field(0, alias="pre_vasoactive_i___12")
    pre_vasoactive_i___13: Optional[int] = Field(0, alias="pre_vasoactive_i___13")
    pre_vasoactive_i___14: Optional[int] = Field(0, alias="pre_vasoactive_i___14")
    pre_vasoactive_i___15: Optional[int] = Field(0, alias="pre_vasoactive_i___15")
    pre_vasoactive_i___16: Optional[int] = Field(0, alias="pre_vasoactive_i___16")
    pre_vasoactive_i___17: Optional[int] = Field(0, alias="pre_vasoactive_i___17")
    
    pre_dobutamine_i: Optional[float] = Field(None, alias="pre_dobutamine_i")
    pre_epinephrine_i: Optional[float] = Field(None, alias="pre_epinephrine_i")
    pre_norepinephrine_i: Optional[float] = Field(None, alias="pre_norepinephrine_i")
    pre_vasopressin_i: Optional[float] = Field(None, alias="pre_vasopressin_i")
    pre_milrinone_i: Optional[float] = Field(None, alias="pre_milrinone_i")


class PreVAECLSHVLabModel(PreHVLabBaseModel):
    """Instrument: prevaecls_hemodynamics_ventilation_labor"""
    
    INSTRUMENT_NAME: ClassVar[str] = "prevaecls_hemodynamics_ventilation_labor"
    INSTRUMENT_LABEL: ClassVar[str] = "Pre-ECLS Hämodynamik/Beatmung/Labor"
    
    redcap_repeat_instrument: Optional[str] = Field(None, alias="redcap_repeat_instrument")
    redcap_repeat_instance: Optional[int] = Field(None, alias="redcap_repeat_instance")
    
    pre_bga: Optional[int] = Field(None, alias="pre_bga")
    pre_assess_date: Optional[date] = Field(None, alias="pre_assess_date")
    pre_assess_time: Optional[time] = Field(None, alias="pre_assess_time")
    
    pre_pco2: Optional[float] = Field(None, alias="pre_pco2")
    pre_p02: Optional[float] = Field(None, alias="pre_p02")
    pre_ph: Optional[float] = Field(None, alias="pre_ph")
    pre_hco3: Optional[float] = Field(None, alias="pre_hco3")
    pre_be: Optional[float] = Field(None, alias="pre_be")
    pre_k: Optional[float] = Field(None, alias="pre_k")
    pre_na: Optional[float] = Field(None, alias="pre_na")
    pre_sa02: Optional[float] = Field(None, alias="pre_sa02")
    pre_gluc: Optional[float] = Field(None, alias="pre_gluc")
    pre_lactate: Optional[float] = Field(None, alias="pre_lactate")
    pre_svo2_m: Optional[int] = Field(None, alias="pre_svo2_m")
    pre_svo2: Optional[float] = Field(None, alias="pre_svo2")
    
    pre_vent: Optional[int] = Field(None, alias="pre_vent")
    pre_ventilation: Optional[int] = Field(None, alias="pre_ventilation")
    pre_02l: Optional[float] = Field(None, alias="pre_02l")
    pre_fi02: Optional[float] = Field(None, alias="pre_fi02")
    pre_vent_spec: Optional[int] = Field(None, alias="pre_vent_spec")
    pre_vent_type: Optional[int] = Field(None, alias="pre_vent_type")
    pre_hfv_rate: Optional[float] = Field(None, alias="pre_hfv_rate")
    pre_conv_vent_rate: Optional[float] = Field(None, alias="pre_conv_vent_rate")
    pre_vent_map: Optional[float] = Field(None, alias="pre_vent_map")
    pre_vent_pip: Optional[float] = Field(None, alias="pre_vent_pip")
    pre_vent_peep: Optional[float] = Field(None, alias="pre_vent_peep")
    
    pre_hemodynamics: Optional[int] = Field(None, alias="pre_hemodynamics")
    pre_hr: Optional[float] = Field(None, alias="pre_hr")
    pre_sys_bp: Optional[float] = Field(None, alias="pre_sys_bp")
    pre_dia_bp: Optional[float] = Field(None, alias="pre_dia_bp")
    pre_mean_bp: Optional[float] = Field(None, alias="pre_mean_bp")
    pre_cvd: Optional[float] = Field(None, alias="pre_cvd")
    pre_sp02: Optional[float] = Field(None, alias="pre_sp02")
    pre_temp: Optional[float] = Field(None, alias="pre_temp")
    pre_pac: Optional[int] = Field(None, alias="pre_pac")
    pre_pcwp: Optional[float] = Field(None, alias="pre_pcwp")
    pre_sys_pap: Optional[float] = Field(None, alias="pre_sys_pap")
    pre_dia_pap: Optional[float] = Field(None, alias="pre_dia_pap")
    pre_mean_pap: Optional[float] = Field(None, alias="pre_mean_pap")
    pre_ci: Optional[float] = Field(None, alias="pre_ci")
    
    pre_neuro: Optional[int] = Field(None, alias="pre_neuro")
    pre_gcs: Optional[float] = Field(None, alias="pre_gcs")
    
    pre_lab_results: Optional[int] = Field(None, alias="pre_lab_results")
    pre_lab_results_elso: Optional[int] = Field(None, alias="pre_lab_results_elso")
    pre_wbc: Optional[float] = Field(None, alias="pre_wbc")
    pre_hb: Optional[float] = Field(None, alias="pre_hb")
    pre_hct: Optional[float] = Field(None, alias="pre_hct")
    pre_plt: Optional[float] = Field(None, alias="pre_plt")
    pre_ptt: Optional[float] = Field(None, alias="pre_ptt")
    pre_quick: Optional[float] = Field(None, alias="pre_quick")
    pre_inr: Optional[float] = Field(None, alias="pre_inr")
    pre_act_m: Optional[int] = Field(None, alias="pre_act_m")
    pre_act: Optional[float] = Field(None, alias="pre_act")
    pre_ck: Optional[float] = Field(None, alias="pre_ck")
    pre_got: Optional[float] = Field(None, alias="pre_got")
    pre_ldh: Optional[float] = Field(None, alias="pre_ldh")
    pre_crea: Optional[float] = Field(None, alias="pre_crea")
    pre_urea: Optional[float] = Field(None, alias="pre_urea")
    pre_alb: Optional[float] = Field(None, alias="pre_alb")
    pre_crp_m: Optional[int] = Field(None, alias="pre_crp_m")
    pre_crp: Optional[float] = Field(None, alias="pre_crp")
    pre_pct_m: Optional[int] = Field(None, alias="pre_pct_m")
    pre_pct: Optional[float] = Field(None, alias="pre_pct")


class PreVAECLSMedicationModel(BaseExportModel):
    """Instrument: prevaecls"""
    
    INSTRUMENT_NAME: ClassVar[str] = "prevaecls"
    INSTRUMENT_LABEL: ClassVar[str] = "Pre-ECLS"
    
    redcap_repeat_instrument: Optional[str] = Field(None, alias="redcap_repeat_instrument")
    redcap_repeat_instance: Optional[int] = Field(None, alias="redcap_repeat_instance")
    
    pre_med___1: Optional[int] = Field(0, alias="pre_med___1")
    pre_med___2: Optional[int] = Field(0, alias="pre_med___2")
    pre_med___3: Optional[int] = Field(0, alias="pre_med___3")
    pre_med___4: Optional[int] = Field(0, alias="pre_med___4")
    pre_med___5: Optional[int] = Field(0, alias="pre_med___5")
    pre_med___6: Optional[int] = Field(0, alias="pre_med___6")
    pre_med___7: Optional[int] = Field(0, alias="pre_med___7")
    pre_med___8: Optional[int] = Field(0, alias="pre_med___8")
    pre_med___9: Optional[int] = Field(0, alias="pre_med___9")
    
    pre_vasoactive___1: Optional[int] = Field(0, alias="pre_vasoactive___1")
    pre_vasoactive___2: Optional[int] = Field(0, alias="pre_vasoactive___2")
    pre_vasoactive___3: Optional[int] = Field(0, alias="pre_vasoactive___3")
    pre_vasoactive___4: Optional[int] = Field(0, alias="pre_vasoactive___4")
    pre_vasoactive___5: Optional[int] = Field(0, alias="pre_vasoactive___5")
    pre_vasoactive___6: Optional[int] = Field(0, alias="pre_vasoactive___6")
    pre_vasoactive___7: Optional[int] = Field(0, alias="pre_vasoactive___7")
    pre_vasoactive___8: Optional[int] = Field(0, alias="pre_vasoactive___8")
    pre_vasoactive___9: Optional[int] = Field(0, alias="pre_vasoactive___9")
    pre_vasoactive___10: Optional[int] = Field(0, alias="pre_vasoactive___10")
    pre_vasoactive___11: Optional[int] = Field(0, alias="pre_vasoactive___11")
    pre_vasoactive___12: Optional[int] = Field(0, alias="pre_vasoactive___12")
    pre_vasoactive___13: Optional[int] = Field(0, alias="pre_vasoactive___13")
    pre_vasoactive___14: Optional[int] = Field(0, alias="pre_vasoactive___14")
    pre_vasoactive___15: Optional[int] = Field(0, alias="pre_vasoactive___15")
    pre_vasoactive___16: Optional[int] = Field(0, alias="pre_vasoactive___16")
    pre_vasoactive___17: Optional[int] = Field(0, alias="pre_vasoactive___17")
    pre_vasoactive___18: Optional[int] = Field(0, alias="pre_vasoactive___18")
    
    pre_dobutamine: Optional[float] = Field(None, alias="pre_dobutamine")
    pre_epinephrine: Optional[float] = Field(None, alias="pre_epinephrine")
    pre_norepinephrine: Optional[float] = Field(None, alias="pre_norepinephrine")
    pre_vasopressin: Optional[float] = Field(None, alias="pre_vasopressin")
    pre_milrinone: Optional[float] = Field(None, alias="pre_milrinone")
