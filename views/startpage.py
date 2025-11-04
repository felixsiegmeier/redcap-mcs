import streamlit as st
from state_provider.state_provider import state_provider
from schemas.app_state_schemas.app_state import Views
from services.delimiter_auto_detecion import detect_delimiter


def render_startpage():
    st.title("mLife Data Parser")
    st.write("Upload your CSV file 'Gesamte Akte' for processing:")
    st.markdown("When you upload a file, this view will be replaced by the homepage.")

    uploaded_file = st.file_uploader("Choose a file", type="csv")

    if uploaded_file is not None:
        # Parse and switch to homepage
        file = uploaded_file.read().decode("utf-8")
        delimiter = detect_delimiter(file)
        if delimiter is None:
            st.error("Invalid file: No valid delimiter detected. The file must contain more than 20 occurrences of ';' or '|' as delimiter.")
        else:
            state_provider.parse_data_to_state(file, delimiter)
            if state_provider.get_state() is not None:
                state_provider.update_state(selected_view=Views.HOMEPAGE)
            st.rerun()  # Refresh to show homepage