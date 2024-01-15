import streamlit as st
from eventum.studio.session import restore_state


restore_state(st.session_state)
