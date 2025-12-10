from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from enum import Enum


class VentilationType(str, Enum):
    INVASIVE = "Invasive Ventilation"
    NON_INVASIVE = "Non invasive Ventilation"
    HIGH_FLOW = "High Flow Therapy"
    NO_VENTILATION = "No Ventilation"


class VentilationSpecifics(str, Enum):
    IPPV = "IPPV"
    BIPAP = "BIPAP"
    SIMV = "SIMV"
    ASB = "ASB"
    PC_BIPAP = "PC-BIPAP"
    PC_PSV = "PC-PSV"
    PC_CMV = "PC-CMV"
    PC_SIMV = "PC-SIMV"
    PC_PC_APRV = "PC-PC-APRV"
    PC_AC = "PC-AC"
    VC_CMV = "VC-CMV"
    VC_SIMV = "VC-SIMV"
    VC_MMV = "VC-MMV"
    VC_AC = "VC-AC"
    SPN_CPAP_PS = "SPN-CPAP/PS"
    BILEVEL = "BiLevel"
    A_C_VC = "A/C VC"
    A_C_PC = "A/C PC"
    A_C_PRVC = "A/C PRVC"
    SIMV_VC = "SIMV-VC"
    SIMV_PC = "SIMV-PC"
    BILEVEL_VG = "BiLevel-VG"
    CPAP_PS = "CPAP/PS"
    SBT = "SBT"
    NIV = "NIV"


class RespiratoryModel(BaseModel):
    # REDCap Meta
    record_id: str = Field(..., alias="record_id")
    redcap_event_name: str = Field(..., alias="redcap_event_name")
    redcap_repeat_instrument: Optional[str] = Field(None, alias="redcap_repeat_instrument")
    redcap_repeat_instance: Optional[int] = Field(None, alias="redcap_repeat_instance")

    # Erhebungszeitpunkt optional, falls aus gleichem Visit
    assess_time_point: Optional[str] = Field(None, alias="assess_time_point")
    assess_date_hemo: Optional[date] = Field(None, alias="assess_date_hemo")

    # Respirator-Einstellungen
    vent: Optional[bool] = Field(None, alias="vent")
    o2: Optional[float] = Field(None, alias="o2")
    fi02: Optional[float] = Field(None, alias="fi02")
    vent_spec: Optional[VentilationSpecifics] = Field(None, alias="vent_spec")
    vent_type: Optional[VentilationType] = Field(None, alias="vent_type")
    hfv_rate: Optional[float] = Field(None, alias="hfv_rate")
    conv_vent_rate: Optional[float] = Field(None, alias="conv_vent_rate")
    vent_map: Optional[float] = Field(None, alias="vent_map")
    vent_pip: Optional[float] = Field(None, alias="vent_pip")
    vent_peep: Optional[float] = Field(None, alias="vent_peep")
    prone_pos: Optional[bool] = Field(None, alias="prone_pos")

    class Config:
        from_attributes = True
        populate_by_name = True
