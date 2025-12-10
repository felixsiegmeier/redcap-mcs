# state_model.py
from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime, time
from enum import Enum
import pandas as pd

from schemas.db_schemas.lab import LabModel
from schemas.db_schemas.vitals import VitalsModel

class Views(Enum):
    HOMEPAGE = "homepage"
    STARTPAGE = "startpage"
    VITALS = "vitals"
    LAB = "lab"
    IMPELLA = "impella"
    ECMO = "ecmo"
    RESPIRATORY = "respiratory"
    LAB_FORM = "lab_form"
    VITALS_FORM = "vitals_form"
    EXPORT_BUILDER = "export_builder"

class UiState(BaseModel):
    selected_categories : list[str] = []
    selected_parameters : list[str] = []
    show_median : bool = False

class AppState(BaseModel):
    # Allow arbitrary types in nested models (safe to include here as well)
    model_config = {"arbitrary_types_allowed": True}
    last_updated: Optional[datetime] = None
    record_id: Optional[str] = None
    data: Optional[pd.DataFrame] = None
    selected_view: Views = Views.STARTPAGE
    time_range: Optional[tuple[datetime, datetime]] = None
    selected_time_range: Optional[tuple[datetime, datetime]] = time_range
    value_strategy: str = "nearest"
    nearest_ecls_time: Optional[time] = None
    nearest_impella_time: Optional[time] = None
    vitals_ui: UiState = UiState()
    lab_ui: UiState = UiState()
    impella_ui: UiState = UiState()
    ecmo_ui: UiState = UiState()
    respiratory_ui: UiState = UiState()
    lab_form: list[LabModel] | None = []
    vitals_form: list[VitalsModel] | None = []
