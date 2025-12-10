"""
Base Export Model - Gemeinsame Basis für alle REDCap-Instrumente.

Alle Instrument-spezifischen Models erben von diesem Basis-Model.
"""

from pydantic import BaseModel, Field
from typing import Optional, ClassVar
from datetime import date, time
from abc import ABC


class BaseExportModel(BaseModel, ABC):
    """
    Basis-Model für alle REDCap Export-Instrumente.
    
    Enthält die gemeinsamen Felder, die in jedem REDCap-Datensatz 
    vorkommen: record_id, redcap_event_name, redcap_repeat_instrument, etc.
    """
    
    # REDCap Pflichtfelder
    record_id: str = Field(..., description="REDCap Record ID")
    redcap_event_name: Optional[str] = Field(None, description="REDCap Event Name (z.B. 'ecls_arm_2')")
    redcap_repeat_instrument: Optional[str] = Field(None, description="Name des Instruments")
    redcap_repeat_instance: Optional[int] = Field(None, description="Instanz-Nummer (für repeating instruments)")
    
    # Klassenattribute für Instrument-Metadaten (von Subklassen überschrieben)
    INSTRUMENT_NAME: ClassVar[str] = ""  # z.B. "labor", "echocardiography"
    INSTRUMENT_LABEL: ClassVar[str] = ""  # z.B. "Labor", "Echokardiographie"
    
    class Config:
        populate_by_name = True
        from_attributes = True
        use_enum_values = True
    
    def get_instrument_name(self) -> str:
        """Gibt den REDCap Instrument-Namen zurück."""
        return self.redcap_repeat_instrument or self.INSTRUMENT_NAME
    
    def is_complete(self) -> bool:
        """
        Prüft ob das Formular als "complete" markiert werden kann.
        Überschreiben in Subklassen für spezifische Logik.
        """
        return True
    
    def to_redcap_dict(self) -> dict:
        """
        Konvertiert das Model zu einem REDCap-kompatiblen Dictionary.
        
        - None-Werte werden zu leeren Strings
        - Datumsfelder werden formatiert (YYYY-MM-DD)
        - Zeitfelder werden formatiert (HH:MM)
        - Boolean/Int-Felder für Checkboxen bleiben 0/1
        """
        result = {}
        
        for field_name, value in self.model_dump().items():
            if value is None:
                result[field_name] = ""
            elif isinstance(value, date):
                result[field_name] = value.strftime("%Y-%m-%d")
            elif isinstance(value, time):
                result[field_name] = value.strftime("%H:%M")
            elif isinstance(value, bool):
                result[field_name] = 1 if value else 0
            else:
                result[field_name] = value
        
        return result


class TimedExportModel(BaseExportModel):
    """
    Erweitertes Basis-Model für zeitbasierte Instrumente.
    
    Für Instrumente die täglich/regelmäßig erfasst werden:
    - Labor
    - Hämodynamik/Beatmung
    - Komplikationen
    
    WICHTIG: Die generischen Felder (assess_date, assess_time, assess_time_point)
    werden beim Export AUSGESCHLOSSEN, da jedes Instrument eigene spezifische
    Zeitfelder hat (z.B. assess_date_labor, assess_date_hemo).
    """
    
    # Generische Zeitfelder (nur intern, werden beim Export ausgeschlossen)
    assess_date: Optional[date] = Field(None, description="Datum der Erhebung", exclude=True)
    assess_time: Optional[time] = Field(None, description="Uhrzeit der Erhebung", exclude=True)
    assess_time_point: Optional[int] = Field(None, description="Tag seit Implantation", exclude=True)
    
    def get_day_number(self) -> Optional[int]:
        """Gibt die Tagesnummer zurück (entspricht meist redcap_repeat_instance)."""
        return self.assess_time_point or self.redcap_repeat_instance
