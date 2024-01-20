import streamlit as st


def null_notifier(body, **kwargs):
    pass


def logger_notifier(body, **kwargs):
    raise NotImplementedError


streamlit_toast_notifier = st.toast


default_notifier = streamlit_toast_notifier
