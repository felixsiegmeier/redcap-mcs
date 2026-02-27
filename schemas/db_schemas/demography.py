from .base import BaseExportModel
from typing import ClassVar, Optional
from pydantic import Field
from datetime import date

class DemographyModel(BaseExportModel):
    """
    Demographische Daten
    """
    # Instrument-Metadaten
    INSTRUMENT_NAME: ClassVar[str] = "demography"

    birthdate: Optional[date] = Field(default=None, description="Birthdate of the participant")
    weight: Optional[float] = Field(default=None, description="Weight of the participant")
    height: Optional[float] = Field(default=None, description="Height of the participant")
