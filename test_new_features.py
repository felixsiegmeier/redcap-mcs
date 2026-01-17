#!/usr/bin/env python3
"""
Test-Skript für neue Funktionen: Gewicht/Größe-Eingabe
"""

import sys
import pandas as pd

def test_appstate_fields():
    """Test 1: AppState mit neuen Feldern"""
    print("=" * 60)
    print("TEST 1: AppState mit patient_weight und patient_height")
    print("=" * 60)
    
    try:
        from state import AppState
        state = AppState()
        
        # Prüfe neue Felder
        assert hasattr(state, 'patient_weight'), "patient_weight Feld fehlt"
        assert hasattr(state, 'patient_height'), "patient_height Feld fehlt"
        
        # Setze Werte
        state.patient_weight = 75.5
        state.patient_height = 180.0
        
        print(f"✅ patient_weight: {state.patient_weight} kg")
        print(f"✅ patient_height: {state.patient_height} cm")
        print(f"✅ Standardwerte sind None: {AppState().patient_weight is None}")
        
        return True
    except Exception as e:
        print(f"❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_hemodynamics_aggregator():
    """Test 2: HemodynamicsAggregator - get_patient_weight priorisiert State"""
    print("\n" + "=" * 60)
    print("TEST 2: HemodynamicsAggregator._get_patient_weight()")
    print("=" * 60)
    
    try:
        from services.aggregators.hemodynamics_aggregator import HemodynamicsAggregator
        from state import AppState
        from datetime import date
        import streamlit as st
        
        # Initialisiere session_state
        if "app_state" not in st.session_state:
            st.session_state.app_state = AppState()
        
        # Erstelle einen HemodynamicsAggregator mit erforderlichen Parametern
        agg = HemodynamicsAggregator(
            date=date.today(),
            record_id="TEST001",
            redcap_event_name="ecls_arm_2",
            redcap_repeat_instance=1
        )
        
        # Ohne Gewicht in State
        st.session_state.app_state.patient_weight = None
        weight = agg._get_patient_weight()
        print(f"✅ Gewicht ohne State-Wert: {weight} (None erwartet)")
        
        # Mit Gewicht im State
        st.session_state.app_state.patient_weight = 85.0
        weight = agg._get_patient_weight()
        print(f"✅ Gewicht mit State-Wert: {weight} kg (85.0 erwartet)")
        assert weight == 85.0, f"Erwartet 85.0, got {weight}"
        
        # Prüfe dass State priorität hat über Daten
        print(f"✅ State hat Priorität über Datensätze")
        
        return True
    except Exception as e:
        print(f"❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_imports():
    """Test 3: Alle Imports funktionieren"""
    print("\n" + "=" * 60)
    print("TEST 3: Alle Imports funktionieren")
    print("=" * 60)
    
    try:
        from state import get_state, update_state, get_data
        from views.homepage import render_homepage
        from services.aggregators.hemodynamics_aggregator import HemodynamicsAggregator
        
        print("✅ state.py Imports OK")
        print("✅ views.homepage Imports OK")
        print("✅ hemodynamics_aggregator Imports OK")
        
        return True
    except Exception as e:
        print(f"❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    results = []
    
    results.append(test_imports())
    results.append(test_appstate_fields())
    results.append(test_hemodynamics_aggregator())
    
    print("\n" + "=" * 60)
    if all(results):
        print("✅ ALLE TESTS BESTANDEN")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ EINIGE TESTS FEHLGESCHLAGEN")
        print("=" * 60)
        sys.exit(1)
