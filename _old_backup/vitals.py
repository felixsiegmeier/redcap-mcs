from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class VitalsModel(BaseModel):
    # REDCap Meta
    record_id: str = Field(..., alias="record_id")
    redcap_event_name: str = Field(..., alias="redcap_event_name")
    redcap_repeat_instrument: Optional[str] = Field(None, alias="redcap_repeat_instrument")
    redcap_repeat_instance: Optional[int] = Field(None, alias="redcap_repeat_instance")

    # Erhebungszeitpunkt
    assess_time_point: Optional[str] = Field(None, alias="assess_time_point")
    assess_date_hemo: Optional[date] = Field(None, alias="assess_date_hemo")

    # NIRS
    nirs_avail: Optional[bool] = Field(None, alias="nirs_avail")
    nirs_loc___1: Optional[bool] = Field(None, alias="nirs_loc___1")
    nirs_loc___2: Optional[bool] = Field(None, alias="nirs_loc___2")
    nirs_left_c: Optional[float] = Field(None, alias="nirs_left_c")
    nirs_right_c: Optional[float] = Field(None, alias="nirs_right_c")
    nirs_left_f: Optional[float] = Field(None, alias="nirs_left_f")
    nirs_right_f: Optional[float] = Field(None, alias="nirs_right_f")
    nirs_change: Optional[bool] = Field(None, alias="nirs_change")
    nirs_change_spec: Optional[float] = Field(None, alias="nirs_change_spec")

    # Hämodynamik
    hr: Optional[float] = Field(None, alias="hr")
    sys_bp: Optional[float] = Field(None, alias="sys_bp")
    dia_bp: Optional[float] = Field(None, alias="dia_bp")
    mean_bp: Optional[float] = Field(None, alias="mean_bp")
    cvp: Optional[float] = Field(None, alias="cvp")
    sp02: Optional[float] = Field(None, alias="sp02")
    pac: Optional[bool] = Field(None, alias="pac")
    pcwp: Optional[float] = Field(None, alias="pcwp")
    sys_pap: Optional[float] = Field(None, alias="sys_pap")
    dia_pap: Optional[float] = Field(None, alias="dia_pap")
    mean_pap: Optional[float] = Field(None, alias="mean_pap")
    ci: Optional[float] = Field(None, alias="ci")

    # Neurologie/Mobilisation (wenn vorhanden)
    gcs_avail: Optional[bool] = Field(None, alias="gcs_avail")
    gcs: Optional[int] = Field(None, alias="gcs")
    mobil: Optional[str] = Field(None, alias="mobil")
    rass___1: Optional[bool] = Field(None, alias="rass___1")
    rass___2: Optional[bool] = Field(None, alias="rass___2")
    rass___3: Optional[bool] = Field(None, alias="rass___3")
    rass___4: Optional[bool] = Field(None, alias="rass___4")
    rass___5: Optional[bool] = Field(None, alias="rass___5")
    rass___6: Optional[bool] = Field(None, alias="rass___6")
    rass___7: Optional[bool] = Field(None, alias="rass___7")
    rass___8: Optional[bool] = Field(None, alias="rass___8")
    rass___9: Optional[bool] = Field(None, alias="rass___9")
    rass___10: Optional[bool] = Field(None, alias="rass___10")

    class Config:
        from_attributes = True
        populate_by_name = True