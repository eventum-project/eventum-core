import streamlit as st

from eventum.studio.components.component import BaseComponent
from eventum.studio.notifiers import NotificationLevel, default_notifier
from eventum.utils.relative_time import validate_time_span


class DownsamplingInput(BaseComponent):
    """Downsampling input component."""

    def _init_state(self) -> None:
        self._session_state['downsampling_span'] = '1s'
        self._session_state['downsampling_span_previous'] = '1s'
        self._session_state['status'] = 'Off'

    def _show(self) -> None:
        col1, col2 = st.columns([1, 1])

        col1.radio(
            label='Downsampling',
            key=self._wk('status'),
            options=['Off', 'On'],
            horizontal=True
        )

        col2.text_input(
            'Downsampling span',
            key=self._wk('downsampling_span'),
            placeholder='expression',
            disabled=self.get_status() is False,
            on_change=self._check_expression
        )

        ss = self._session_state
        ss['downsampling_span_previous'] = ss['downsampling_span']

    def _check_expression(self) -> None:
        ss = self._session_state
        if not validate_time_span(ss['downsampling_span']):
            ss['downsampling_span'] = ss['downsampling_span_previous']
            default_notifier(
                message='Incorrect downsampling span',
                level=NotificationLevel.WARNING
            )

    def get_status(self) -> bool:
        """Get status whether downsampling is enabled."""
        return True if self._session_state['status'] == 'On' else False

    def get_span(self) -> str:
        """Get current span of downsampling."""
        return self._session_state['downsampling_span']
