import streamlit as st
from datetime import date, datetime

from schemas.app_state_schemas.app_state import Views
from services.utils import coerce_to_datetime, normalize_date_range
from state_provider.state_provider import state_provider

class Sidebar:

    def _update_record_id(self):
        new_id = st.session_state["record_id_input"]
        st.session_state["export_record_id_input"] = new_id
        state_provider.update_state(record_id=new_id)

    def _sync_sidebar_date_range(self):
        raw_value = st.session_state.get("date_range_input")
        if isinstance(raw_value, (date, datetime)):
            values = (raw_value, raw_value)
        elif isinstance(raw_value, (list, tuple)) and len(raw_value) == 2:
            values = tuple(raw_value)
        else:
            return

        start_dt = coerce_to_datetime(values[0])
        end_dt = coerce_to_datetime(values[1])
        if not start_dt or not end_dt:
            return

        normalized = (start_dt.date(), end_dt.date())
        st.session_state["date_range_input"] = normalized
        st.session_state["export_date_range_input"] = normalized
        state_provider.set_selected_time_range(start_dt, end_dt)

    def _render_record_id_input(self):
        st.text_input("Record ID", key="record_id_input", on_change=self._update_record_id, help="Enter the RedCap record ID for CSV export")

    def _render_time_range_picker(self):
        default_range = (date.today(), date.today())
        selected_range = state_provider.get_selected_time_range()
        initial_range = normalize_date_range(selected_range, default_range)
        current_value = normalize_date_range(
            st.session_state.get("date_range_input"),
            initial_range,
        )

        st.session_state.setdefault("date_range_input", current_value)
        st.session_state.setdefault("export_date_range_input", current_value)

        st.date_input(
            "Select a date range",
            key="date_range_input",
            on_change=self._sync_sidebar_date_range,
            help="Select the date range for exploration, visualization and export via RedCap CSV-File.",
        )

    def _render_navigation_buttons(self):
        state = state_provider.get_state()
        if state.parsed_data:
            def go_to_homepage():
                state_provider.update_state(selected_view=Views.HOMEPAGE)
            st.button("Overview", on_click=go_to_homepage, width="stretch")
            self._render_explore_expander()
            self._render_forms_expander()

    def _render_explore_expander(self):
        def go_to_vitals():
            state_provider.update_state(selected_view=Views.VITALS)

        def go_to_lab():
            state_provider.update_state(selected_view=Views.LAB)

        def go_to_respiratory():
            state_provider.update_state(selected_view=Views.RESPIRATORY)

        def go_to_impella():
            state_provider.update_state(selected_view=Views.IMPELLA)

        def go_to_ecmo():
            state_provider.update_state(selected_view=Views.ECMO)

        with st.expander(label="Explore Data"):
            st.button("Vitals", key="vitals_button", on_click=go_to_vitals, width="stretch")
            st.button("Respiratory", key="respiratory_button", on_click=go_to_respiratory, width="stretch")
            st.button("Lab", key="lab_button", on_click=go_to_lab, width="stretch")
            if not state_provider.query_data("impella").empty:
                st.button("Impella", key="impella_button", on_click=go_to_impella, width="stretch")
            if not state_provider.query_data("ecmo").empty:
                st.button("ECMO", key="ecmo_button", on_click=go_to_ecmo, width="stretch")

    def _render_forms_expander(self):
        def go_to_export_builder():
            state_provider.update_state(selected_view=Views.EXPORT_BUILDER)

        def go_to_lab_form():
            state_provider.update_state(selected_view=Views.LAB_FORM)

        with st.expander(label="Forms"):
            st.button("Export Builder", key="export_builder_button", on_click=go_to_export_builder, width="stretch")
            st.button("Lab Form", key="lab_form_button", on_click=go_to_lab_form, width="stretch")

    def render_sidebar(self):
        sidebar = st.sidebar
        with sidebar:
            st.header("Navigation")
            self._render_record_id_input()
            self._render_time_range_picker()
            self._render_navigation_buttons()