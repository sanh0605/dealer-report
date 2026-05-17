import streamlit as st

def render_kpi_row(metrics: list[dict]) -> None:
    with st.container(horizontal=True):
        for m in metrics:
            st.metric(
                label=m["label"],
                value=m["value"],
                delta=m.get("delta"),
                delta_color=m.get("delta_color", "normal"),
                border=True
            )
