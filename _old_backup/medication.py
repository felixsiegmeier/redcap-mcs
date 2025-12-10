from pydantic import BaseModel, Field
from typing import Optional


class MedicationModel(BaseModel):
    # REDCap Meta
    record_id: str = Field(..., alias="record_id")
    redcap_event_name: str = Field(..., alias="redcap_event_name")
    redcap_repeat_instrument: Optional[str] = Field(None, alias="redcap_repeat_instrument")
    redcap_repeat_instance: Optional[int] = Field(None, alias="redcap_repeat_instance")

    # Antikoagulation/Antiplättchen
    iv_ac: Optional[bool] = Field(None, alias="iv_ac")
    iv_ac_spec: Optional[str] = Field(None, alias="iv_ac_spec")
    post_antiplat: Optional[bool] = Field(None, alias="post_antiplat")
    post_antiplat_spec___1: Optional[bool] = Field(None, alias="post_antiplat_spec___1")
    post_antiplat_spec___2: Optional[bool] = Field(None, alias="post_antiplat_spec___2")
    post_antiplat_spec___3: Optional[bool] = Field(None, alias="post_antiplat_spec___3")
    post_antiplat_spec___4: Optional[bool] = Field(None, alias="post_antiplat_spec___4")
    post_antiplat_spec___5: Optional[bool] = Field(None, alias="post_antiplat_spec___5")
    post_antiplat_o: Optional[str] = Field(None, alias="post_antiplat_o")

    # Antiinfektiva
    antibiotic: Optional[bool] = Field(None, alias="antibiotic")
    antibiotic_spec___1: Optional[bool] = Field(None, alias="antibiotic_spec___1")
    antibiotic_spec___2: Optional[bool] = Field(None, alias="antibiotic_spec___2")
    antibiotic_spec___3: Optional[bool] = Field(None, alias="antibiotic_spec___3")
    antibiotic_spec___4: Optional[bool] = Field(None, alias="antibiotic_spec___4")
    antibiotic_spec___5: Optional[bool] = Field(None, alias="antibiotic_spec___5")
    antibiotic_spec___6: Optional[bool] = Field(None, alias="antibiotic_spec___6")
    antibiotic_spec___7: Optional[bool] = Field(None, alias="antibiotic_spec___7")
    antibiotic_spec___8: Optional[bool] = Field(None, alias="antibiotic_spec___8")
    antibiotic_spec___9: Optional[bool] = Field(None, alias="antibiotic_spec___9")
    antibiotic_spec___10: Optional[bool] = Field(None, alias="antibiotic_spec___10")
    antibiotic_spec___11: Optional[bool] = Field(None, alias="antibiotic_spec___11")
    antibiotic_spec___12: Optional[bool] = Field(None, alias="antibiotic_spec___12")
    antibiotic_spec___13: Optional[bool] = Field(None, alias="antibiotic_spec___13")
    antibiotic_spec___14: Optional[bool] = Field(None, alias="antibiotic_spec___14")
    antibiotic_spec___15: Optional[bool] = Field(None, alias="antibiotic_spec___15")
    antibiotic_spec___16: Optional[bool] = Field(None, alias="antibiotic_spec___16")
    antibiotic_spec___17: Optional[bool] = Field(None, alias="antibiotic_spec___17")
    antibiotic_spec___18: Optional[bool] = Field(None, alias="antibiotic_spec___18")
    antibiotic_spec___19: Optional[bool] = Field(None, alias="antibiotic_spec___19")
    antibiotic_spec___20: Optional[bool] = Field(None, alias="antibiotic_spec___20")
    antibiotic_spec_o: Optional[str] = Field(None, alias="antibiotic_spec_o")
    antiviral: Optional[bool] = Field(None, alias="antiviral")
    antiviral_spec: Optional[str] = Field(None, alias="antiviral_spec")

    # Ernährung
    nutrition: Optional[bool] = Field(None, alias="nutrition")
    nutrition_spec___1: Optional[bool] = Field(None, alias="nutrition_spec___1")
    nutrition_spec___2: Optional[bool] = Field(None, alias="nutrition_spec___2")

    # Transfusion/Koagulation
    transfusion_coag: Optional[bool] = Field(None, alias="transfusion_coag")
    thromb_t: Optional[float] = Field(None, alias="thromb_t")
    ery_t: Optional[float] = Field(None, alias="ery_t")
    ffp_t: Optional[float] = Field(None, alias="ffp_t")
    ppsb_t: Optional[float] = Field(None, alias="ppsb_t")
    fib_t: Optional[float] = Field(None, alias="fib_t")
    at3_t: Optional[float] = Field(None, alias="at3_t")
    fxiii_t: Optional[float] = Field(None, alias="fxiii_t")

    # Organunterstützung (sonstige)
    organ_support___1: Optional[bool] = Field(None, alias="organ_support___1")
    organ_support___2: Optional[bool] = Field(None, alias="organ_support___2")
    organ_support___3: Optional[bool] = Field(None, alias="organ_support___3")
    organ_support___4: Optional[bool] = Field(None, alias="organ_support___4")
    organ_support___5: Optional[bool] = Field(None, alias="organ_support___5")
    organ_support___6: Optional[bool] = Field(None, alias="organ_support___6")
    organ_support___7: Optional[bool] = Field(None, alias="organ_support___7")
    organ_support___8: Optional[bool] = Field(None, alias="organ_support___8")
    organ_support___9: Optional[bool] = Field(None, alias="organ_support___9")
    organ_support___10: Optional[bool] = Field(None, alias="organ_support___10")

    # Diverse Medikamente Sammelkategorie
    medication___1: Optional[bool] = Field(None, alias="medication___1")
    medication___2: Optional[bool] = Field(None, alias="medication___2")
    medication___3: Optional[bool] = Field(None, alias="medication___3")
    medication___4: Optional[bool] = Field(None, alias="medication___4")
    medication___5: Optional[bool] = Field(None, alias="medication___5")
    medication___6: Optional[bool] = Field(None, alias="medication___6")
    medication___7: Optional[bool] = Field(None, alias="medication___7")
    medication___8: Optional[bool] = Field(None, alias="medication___8")
    medication___9: Optional[bool] = Field(None, alias="medication___9")
    medication___10: Optional[bool] = Field(None, alias="medication___10")
    medication___11: Optional[bool] = Field(None, alias="medication___11")

    # Narkotika-Spezifika
    narcotics_spec___1: Optional[bool] = Field(None, alias="narcotics_spec___1")
    narcotics_spec___2: Optional[bool] = Field(None, alias="narcotics_spec___2")
    narcotics_spec___3: Optional[bool] = Field(None, alias="narcotics_spec___3")
    narcotics_spec___4: Optional[bool] = Field(None, alias="narcotics_spec___4")

    class Config:
        from_attributes = True
        populate_by_name = True
