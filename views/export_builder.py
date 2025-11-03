import streamlit as st
from state_provider.state_provider_class import state_provider
from datetime import date, time, timedelta
import datetime as dt
from services.value_aggregation.lab_aggregator import LabAggregator

class ExportBuilder:

    @staticmethod
    def _to_datetime(value):
        if isinstance(value, dt.datetime):
            return value
        if isinstance(value, date):
            return dt.datetime.combine(value, dt.datetime.min.time())
        return None

    @staticmethod
    def _dates_from_range(candidate, fallback):
        if isinstance(candidate, (list, tuple)) and len(candidate) == 2:
            start, end = candidate
            start_date = start.date() if isinstance(start, dt.datetime) else start if isinstance(start, date) else None
            end_date = end.date() if isinstance(end, dt.datetime) else end if isinstance(end, date) else None
            if start_date and end_date:
                return (start_date, end_date)
        return fallback

    def _has_ecmo_data(self):
        return not state_provider.query_data("ecmo").empty

    def _has_impella_data(self):
        return not state_provider.query_data("impella").empty

    def _update_record_id(self):
        new_id = st.session_state["export_record_id_input"]
        st.session_state["record_id_input"] = new_id
        state_provider.update_state(record_id=new_id)

    def _sync_export_date_range(self):
        raw_value = st.session_state.get("export_date_range_input")
        print(f"exporter raw_value: {raw_value}")
        if isinstance(raw_value, (date, dt.datetime)):
            values = (raw_value, raw_value)
        elif isinstance(raw_value, (list, tuple)) and len(raw_value) == 2:
            values = tuple(raw_value)
        else:
            print("returning because exporter raw_value is not valid")
            return

        start_dt = self._to_datetime(values[0])
        end_dt = self._to_datetime(values[1])
        if not start_dt or not end_dt:
            print("export returning")
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
            #value=current_value,
            key="export_date_range_input",
            on_change=self._sync_export_date_range,
            help="Select the date range for exploration, visualization and export via RedCap CSV-File.",
        )
    
    def _build_data(self):
        dates = []
        selected = state_provider.get_selected_time_range()
        # selected is expected to be a (start, end) tuple; handle datetimes and dates
        if isinstance(selected, (list, tuple)) and len(selected) == 2:
            start, end = selected
            if isinstance(start, dt.datetime):
                start = start.date()
            if isinstance(end, dt.datetime):
                end = end.date()
            # ensure valid date range and build inclusive list of dates
            if isinstance(start, dt.date) and isinstance(end, dt.date) and start <= end:
                current = start
                while current <= end:
                    dates.append(current)
                    current = current + timedelta(days=1)
        
        data = []
        for date in dates:
            if self._has_ecmo_data() and state_provider.get_nearest_ecls_time():
                ecls_lab_builder = LabAggregator(
                    state_provider,
                    date=date,
                    record_id=state_provider.get_record_id(),
                    redcap_event_name="ecls_arm_2",
                    redcap_repeat_instrument="labor",
                    redcap_repeat_instance=1,
                    value_strategy=state_provider.get_value_strategy(),
                    nearest_time=state_provider.get_nearest_ecls_time()
                )
                entry = ecls_lab_builder.create_lab_entry()
                data.append(entry)
            
            if self._has_impella_data() and state_provider.get_nearest_impella_time():
                impella_lab_builder = LabAggregator(
                    state_provider,
                    date=date,
                    record_id=state_provider.get_record_id(),
                    redcap_event_name="impella_arm_2",
                    redcap_repeat_instrument="labor",
                    redcap_repeat_instance=1,
                    value_strategy=state_provider.get_value_strategy(),
                    nearest_time=state_provider.get_nearest_impella_time()
                )
                entry = impella_lab_builder.create_lab_entry()
                data.append(entry)

        state_provider.update_state(lab_form=data)

    def _render_record_id_input(self):
        st.text_input("Record ID", value=state_provider.get_record_id(), key="export_record_id_input", on_change=self._update_record_id, help="Enter the RedCap record ID for CSV export")

    def _render_value_strategy_picker(self):
        value_strategy = state_provider.get_value_strategy()
        options = ["median", "mean", "first", "last", "nearest"]
        selected_option = st.selectbox("Select Value Strategy", options, index=options.index(value_strategy) if value_strategy in options else 0)
        state_provider.update_state(value_strategy=selected_option)

    def _render_nearest_time_picker(self):
        if state_provider.get_value_strategy() == "nearest":
            if self._has_ecmo_data():
                nearest_ecls_time = state_provider.get_nearest_ecls_time() or time(0,0)
                selected_ecls_time = st.time_input(
                    "Select Nearest ECLS Time",
                    value=nearest_ecls_time,
                    help=("Select the time to find the nearest values for.\n"
                          "Automatically set to the earliest time from ECLS data in the dataset if available,\n"
                          "otherwise set to midnight.\n"
                          "Adjust manually to the implantation time if needed."))
                state_provider.update_state(nearest_ecls_time=selected_ecls_time)
            
            if self._has_impella_data():
                nearest_impella_time = state_provider.get_nearest_impella_time() or time(0,0)
                selected_impella_time = st.time_input(
                    "Select Nearest Impella Time",
                    value=nearest_impella_time,
                    help=("Select the time to find the nearest values for.\n"
                          "Automatically set to the earliest time from Impella data in the dataset if available,\n"
                          "otherwise set to midnight.\n"
                          "Adjust manually to the implantation time if needed."))
                state_provider.update_state(nearest_impella_time=selected_impella_time)
    
    def _render_build_data_button(self):
        if state_provider.get_record_id():
            st.button("Build Data", on_click=self._build_data)

    def export_builder(self):
        st.title("Export Builder")
        st.write("Configure your export settings:")
        self._render_record_id_input()
        self._render_time_range_picker()
        self._render_value_strategy_picker()
        self._render_nearest_time_picker()
        self._render_build_data_button()

def export_builder():
    builder = ExportBuilder()
    builder.export_builder()