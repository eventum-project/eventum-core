import streamlit as st
from enum import Enum


class NotificationLevel(Enum):
    SUCCESS = 'success'
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'


class NotificationColor(Enum):
    SUCCESS = 'green'
    INFO = 'default'
    WARNING = 'yellow'
    ERROR = 'red'


def null_notifier(
    message: str,
    level: NotificationLevel = NotificationLevel.INFO,
):
    pass


def logger_notifier(
    message: str,
    level: NotificationLevel = NotificationLevel.INFO,
):
    raise NotImplementedError


def streamlit_toast_notifier(
    message: str,
    level: NotificationLevel = NotificationLevel.INFO,
):
    match level:
        case NotificationLevel.SUCCESS:
            fmt_msg = f':{NotificationColor.SUCCESS.value}[{message}]'
        case NotificationLevel.WARNING:
            fmt_msg = f':{NotificationColor.WARNING.value}[{message}]'
        case NotificationLevel.ERROR:
            fmt_msg = f':{NotificationColor.ERROR.value}[{message}]'
        case _:
            fmt_msg = message

    return lambda: st.toast(fmt_msg)


default_notifier = streamlit_toast_notifier
