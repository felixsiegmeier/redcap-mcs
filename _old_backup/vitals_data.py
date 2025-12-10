from state_provider.state_provider import state_provider
import streamlit as st
import altair as alt
import pandas as pd


def render_vitals_data():
    
    def category_picker():
        state = state_provider.get_state()
        with st.expander("Categories"):
            vitals_data = state_provider.query_data("vitals")
            categories = vitals_data["category"].unique().tolist()
            state.vitals_ui.selected_categories = st.pills(
                label="Select categories",
                options=categories,
                selection_mode="multi",
            )
            state_provider.save_state(state)

    def parameter_picker():
        state = state_provider.get_state()
        with st.expander("Parameters"):
            if state.vitals_ui.selected_categories:
                vitals_data = state_provider.query_data("vitals", {"category": state.vitals_ui.selected_categories})
                parameters = vitals_data["parameter"].unique().tolist()
                state.vitals_ui.selected_parameters = st.pills(
                    label="Select parameters",
                    options=parameters,
                    selection_mode="multi",
                )
            else:
                st.warning("Please select at least one category to see available parameters.")
                state.vitals_ui.selected_parameters = []
            state_provider.save_state(state)

    def get_filtered_vitals():
        state = state_provider.get_state()
        filters = {}
        if state.vitals_ui.selected_categories:
            filters["category"] = state.vitals_ui.selected_categories
        if state.vitals_ui.selected_parameters:
            filters["parameter"] = state.vitals_ui.selected_parameters
        if hasattr(state, "selected_time_range") and state.selected_time_range:
            start, end = state.selected_time_range
            filters["timestamp"] = [start, end]
        is_aggregated = state.vitals_ui.show_median
        if is_aggregated:
            filters["value_strategy"] = "median"
        filtered = state_provider.query_data("vitals", filters)
        return filtered, is_aggregated

    def median_picker():
        state = state_provider.get_state()
        state.vitals_ui.show_median = st.checkbox("Show median value")
        state_provider.save_state(state)

    state = state_provider.get_state()
    st.header("Vitals Data")
    if hasattr(state, "selected_time_range") and state.selected_time_range:
        start, end = state.selected_time_range
        st.subheader(f"Date Range: {start.strftime('%d.%m.%Y')} - {end.strftime('%d.%m.%Y')}")
    category_picker()
    if state.vitals_ui.selected_categories:
        parameter_picker()
        median_picker()
        if not state.vitals_ui.selected_parameters:
            st.warning("Please select at least one parameter.")
            return
    else:
        st.warning("Please select at least one category.")
        return
    filtered_vitals, is_aggregated = get_filtered_vitals()
    st.write(filtered_vitals)
    
    if not filtered_vitals.empty:
        x_field = "date:T" if is_aggregated else "timestamp:T"
        tooltip_fields = ["date:T", "parameter:N", "value:Q"] if is_aggregated else ["timestamp:T", "parameter:N", "value:Q"]
        chart = alt.Chart(filtered_vitals).mark_line(point=True).encode(
            x=x_field,
            y="value:Q",
            color="parameter:N",
            tooltip=tooltip_fields
        ).properties(
            width=700,
            height=400,
            title="Vitals Over Time"
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No data available for the selected filters.")