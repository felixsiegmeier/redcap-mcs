import streamlit as st
import pandas as pd
from io import StringIO
from state_provider.state_provider import state_provider
from schemas.app_state_schemas.app_state import Views


def render_startpage():
    st.title("mLife Data Parser")
    st.write("Upload your CSV file 'Gesamte Akte' for processing:")
    st.markdown("When you upload a file, this view will be replaced by the homepage.")

    uploaded_file = st.file_uploader("Choose a file", type="csv")

    if uploaded_file is not None:
        # Parse and switch to homepage
        try:
            df = pd.read_csv(uploaded_file, sep=";")
            state_provider.parse_data_to_state(df)
            if state_provider.get_state() is not None:
                state_provider.update_state(selected_view=Views.HOMEPAGE)
            st.rerun()  # Refresh to show homepage
        except Exception as e:
            st.error(f"Error parsing file: {e}")