import pytest
from schemas.db_schemas.hemodynamics import HemodynamicsModel
from schemas.db_schemas.lab import LabModel

def test_hemodynamics_derived_fields_manual_update():
    # Initialisiere Model mit minimalen Daten
    model = HemodynamicsModel(
        record_id="test_1",
        redcap_event_name="event_1",
        assess_date_hemo="2026-01-26"
    )
    
    # Vorher: transfusion_coag sollte None oder 0 sein
    assert model.transfusion_coag is None or model.transfusion_coag == 0
    
    # Setze ein Feld, das transfusion_coag beeinflusst
    model.thromb_t = 2
    
    # Pydantic validiert nicht automatisch bei Attribut-Zuweisung
    # transfusion_coag sollte immer noch None/0 sein, wenn nicht manuell getriggert
    assert model.transfusion_coag is None or model.transfusion_coag == 0
    
    # Manuelles Triggering der abgeleiteten Felder
    model.set_derived_fields()
    
    # Nachher: transfusion_coag muss jetzt 1 sein
    assert model.transfusion_coag == 1
    
    # Teste Katecholamine -> vasoactive_med
    model.norepinephrine = 0.1
    model.set_derived_fields()
    assert model.vasoactive_med == 1
    
    # Teste Antiplatelets
    model.antiplat_therapy_spec___1 = 1
    model.set_derived_fields()
    assert model.antiplat_th == 1

def test_lab_derived_fields_manual_update():
    model = LabModel(
        record_id="test_1",
        redcap_event_name="event_1",
        assess_date_labor="2026-01-26"
    )
    
    # Vorher
    assert model.post_pct == 0
    
    # Setze Wert
    model.pct = 0.5
    
    # Trigger
    model.set_derived_fields()
    
    # Nachher
    assert model.post_pct == 1
    
    # Teste Albumin Umrechnung (g/L -> g/dL)
    model.albumin = 35.0
    model.set_derived_fields()
    assert model.albumin == 3.5
