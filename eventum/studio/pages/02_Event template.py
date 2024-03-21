import streamlit as st
from eventum.studio.components.component import persist_state

persist_state()

st.write(st.session_state)
