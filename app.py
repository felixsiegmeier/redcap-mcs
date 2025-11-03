from state_provider.state_provider_class import state_provider
from views.sidebar import Sidebar
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

    if state_provider.get_selected_view() == Views.LAB_FORM:
        st.set_page_config(layout="wide")

    if not state_provider.get_selected_view() == Views.STARTPAGE:
        Sidebar().render_sidebar()

    if state_provider.get_selected_view() == Views.STARTPAGE:
        render_startpage()
        with st.sidebar:
            st.header("Please upload a file")

    elif state_provider.get_selected_view() == Views.HOMEPAGE:
        render_homepage()

    elif state_provider.get_selected_view() == Views.VITALS:
        render_vitals_data()

    elif state_provider.get_selected_view() == Views.LAB:
        render_lab_data()

    elif state_provider.get_selected_view() == Views.LAB_FORM:
        lab_form()

    elif state_provider.get_selected_view() == Views.EXPORT_BUILDER:
        export_builder()

if __name__ == "__main__":
    run_app()
    