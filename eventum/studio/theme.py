import streamlit as st


def apply_theme():
    """Apply theme for page by setting css styles."""
    st.markdown(
        '<style>'
        'code {color: #8A8BC8}\n'
        'div[data-testid=stToast] {background-color: #1c1f31}\n'
        '</style>',
        unsafe_allow_html=True
    )
