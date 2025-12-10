from pydantic import BaseModel, Field
from typing import Optional, ClassVar
from datetime import datetime, date, time
from enum import IntEnum

from .base import TimedExportModel


class WithdrawalSite(IntEnum):
    ARTERIA_RADIALIS_RIGHT = 1
    ARTERIA_RADIALIS_LEFT = 2
    ARTERIA_FEMORALIS_RIGHT = 3
    ARTERIA_FEMORALIS_LEFT = 4
    ARTERIA_BRACHIALIS_RIGHT = 5
    ARTERIA_BRACHIALIS_LEFT = 6
    UNKNOWN = 7


class LabModel(TimedExportModel):
    """
    REDCap Labor-Instrument (labor).
    
    Erfasst täglich Laborwerte: Blutgase, Hämatologie, Gerinnung, 
    Organfunktion, Infektionsmarker, etc.
    """
    
    # Instrument-Metadaten
    INSTRUMENT_NAME: ClassVar[str] = "labor"
    INSTRUMENT_LABEL: ClassVar[str] = "Labor"
    
    # REDCap-Felder überschreiben mit korrektem Default
    redcap_repeat_instrument: Optional[str] = Field("labor", alias="redcap_repeat_instrument")
    
    # Labor-spezifische Kontroll-Felder
    na_post_2: Optional[int] = Field(1, alias="na_post_2")
    ecmella_2: Optional[int] = Field(0, alias="ecmella_2")

    # Zeitpunkt/Erhebungsmetadaten (Labor-spezifische Aliase)
    assess_time_point_labor: Optional[int] = Field(None, alias="assess_time_point_labor")
    assess_date_labor: Optional[date] = Field(None, alias="assess_date_labor")
    date_assess_labor: Optional[date] = Field(None, alias="date_assess_labor")
    time_assess_labor: Optional[time] = Field(None, alias="time_assess_labor")

    art_site: WithdrawalSite = Field(WithdrawalSite.UNKNOWN, alias="art_site")

    # Blutgas-Parameter
    pc02: Optional[float] = Field(None)
    p02: Optional[float] = Field(None)
    ph: Optional[float] = Field(None)
    hco3: Optional[float] = Field(None)
    be: Optional[float] = Field(None)
    sa02: Optional[float] = Field(None)
    k: Optional[float] = Field(None)
    na: Optional[float] = Field(None)
    gluc: Optional[float] = Field(None)
    lactate: Optional[float] = Field(None)
    sv02: Optional[float] = Field(None)

    # Hämatologie & Gerinnung
    wbc: Optional[float] = Field(None)
    hb: Optional[float] = Field(None)
    hct: Optional[float] = Field(None)
    plt: Optional[float] = Field(None)
    ptt: Optional[float] = Field(None)
    quick: Optional[float] = Field(None)
    inr: Optional[float] = Field(None)
    post_act: Optional[int] = Field(None, alias="post_act")
    act: Optional[float] = Field(None, alias="act")

    # Organsystem-Labore
    ck: Optional[float] = Field(None)
    ckmb: Optional[float] = Field(None)
    got: Optional[float] = Field(None, alias="got")
    alat: Optional[float] = Field(None, alias="alat")
    ggt: Optional[float] = Field(None)
    ldh: Optional[float] = Field(None)
    lipase: Optional[float] = Field(None)
    albumin: Optional[float] = Field(None, alias="albumin")
    post_crp: Optional[int] = Field(None, alias="post_crp")
    crp: Optional[float] = Field(None, alias="crp")
    post_pct: Optional[int] = Field(None, alias="post_pct")
    pct: Optional[float] = Field(None)
    hemolysis: Optional[int] = Field(None, alias="hemolysis")
    fhb: Optional[float] = Field(None)
    hapto: Optional[float] = Field(None, alias="hapto")
    bili: Optional[float] = Field(None)
    crea: Optional[float] = Field(None)
    cc: Optional[float] = Field(None)
    urea: Optional[float] = Field(None)

    labor_complete: Optional[int] = Field(0, alias="labor_complete")
    
    # Config wird von TimedExportModel geerbt