"""
REDCap Hemodynamics/Ventilation/Medication Instrument Model.

Erfasst täglich: Hämodynamik, Beatmung, Medikation, NIRS, etc.
"""

from pydantic import Field, model_validator, PrivateAttr
from typing import Optional, ClassVar, Self
from datetime import date
from enum import IntEnum

from .base import TimedExportModel


class VentilationMode(IntEnum):
    """Beatmungsmodus"""
    NON_INVASIVE = 1
    NO_VENTILATION = 2
    INVASIVE = 5
    HIGH_FLOW = 6


class VentilationType(IntEnum):
    """Beatmungstyp"""
    CONVENTIONAL = 1
    HIGH_FREQUENCY = 2


class RenalReplacement(IntEnum):
    """Nierenersatztherapie"""
    NONE = 0
    CVVH = 1
    CVVHD = 2
    CVVHDF = 3
    IHD = 4


class FluidBalance(IntEnum):
    """Flüssigkeitsbilanz-Kategorie"""
    NEGATIVE = 0
    NEUTRAL = 1
    POSITIVE = 2


class HemodynamicsModel(TimedExportModel):
    """
    REDCap hemodynamics_ventilation_medication Instrument.
    
    Dieses Instrument existiert in BEIDEN Arms:
    - ecls_arm_2
    - impella_arm_2
    
    Die Unterscheidung erfolgt über redcap_event_name!
    """
    
    # Instrument-Metadaten
    INSTRUMENT_NAME: ClassVar[str] = "hemodynamics_ventilation_medication"
    INSTRUMENT_LABEL: ClassVar[str] = "Hämodynamik / Beatmung / Medikation"
    
    # REDCap-Felder mit korrektem Default
    redcap_repeat_instrument: Optional[str] = Field(
        "hemodynamics_ventilation_medication", 
        alias="redcap_repeat_instrument"
    )
    
    # Kontrollfelder
    na_post: Optional[int] = Field(1, alias="na_post")
    ecmella: Optional[int] = Field(0, alias="ecmella")
    
    # Zeitpunkt
    assess_time_point: Optional[int] = Field(None, alias="assess_time_point")
    assess_date_hemo: Optional[date] = Field(None, alias="assess_date_hemo")
    
    # ==================== NIRS ====================
    nirs_avail: Optional[int] = Field(None, alias="nirs_avail")  # 0=no, 1=yes
    # nirs_loc ist checkbox - hier nicht modelliert
    nirs_left_c: Optional[float] = Field(None, alias="nirs_left_c")  # Cerebral links
    nirs_right_c: Optional[float] = Field(None, alias="nirs_right_c")  # Cerebral rechts
    nirs_left_f: Optional[float] = Field(None, alias="nirs_left_f")  # Femoral links
    nirs_right_f: Optional[float] = Field(None, alias="nirs_right_f")  # Femoral rechts
    nirs_change: Optional[int] = Field(None, alias="nirs_change")
    nirs_change_spec: Optional[str] = Field(None, alias="nirs_change_spec")
    
    # ==================== Hämodynamik ====================
    hr: Optional[float] = Field(None, alias="hr")  # Herzfrequenz
    sys_bp: Optional[float] = Field(None, alias="sys_bp")  # Systolischer BD
    dia_bp: Optional[float] = Field(None, alias="dia_bp")  # Diastolischer BD
    mean_bp: Optional[float] = Field(None, alias="mean_bp")  # Mittlerer BD
    cvp: Optional[float] = Field(None, alias="cvp")  # ZVD
    sp02: Optional[float] = Field(None, alias="sp02")  # SpO2
    
    # Pulmonalarterie (PAC)
    pac: Optional[int] = Field(None, alias="pac")  # PAC vorhanden?
    pcwp: Optional[float] = Field(None, alias="pcwp")  # Wedge-Druck
    sys_pap: Optional[float] = Field(None, alias="sys_pap")  # Syst. PA-Druck
    dia_pap: Optional[float] = Field(None, alias="dia_pap")  # Diast. PA-Druck
    mean_pap: Optional[float] = Field(None, alias="mean_pap")  # Mittlerer PA-Druck
    ci: Optional[float] = Field(None, alias="ci")  # Cardiac Index
    
    # ==================== Katecholamine ====================
    vasoactive_med: Optional[int] = Field(None, alias="vasoactive_med")  # Katecholamine ja/nein
    # vasoactive_spec ist checkbox - nicht modelliert
    vasoactive_o: Optional[str] = Field(None, alias="vasoactive_o")  # Andere Katecholamine
    dobutamine: Optional[float] = Field(None, alias="dobutamine")  # µg/kg/min
    epinephrine: Optional[float] = Field(None, alias="epinephrine")  # µg/kg/min
    norepinephrine: Optional[float] = Field(None, alias="norepinephrine")  # µg/kg/min
    vasopressin: Optional[float] = Field(None, alias="vasopressin")  # IU/h
    milrinone: Optional[float] = Field(None, alias="milrinone")  # µg/kg/min
    
    # ==================== Beatmung ====================
    vent: Optional[int] = Field(None, alias="vent")  # VentilationMode
    o2: Optional[float] = Field(None, alias="o2")  # O2-Flow L/min
    fi02: Optional[float] = Field(None, alias="fi02")  # FiO2 %
    # vent_spec ist dropdown - nicht modelliert
    vent_type: Optional[int] = Field(None, alias="vent_type")  # VentilationType
    hfv_rate: Optional[float] = Field(None, alias="hfv_rate")  # HF-Ventilation Rate
    conv_vent_rate: Optional[float] = Field(None, alias="conv_vent_rate")  # Konv. Vent Rate
    vent_map: Optional[float] = Field(None, alias="vent_map")  # MAP mbar
    vent_pip: Optional[float] = Field(None, alias="vent_pip")  # PIP mbar
    vent_peep: Optional[float] = Field(None, alias="vent_peep")  # PEEP mbar
    prone_pos: Optional[int] = Field(None, alias="prone_pos")  # Bauchlage ja/nein
    
    # ==================== Neurologie ====================
    gcs_avail: Optional[int] = Field(None, alias="gcs_avail")
    gcs: Optional[float] = Field(None, alias="gcs")  # Glasgow Coma Scale
    
    # RASS als Checkbox (10 Felder für RASS +4 bis -5)
    rass___1: Optional[int] = Field(0, alias="rass___1")  # Combative (+4)
    rass___2: Optional[int] = Field(0, alias="rass___2")  # Very agitated (+3)
    rass___3: Optional[int] = Field(0, alias="rass___3")  # Agitated (+2)
    rass___4: Optional[int] = Field(0, alias="rass___4")  # Restless (+1)
    rass___5: Optional[int] = Field(0, alias="rass___5")  # Alert and calm (0)
    rass___6: Optional[int] = Field(0, alias="rass___6")  # Drowsy (-1)
    rass___7: Optional[int] = Field(0, alias="rass___7")  # Light sedation (-2)
    rass___8: Optional[int] = Field(0, alias="rass___8")  # Moderate sedation (-3)
    rass___9: Optional[int] = Field(0, alias="rass___9")  # Deep sedation (-4)
    rass___10: Optional[int] = Field(0, alias="rass___10")  # Unarousable (-5)
    
    # Internes Feld für numerischen RASS-Wert (nicht exportiert)
    _rass_score: Optional[int] = PrivateAttr(default=None)
    
    # ==================== Transfusionen (24h) ====================
    transfusion_coag: Optional[int] = Field(None, alias="transfusion_coag")
    thromb_t: Optional[float] = Field(None, alias="thromb_t")  # Thrombozyten-Konzentrate
    ery_t: Optional[float] = Field(None, alias="ery_t")  # Erythrozyten-Konzentrate
    ffp_t: Optional[float] = Field(None, alias="ffp_t")  # Fresh Frozen Plasma
    ppsb_t: Optional[float] = Field(None, alias="ppsb_t")  # PPSB
    fib_t: Optional[float] = Field(None, alias="fib_t")  # Fibrinogen
    at3_t: Optional[float] = Field(None, alias="at3_t")  # Antithrombin III
    fxiii_t: Optional[float] = Field(None, alias="fxiii_t")  # Faktor XIII
    
    # ==================== Nierenfunktion ====================
    renal_repl: Optional[int] = Field(None, alias="renal_repl")  # RenalReplacement
    urine: Optional[float] = Field(None, alias="urine")  # Urinausscheidung
    output_renal_repl: Optional[float] = Field(None, alias="output_renal_repl")  # CRRT Output ml
    
    # ==================== Bilanz ====================
    fluid_balance: Optional[int] = Field(None, alias="fluid_balance")  # FluidBalance
    fluid_balance_numb: Optional[float] = Field(None, alias="fluid_balance_numb")  # Numerische Bilanz
    
    # Completion Status
    hemodynamics_ventilation_medication_complete: Optional[int] = Field(
        0, 
        alias="hemodynamics_ventilation_medication_complete"
    )
    
    @model_validator(mode="after")
    def set_derived_fields(self) -> Self:
        """Setzt abgeleitete Felder basierend auf vorhandenen Werten."""
        # PAK verfügbar
        pac_fields = [
            self.pcwp,
            self.sys_pap,
            self.dia_pap,
            self.mean_pap,
            self.ci
        ]
        self.pac = 1 if any(field is not None for field in pac_fields) else 0

        # NIRS verfügbar
        nirs_fields = [
            self.nirs_left_c,
            self.nirs_right_c,
            self.nirs_left_f,
            self.nirs_right_f
        ]
        self.nirs_avail = 1 if any(field is not None for field in nirs_fields) else 0
        
        # Katecholamine vorhanden
        catecholamines = [
            self.dobutamine,
            self.epinephrine,
            self.norepinephrine,
            self.milrinone,
            self.vasopressin
        ]
        self.vasoactive_med = 1 if any(v is not None and v > 0 for v in catecholamines) else 0
        
        # Beatmung vorhanden - REDCap-konforme Werte
        if self.vent_peep is not None and self.conv_vent_rate is not None:
            self.vent = 5  # Invasive Ventilation
            self.vent_type = VentilationType.CONVENTIONAL.value
        elif self.vent_peep is not None and self.conv_vent_rate is None:
            self.vent = 1  # Non invasive Ventilation
            self.vent_type = VentilationType.CONVENTIONAL.value
        elif self.vent_peep is None and self.conv_vent_rate is None and self.fi02 is not None:
            self.vent = 6  # High Flow Therapy
        else:
            self.vent = 2  # No Ventilation
        
        # GCS vorhanden
        self.gcs_avail = 1 if self.gcs is not None else 0
        
        return self
    
    def set_rass_score(self, score: int) -> None:
        """Setzt den RASS-Score und konvertiert zu Checkbox-Format.
        
        Args:
            score: Numerischer RASS-Score (-5 bis +4)
        """
        self._rass_score = score
        
        # Mapping: +4→1, +3→2, +2→3, +1→4, 0→5, -1→6, -2→7, -3→8, -4→9, -5→10
        checkbox_mapping = {
            4: 1, 3: 2, 2: 3, 1: 4, 0: 5,
            -1: 6, -2: 7, -3: 8, -4: 9, -5: 10
        }
        
        if score in checkbox_mapping:
            checkbox_num = checkbox_mapping[score]
            # Setze alle Checkboxen auf 0, dann die richtige auf 1
            for i in range(1, 11):
                setattr(self, f"rass___{i}", 0)
            setattr(self, f"rass___{checkbox_num}", 1)