import streamlit as st
from state_provider.state_provider_class import state_provider
from datetime import date, datetime, time

class ExportBuilder:

    @staticmethod
    def _to_datetime(value):
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        return None

    @staticmethod
    def _dates_from_range(candidate, fallback):
        if isinstance(candidate, (list, tuple)) and len(candidate) == 2:
            start, end = candidate
            start_date = start.date() if isinstance(start, datetime) else start if isinstance(start, date) else None
            end_date = end.date() if isinstance(end, datetime) else end if isinstance(end, date) else None
            if start_date and end_date:
                return (start_date, end_date)
        return fallback

    def _update_record_id(self):
        new_id = st.session_state["export_record_id_input"]
        st.session_state["record_id_input"] = new_id
        state_provider.update_state(record_id=new_id)

    def _sync_export_date_range(self):
        raw_value = st.session_state.get("export_date_range_input")
        if isinstance(raw_value, (date, datetime)):
            values = (raw_value, raw_value)
        elif isinstance(raw_value, (list, tuple)) and len(raw_value) == 2:
            values = tuple(raw_value)
        else:
            return

        start_dt = self._to_datetime(values[0])
        end_dt = self._to_datetime(values[1])
        if not start_dt or not end_dt:
            return

        normalized = (start_dt.date(), end_dt.date())
        st.session_state["export_date_range_input"] = normalized
        st.session_state["date_range_input"] = normalized
        state_provider.set_selected_time_range(start_dt, end_dt)

    def _render_time_range_picker(self):
        default_range = (date.today(), date.today())
        selected_range = state_provider.get_selected_time_range()
        initial_range = self._dates_from_range(selected_range, default_range)

        current_value = self._dates_from_range(
            st.session_state.get("export_date_range_input"),
            initial_range,
        )

        st.session_state.setdefault("export_date_range_input", current_value)
        st.session_state.setdefault("date_range_input", current_value)

        st.date_input(
            "Select a date range",
            value=current_value,
            key="export_date_range_input",
            on_change=self._sync_export_date_range,
            help="Select the date range for exploration, visualization and export via RedCap CSV-File.",
        )

    def _render_record_id_input(self):
        st.text_input("Record ID", value=state_provider.get_record_id(), key="export_record_id_input", on_change=self._update_record_id, help="Enter the RedCap record ID for CSV export")

    def _render_value_strategy_picker(self):
        value_strategy = state_provider.get_value_strategy()
        options = ["median", "mean", "first", "last", "nearest"]
        selected_option = st.selectbox("Select Value Strategy", options, index=options.index(value_strategy) if value_strategy in options else 0)
        state_provider.update_state(value_strategy=selected_option)

    def _render_nearest_time_picker(self):
        if state_provider.get_value_strategy() == "nearest":
            nearest_time = state_provider.get_nearest_time() or datetime.now().time()
            selected_time = st.time_input("Select Nearest Time", value=nearest_time, help="Select the time to find the nearest value to.")
            state_provider.update_state(nearest_time=selected_time)

    def export_builder(self):
        st.title("Export Builder")
        st.write("Configure your export settings:")
        self._render_record_id_input()
        self._render_time_range_picker()
        self._render_value_strategy_picker()
        self._render_nearest_time_picker()

def export_builder():
    builder = ExportBuilder()
    builder.export_builder()