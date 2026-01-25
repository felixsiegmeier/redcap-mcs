"""
REDCap Impella Assessment Instrument Model.

Erfasst täglich die Impella-Parameter und Komplikationen.
Nur in impella_arm_2 verfügbar!
"""

from pydantic import Field
from typing import Optional, ClassVar
from datetime import date
from enum import IntEnum

from .base import TimedExportModel


class ImpellaPumpLevel(IntEnum):
    """Impella Pump Level (P-Level)."""
    P1 = 1
    P2 = 2
    P3 = 3
    P4 = 4
    P5 = 5
    P6 = 6
    P7 = 7
    P8 = 8
    P9 = 9


class ImpellaPositionWrongSpec(IntEnum):
    """Impella position in case of alarm position wrong."""
    AORTA = 1
    VENTRICLE = 2


class ImpellaRepositionSpec(IntEnum):
    """Type of repositioning."""
    HYBRID = 1
    ECHOCARDIOGRAPHIC = 2


class ImpellaAssessmentModel(TimedExportModel):
    """
    REDCap impellaassessment_and_complications Instrument.
    
    NUR verfügbar in: impella_arm_2
    Repeat-Instrument: Ja (pro Tag eine Instanz)
    
    Erfasst täglich:
    - Impella-Parameter (Level, Flow, Purge, RPM)
    - Alarme und Komplikationen
    """
    
    # Instrument-Metadaten
    INSTRUMENT_NAME: ClassVar[str] = "impellaassessment_and_complications"
    INSTRUMENT_LABEL: ClassVar[str] = "Impella Assessment"
    
    # REDCap-Felder mit korrektem Default
    redcap_repeat_instrument: Optional[str] = Field(
        "impellaassessment_and_complications", 
        alias="redcap_repeat_instrument"
    )
    
    # Dieses Instrument ist NUR in impella_arm_2 verfügbar!
    redcap_event_name: Optional[str] = Field("impella_arm_2", alias="redcap_event_name")
    
    # Zeitpunkt
    imp_compl_time_point: Optional[int] = Field(None, alias="imp_compl_time_point")
    imp_compl_date: Optional[date] = Field(None, alias="imp_compl_date")
    
    # ==================== Impella-Parameter ====================
    imp_level: Optional[float] = Field(None, alias="imp_level")  # Level (numerisch)
    imp_p_level: Optional[ImpellaPumpLevel] = Field(None, alias="imp_p_level")  # P-Level (Radio)
    imp_flow: Optional[float] = Field(None, alias="imp_flow")  # Flow L/min
    imp_purge_pressure: Optional[float] = Field(None, alias="imp_purge_pressure")  # Purge-Druck mmHg
    imp_purge_flow: Optional[float] = Field(None, alias="imp_purge_flow")  # Purge-Flow ml/h
    imp_rpm: Optional[float] = Field(None, alias="imp_rpm")  # Drehzahl
    
    # ==================== Alarme & Komplikationen ====================
    imp_alarm: Optional[int] = Field(None, alias="imp_alarm")  # Alarm aufgetreten
    imp_position_wrong: Optional[int] = Field(None, alias="imp_position_wrong")
    imp_position_wrong_spec: Optional[ImpellaPositionWrongSpec] = Field(
        None,
        alias="imp_position_wrong_spec",
    )
    imp_suction: Optional[int] = Field(None, alias="imp_suction")  # Suction Alarm
    imp_position_unknown: Optional[int] = Field(None, alias="imp_position_unknown")
    imp_high_purge_pr: Optional[int] = Field(None, alias="imp_high_purge_pr")  # Hoher Purge-Druck
    imp_thrombolytic: Optional[int] = Field(None, alias="imp_thrombolytic")  # Thrombolyse
    imp_exchange: Optional[int] = Field(None, alias="imp_exchange")  # Gerätewechsel
    imp_reposition: Optional[int] = Field(None, alias="imp_reposition")  # Repositionierung
    imp_reposition_spec: Optional[ImpellaRepositionSpec] = Field(
        None,
        alias="imp_reposition_spec",
    )
    imp_problem: Optional[int] = Field(None, alias="imp_problem")  # Anderes Problem
    imp_problem_spec: Optional[str] = Field(None, alias="imp_problem_spec")
    
    # Completion Status
    impellaassessment_and_complications_complete: Optional[int] = Field(
        0, 
        alias="impellaassessment_and_complications_complete"
    )
