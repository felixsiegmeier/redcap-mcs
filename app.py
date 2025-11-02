from state_provider.state_provider_class import state_provider
from views.sidebar import render_sidebar
from views.startpage import render_startpage
from views.homepage import render_homepage
from views.vitals_data import render_vitals_data
from views.lab_data import render_lab_data
from views.lab_form import  lab_form
from views.export_builder import export_builder
from schemas.app_state_schemas.app_state import Views
from datetime import datetime
import streamlit as st

def run_app():

    if state_provider.get_selected_view() == Views.STARTPAGE:
        render_startpage()
        with st.sidebar:
            st.header("Please upload a file")

    elif state_provider.get_selected_view() == Views.EXPORT_BUILDER:
        # Synchronize session_state for sidebar date picker with state_provider
        time_range = state_provider.get_selected_time_range()
        if isinstance(time_range, tuple) and len(time_range) == 2 and all(isinstance(d, datetime) for d in time_range):
            st.session_state["date_range_input"] = (time_range[0].date(), time_range[1].date())
        export_builder()
        render_sidebar()

    else:
        # Synchronize session_state for sidebar date picker with state_provider
        time_range = state_provider.get_selected_time_range()
        if isinstance(time_range, tuple) and len(time_range) == 2 and all(isinstance(d, datetime) for d in time_range):
            st.session_state["date_range_input"] = (time_range[0].date(), time_range[1].date())
        render_sidebar()

        if state_provider.get_selected_view() == Views.HOMEPAGE:
            render_homepage()

        elif state_provider.get_selected_view() == Views.VITALS:
            render_vitals_data()

        elif state_provider.get_selected_view() == Views.LAB:
            render_lab_data()

        elif state_provider.get_selected_view() == Views.LAB_FORM:
            lab_form()

if __name__ == "__main__":
    run_app()
    