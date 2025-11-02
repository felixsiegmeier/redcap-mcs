import streamlit as st
from schemas.app_state_schemas.app_state import Views
from state_provider.state_provider_class import state_provider
from datetime import date, datetime

def explore_expander():
    def go_to_vitals():
        state_provider.update_state(selected_view=Views.VITALS)

    def go_to_lab():
        state_provider.update_state(selected_view=Views.LAB)

    with st.expander(label="Explore Data"):
        st.button("Vitals", key="vitals_button", on_click=go_to_vitals, width="stretch")
        st.button("Lab", key="lab_button", on_click=go_to_lab, width="stretch")
        
def forms_expander():
    def go_to_export_builder():
        state_provider.update_state(selected_view=Views.EXPORT_BUILDER)

    def go_to_lab_form():
        state_provider.update_state(selected_view=Views.LAB_FORM)

    with st.expander(label="Forms"):
        st.button("Export Builder", key="export_builder_button", on_click=go_to_export_builder, width="stretch")
        st.button("Lab Form", key="lab_form_button", on_click=go_to_lab_form, width="stretch")

def render_sidebar():
    sidebar = st.sidebar
    def go_to_homepage():
        state_provider.update_state(selected_view=Views.HOMEPAGE)
    
    def update_record_id():
        new_id = st.session_state["record_id_input"]
        st.session_state["export_record_id_input"] = new_id
        state_provider.update_state(record_id=new_id)

    def _to_datetime(value):
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        return None

    def _dates_from_range(candidate, fallback):
        if isinstance(candidate, (list, tuple)) and len(candidate) == 2:
            start, end = candidate
            start_date = start.date() if isinstance(start, datetime) else start if isinstance(start, date) else None
            end_date = end.date() if isinstance(end, datetime) else end if isinstance(end, date) else None
            if start_date and end_date:
                return (start_date, end_date)
        return fallback

    def _on_sidebar_date_change():
        raw_value = st.session_state.get("date_range_input")
        if isinstance(raw_value, (date, datetime)):
            values = (raw_value, raw_value)
        elif isinstance(raw_value, (list, tuple)) and len(raw_value) == 2:
            values = tuple(raw_value)
        else:
            return

        start_dt = _to_datetime(values[0])
        end_dt = _to_datetime(values[1])
        if not start_dt or not end_dt:
            return

        normalized = (start_dt.date(), end_dt.date())
        st.session_state["date_range_input"] = normalized
        st.session_state["export_date_range_input"] = normalized
        state_provider.set_selected_time_range(start_dt, end_dt)

    state = state_provider.get_state()
    
    with sidebar:
        st.header("Navigation")

        st.text_input("Record ID", value=state_provider.get_record_id(), key="record_id_input", on_change=update_record_id, help="Enter the RedCap record ID for CSV export")

        default_range = (date.today(), date.today())
        selected_range = state_provider.get_selected_time_range()
        initial_range = _dates_from_range(selected_range, default_range)
        current_value = _dates_from_range(
            st.session_state.get("date_range_input"),
            initial_range,
        )

        st.session_state.setdefault("date_range_input", current_value)
        st.session_state.setdefault("export_date_range_input", current_value)

        st.date_input(
            "Select a date range",
            value=current_value,
            key="date_range_input",
            on_change=_on_sidebar_date_change,
            help="Select the date range for exploration, visualization and export via RedCap CSV-File.",
        )

        if state.parsed_data:
            st.button("Overview", on_click=go_to_homepage, width="stretch")
            explore_expander()
            forms_expander()