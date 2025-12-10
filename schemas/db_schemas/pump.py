"""
REDCap Pump (ECMO) Instrument Model.

Erfasst täglich die ECMO-Pumpen-Parameter und mechanische Komplikationen.
Nur in ecls_arm_2 verfügbar!
"""

from pydantic import Field
from typing import Optional, ClassVar
from datetime import date

from .base import TimedExportModel


class PumpModel(TimedExportModel):
    """
    REDCap pump Instrument (ECMO).
    
    NUR verfügbar in: ecls_arm_2
    Repeat-Instrument: Ja (pro Tag eine Instanz)
    
    Erfasst täglich:
    - ECMO-Parameter (Blutfluss, Gasfluss, FiO2, Drehzahl)
    - Mechanische Komplikationen
    """
    
    # Instrument-Metadaten
    INSTRUMENT_NAME: ClassVar[str] = "pump"
    INSTRUMENT_LABEL: ClassVar[str] = "ECMO Pumpe"
    
    # REDCap-Felder mit korrektem Default
    redcap_repeat_instrument: Optional[str] = Field("pump", alias="redcap_repeat_instrument")
    
    # Dieses Instrument ist NUR in ecls_arm_2 verfügbar!
    redcap_event_name: Optional[str] = Field("ecls_arm_2", alias="redcap_event_name")
    
    # Kontrollfelder
    ecls_compl_na: Optional[int] = Field(1, alias="ecls_compl_na")  # Keine Komplikationen
    
    # Zeitpunkt
    ecls_compl_date: Optional[date] = Field(None, alias="ecls_compl_date")
    ecls_compl_time_point: Optional[int] = Field(None, alias="ecls_compl_time_point")
    
    # ==================== ECMO-Parameter ====================
    ecls_pf: Optional[float] = Field(None, alias="ecls_pf")  # Blutfluss L/min
    ecls_fi02: Optional[float] = Field(None, alias="ecls_fi02")  # FiO2 %
    ecls_gf: Optional[float] = Field(None, alias="ecls_gf")  # Gasfluss L/min
    ecls_rpm: Optional[float] = Field(None, alias="ecls_rpm")  # Drehzahl rpm
    
    # ==================== Mechanische Komplikationen ====================
    mechanical_complications: Optional[int] = Field(None, alias="mechanical_complications")
    oxygenator_failure: Optional[int] = Field(None, alias="oxygenator_failure")
    pump_failure: Optional[int] = Field(None, alias="pump_failure")
    raceway_rupture: Optional[int] = Field(None, alias="raceway_rupture")
    other_tubing_ruputure: Optional[int] = Field(None, alias="other_tubing_ruputure")
    circuit_change: Optional[int] = Field(None, alias="circuit_change")
    heat_exchange_malfunction: Optional[int] = Field(None, alias="heat_exchange_malfunction")
    thrombosis_circuit_component: Optional[int] = Field(None, alias="thrombosis_circuit_component")
    cannula_problems: Optional[int] = Field(None, alias="cannula_problems")
    clots_hemofilter: Optional[int] = Field(None, alias="clots_hemofilter")
    air_circuit: Optional[int] = Field(None, alias="air_circuit")
    mc_o: Optional[int] = Field(None, alias="mc_o")  # Andere Komplikation
    mc_o_spec: Optional[str] = Field(None, alias="mc_o_spec")  # Spezifikation
    
    # Completion Status
    pump_complete: Optional[int] = Field(0, alias="pump_complete")
