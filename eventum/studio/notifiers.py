import streamlit as st


default_notifier = st.toast


def null_notifier(body, **kwargs):
    pass


def logger_notifier(body, **kwargs):
    raise NotImplementedError
