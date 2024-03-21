import streamlit as st
from eventum.studio.components.component import persist_state
from eventum.studio.components.time_pattern_adjusters_list import \
    TimePatternAdjustersList

persist_state()

st.set_page_config(
    page_title="Eventum Studio",
)

with st.sidebar:
    TimePatternAdjustersList().show()


st.write(st.session_state)
