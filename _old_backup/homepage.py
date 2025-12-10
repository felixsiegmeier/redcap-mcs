import streamlit as st
from state_provider.state_provider import state_provider
from datetime import datetime
import pandas as pd

def render_ecmo_time_ranges():
    ecmo_time_ranges = state_provider.get_device_time_ranges("ecmo")

    # Cleanup required to remove invalid entries, e.g. "ECMO-Durchtrittsstelle"
    clean_ecmo_time_ranges = []
    for device, start, end in ecmo_time_ranges:
        if not isinstance(device, str):
            continue
        if device.lower().startswith("ecmo"):
            clean_ecmo_time_ranges.append((device, start, end))

    if not len(clean_ecmo_time_ranges):
        st.write("No valid ECMO time ranges found.")
        return

    for device, start, end in clean_ecmo_time_ranges:
        if isinstance(start, datetime) and isinstance(end, datetime):
            st.markdown(f"**<u>{device}</u>: {start.strftime('%d.%m.%Y %H:%M')} - {end.strftime('%d.%m.%Y %H:%M')}**", unsafe_allow_html=True)

def render_impella_time_ranges():
    impella_time_ranges = state_provider.get_device_time_ranges("impella")

    # Cleanup
    clean_impella_time_ranges = []
    for device, start, end in impella_time_ranges:
        if not isinstance(device, str):
            continue
        if device.lower().startswith("impella"):
            clean_impella_time_ranges.append((device, start, end))

    if not len(clean_impella_time_ranges):
        st.write("No valid Impella time ranges found.")
        return

    for device, start, end in clean_impella_time_ranges:
        if isinstance(start, datetime) and isinstance(end, datetime):
            st.markdown(f"**<u>{device}</u>: {start.strftime('%d.%m.%Y %H:%M')} - {end.strftime('%d.%m.%Y %H:%M')}**", unsafe_allow_html=True)

def render_crrt_time_ranges():
    crrt_time_ranges = state_provider.get_device_time_ranges("crrt")

    if not len(crrt_time_ranges):
        st.write("No valid CRRT time ranges found.")
        return

    for device, start, end in crrt_time_ranges:
        if isinstance(start, datetime) and isinstance(end, datetime):
            st.markdown(f"**<u>{device}</u>: {start.strftime('%d.%m.%Y %H:%M')} - {end.strftime('%d.%m.%Y %H:%M')}**", unsafe_allow_html=True)

def render_set_selected_time_range_to_mcs_button():
    mcs_time_ranges = []
    mcs_time_ranges.extend(data for data in state_provider.get_device_time_ranges("impella"))
    mcs_time_ranges.extend(data for data in state_provider.get_device_time_ranges("ecmo"))

    if not len(mcs_time_ranges):
        return

    try:
        mcs_start_date = min(range.start for range in mcs_time_ranges)
        mcs_end_date = max(range.end for range in mcs_time_ranges)
    except ValueError:
        print("Error occurred while determining MCS time range.")
        return

    def set_mcs_range():
        if not mcs_start_date or not mcs_end_date:
            return

        normalized = (mcs_start_date.date(), mcs_end_date.date())
        st.session_state["date_range_input"] = normalized
        st.session_state["export_date_range_input"] = normalized
        state_provider.set_selected_time_range(mcs_start_date, mcs_end_date)

    st.button("Set Selected Time Range to MCS", on_click=set_mcs_range, help="Set the selected time range to the cumulative time span of MCS devices.")

def render_homepage():
    st.header("Overview")
    
    if not state_provider.has_parsed_data():
        st.info("No parsed data available.")
        return
    
    st.subheader("Time Range")
    time_range = state_provider.get_time_range()
    selected_range = state_provider.get_selected_time_range()

    if time_range:
        start = time_range[0].strftime("%d.%m.%Y")
        end = time_range[1].strftime("%d.%m.%Y")
        st.write(f"Available Time Range of Patient Record: **{start} - {end}**")
    else:
        st.write("Available Time Range of Patient Record: **n/a**")

    if selected_range:
        selected_start = selected_range[0].strftime("%d.%m.%Y")
        selected_end = selected_range[1].strftime("%d.%m.%Y")
        st.write(f"Selected Time Range: **{selected_start} - {selected_end}**")
    else:
        st.write("Selected Time Range: **n/a**")

    vitals_count = len(state_provider.query_data("vitals")) if isinstance(state_provider.query_data("vitals"), pd.DataFrame) else 0
    lab_count = len(state_provider.query_data("lab")) if isinstance(state_provider.query_data("lab"), pd.DataFrame) else 0
    ecmo_count = len(state_provider.query_data("ecmo")) if isinstance(state_provider.query_data("ecmo"), pd.DataFrame) else 0
    impella_count = len(state_provider.query_data("impella")) if isinstance(state_provider.query_data("impella"), pd.DataFrame) else 0
    respiratory_count = len(state_provider.query_data("respiratory")) if isinstance(state_provider.query_data("respiratory"), pd.DataFrame) else 0
    medication_count = len(state_provider.query_data("medication")) if isinstance(state_provider.query_data("medication"), pd.DataFrame) else 0

    st.markdown(f""" Containing in Total:
- **{vitals_count}** Vitals  
- **{lab_count}** Lab Results  
- **{ecmo_count + impella_count}** MCS Recordings  
- **{respiratory_count}** Respiratory Values  
- **{medication_count}** Medication entries
    """)

    st.subheader("MCS Time Range")
    render_ecmo_time_ranges()
    render_impella_time_ranges()
    render_set_selected_time_range_to_mcs_button()
    st.subheader("CRRT Time Range")
    render_crrt_time_ranges()