import streamlit as st


def apply_theme():
    """Apply theme for page by setting css styles."""
    st.markdown(
        '<style>'
        'code {color: #8282ef}'
        'div[data-testid=stToast] {background-color: #252526}'
        '</style>',
        unsafe_allow_html=True
    )
