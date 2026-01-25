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


class VentilationSpec(IntEnum):
    """Beatmungsmodus-Spezifikation"""
    IPPV = 1
    BIPAP = 2
    SIMV = 3
    ASB = 4
    PC_BIPAP = 5
    PC_PSV = 6
    PC_CMV = 7
    PC_SIMV = 8
    PC_PC_APRV = 9
    PC_AC = 10
    VC_CMV = 11
    VC_SIMV = 12
    VC_MMV = 13
    VC_AC = 14
    SPN_CPAP_PS = 15
    BiLevel = 16
    A_C_VC = 17
    A_C_PC = 18
    A_C_PRVC = 19
    SIMV_VC = 20
    SIMV_PC = 21
    BiLevel_VG = 22
    CPAP_PS = 23
    SBT = 24
    NIV = 25


class RenalReplacement(IntEnum):
    """Nierenersatztherapie"""
    HEMODIALYSIS = 1
    CONTINUOUS_HEMOFILTRATION = 2
    NONE = 3


class FluidBalance(IntEnum):
    """Flüssigkeitsbilanz-Kategorie"""
    POSITIVE = 1
    NEGATIVE = 2

class Anticoagulation(IntEnum):
    """Anticoagulation"""
    HEPARIN = 1
    ARGATROBAN = 2

class Nutrition(IntEnum):
    """Ernährung"""
    ENTERAL = 1
    PARENTERAL = 2


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
    spo2: Optional[float] = Field(None, alias="spo2")  # SpO2
    
    # Pulmonalarterie (PAC)
    pac: Optional[int] = Field(None, alias="pac")  # PAC vorhanden?
    pcwp: Optional[float] = Field(None, alias="pcwp")  # Wedge-Druck
    sys_pap: Optional[float] = Field(None, alias="sys_pap")  # Syst. PA-Druck
    dia_pap: Optional[float] = Field(None, alias="dia_pap")  # Diast. PA-Druck
    mean_pap: Optional[float] = Field(None, alias="mean_pap")  # Mittlerer PA-Druck
    ci: Optional[float] = Field(None, alias="ci")  # Cardiac Index
    
    # ==================== Katecholamine ====================
    vasoactive_med: Optional[int] = Field(None, alias="vasoactive_med")  # Katecholamine ja/nein
    
    # Vasoactive Infusion Checkboxes (17 Medikamente)
    vasoactive_spec___1: Optional[int] = Field(0, alias="vasoactive_spec___1")  # Dobutamine
    vasoactive_spec___2: Optional[int] = Field(0, alias="vasoactive_spec___2")  # Dopamine
    vasoactive_spec___3: Optional[int] = Field(0, alias="vasoactive_spec___3")  # Enoximone
    vasoactive_spec___4: Optional[int] = Field(0, alias="vasoactive_spec___4")  # Epinephrine
    vasoactive_spec___5: Optional[int] = Field(0, alias="vasoactive_spec___5")  # Esmolol
    vasoactive_spec___6: Optional[int] = Field(0, alias="vasoactive_spec___6")  # Levosimendan
    vasoactive_spec___7: Optional[int] = Field(0, alias="vasoactive_spec___7")  # Metaraminol
    vasoactive_spec___8: Optional[int] = Field(0, alias="vasoactive_spec___8")  # Metoprolol
    vasoactive_spec___9: Optional[int] = Field(0, alias="vasoactive_spec___9")  # Milrinone
    vasoactive_spec___10: Optional[int] = Field(0, alias="vasoactive_spec___10")  # Nicardipine
    vasoactive_spec___11: Optional[int] = Field(0, alias="vasoactive_spec___11")  # Nitroglycerin
    vasoactive_spec___12: Optional[int] = Field(0, alias="vasoactive_spec___12")  # Nitroprusside
    vasoactive_spec___13: Optional[int] = Field(0, alias="vasoactive_spec___13")  # Norepinephrine
    vasoactive_spec___14: Optional[int] = Field(0, alias="vasoactive_spec___14")  # Phenylephrine
    vasoactive_spec___15: Optional[int] = Field(0, alias="vasoactive_spec___15")  # Tolazoline
    vasoactive_spec___16: Optional[int] = Field(0, alias="vasoactive_spec___16")  # Vasopressin
    vasoactive_spec___17: Optional[int] = Field(0, alias="vasoactive_spec___17")  # Other
    
    vasoactive_o: Optional[str] = Field(None, alias="vasoactive_o")  # Andere Katecholamine
    dobutamine: Optional[float] = Field(None, alias="dobutamine")  # µg/kg/min
    epinephrine: Optional[float] = Field(None, alias="epinephrine")  # µg/kg/min
    norepinephrine: Optional[float] = Field(None, alias="norepinephrine")  # µg/kg/min
    vasopressin: Optional[float] = Field(None, alias="vasopressin")  # IU/h
    milrinone: Optional[float] = Field(None, alias="milrinone")  # µg/kg/min
    
    # ==================== Beatmung ====================
    vent: Optional[VentilationMode] = Field(None, alias="vent")
    o2: Optional[float] = Field(None, alias="o2")  # O2-Flow L/min
    fio2: Optional[float] = Field(None, alias="fio2")  # FiO2 %
    vent_spec: Optional[VentilationSpec] = Field(None, alias="vent_spec")
    vent_type: Optional[VentilationType] = Field(None, alias="vent_type")
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

    # ==================== Antikoagulation ====================
    iv_ac: Optional[int] = Field(None, alias="iv_ac")
    iv_ac_spec: Optional[Anticoagulation] = Field(None, alias="iv_ac_spec")

    antiplat_th: Optional[int] = Field(None, alias="antiplat_th")
    antiplat_therapy_spec___1: Optional[int] = Field(0, alias="antiplat_therapy_spec___1")
    antiplat_therapy_spec___2: Optional[int] = Field(0, alias="antiplat_therapy_spec___2")
    antiplat_therapy_spec___3: Optional[int] = Field(0, alias="antiplat_therapy_spec___3")
    antiplat_therapy_spec___4: Optional[int] = Field(0, alias="antiplat_therapy_spec___4")
    antiplat_therapy_spec___5: Optional[int] = Field(0, alias="antiplat_therapy_spec___5")
    
    # ==================== Antibiotika ====================
    antibiotic: Optional[int] = Field(None, alias="antibiotic")
    antibiotic_spec___1: Optional[int] = Field(0, alias="antibiotic_spec___1")
    antibiotic_spec___2: Optional[int] = Field(0, alias="antibiotic_spec___2")
    antibiotic_spec___3: Optional[int] = Field(0, alias="antibiotic_spec___3")
    antibiotic_spec___4: Optional[int] = Field(0, alias="antibiotic_spec___4")
    antibiotic_spec___5: Optional[int] = Field(0, alias="antibiotic_spec___5")
    antibiotic_spec___6: Optional[int] = Field(0, alias="antibiotic_spec___6")
    antibiotic_spec___7: Optional[int] = Field(0, alias="antibiotic_spec___7")
    antibiotic_spec___8: Optional[int] = Field(0, alias="antibiotic_spec___8")
    antibiotic_spec___9: Optional[int] = Field(0, alias="antibiotic_spec___9")
    antibiotic_spec___10: Optional[int] = Field(0, alias="antibiotic_spec___10")
    antibiotic_spec___11: Optional[int] = Field(0, alias="antibiotic_spec___11")
    antibiotic_spec___12: Optional[int] = Field(0, alias="antibiotic_spec___12")
    antibiotic_spec___13: Optional[int] = Field(0, alias="antibiotic_spec___13")
    antibiotic_spec___14: Optional[int] = Field(0, alias="antibiotic_spec___14") # Other
    antibiotic_spec___15: Optional[int] = Field(0, alias="antibiotic_spec___15")
    antibiotic_spec___16: Optional[int] = Field(0, alias="antibiotic_spec___16")
    antibiotic_spec___17: Optional[int] = Field(0, alias="antibiotic_spec___17")
    antibiotic_spec___18: Optional[int] = Field(0, alias="antibiotic_spec___18")
    antibiotic_spec___19: Optional[int] = Field(0, alias="antibiotic_spec___19")
    antibiotic_spec___20: Optional[int] = Field(0, alias="antibiotic_spec___20")
    antibiotic_spec_o: Optional[str] = Field(None, alias="antibiotic_spec_o")

    # ==================== Ernährung ====================
    nutrition: Optional[int] = Field(None, alias="nutrition")
    nutrition_spec: Optional[Nutrition] = Field(None, alias="nutrition_spec")

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
    renal_repl: Optional[RenalReplacement] = Field(None, alias="renal_repl")
    urine: Optional[float] = Field(None, alias="urine")  # Urinausscheidung
    output_renal_repl: Optional[float] = Field(None, alias="output_renal_repl")  # CRRT Output ml
    
    # ==================== Bilanz ====================
    fluid_balance: Optional[FluidBalance] = Field(None, alias="fluid_balance")
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

        # Antikoagulation vorhanden
        self.iv_ac = 1 if self.iv_ac_spec else 0

        # Antiplatelet-Therapie vorhanden
        antiplatelets = [
            self.antiplat_therapy_spec___1,
            self.antiplat_therapy_spec___2,
            self.antiplat_therapy_spec___3,
            self.antiplat_therapy_spec___4,
            self.antiplat_therapy_spec___5
        ]
        self.antiplat_th = 1 if any(v == 1 for v in antiplatelets) else 0

        # Antibiotika vorhanden
        antibiotics = [
            getattr(self, f"antibiotic_spec___{i}") for i in range(1, 21)
        ]
        self.antibiotic = 1 if any(v == 1 for v in antibiotics) else 0
        
        # Beatmung vorhanden - REDCap-konforme Werte
        if self.vent_peep is not None and self.conv_vent_rate is not None:
            self.vent = VentilationMode.INVASIVE
            self.vent_type = VentilationType.CONVENTIONAL
        elif self.vent_peep is not None and self.conv_vent_rate is None:
            self.vent = VentilationMode.NON_INVASIVE
            self.vent_type = VentilationType.CONVENTIONAL
        elif self.vent_peep is None and self.conv_vent_rate is None and self.fio2 is not None:
            self.vent = VentilationMode.HIGH_FLOW
        else:
            self.vent = VentilationMode.NO_VENTILATION
        
        # GCS vorhanden
        self.gcs_avail = 1 if self.gcs is not None else 0

        # Ernährung
        self.nutrition = 1 if self.nutrition_spec else 0
        
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
