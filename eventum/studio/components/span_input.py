import streamlit as st

from eventum.studio.components.component import BaseComponent
from eventum.studio.notifiers import NotificationLevel, default_notifier
from eventum.utils.relative_time import validate_time_span


class SpanInput(BaseComponent):
    """Span input component."""

    def _init_state(self) -> None:
        self._session_state['span_expression'] = '10m'
        self._session_state['previous_span_expression'] = '10m'
        self._session_state['mode'] = 'Auto'

    def _show(self) -> None:
        col1, col2 = st.columns([1, 1])

        col1.radio(
            label='Time span',
            help=(
                'Time span of one bin in histogram.'
            ),
            key=self._wk('mode'),
            options=['Auto', 'Custom'],
            horizontal=True
        )

        col2.text_input(
            'Custom span',
            placeholder='expression',
            help='Expression examples: `1s`, `30m`, `12h`, `7d`, ... etc.',
            key=self._wk('span_expression'),
            disabled=self.is_auto(),
            on_change=self._check_expression
        )

        ss = self._session_state
        ss['previous_span_expression'] = ss['span_expression']

    def _check_expression(self) -> None:
        ss = self._session_state
        if not validate_time_span(ss['span_expression']):
            ss['span_expression'] = ss['previous_span_expression']
            default_notifier(
                message='Incorrect span expression',
                level=NotificationLevel.WARNING
            )

    def is_auto(self) -> bool:
        """Get status whether `Auto` mode is selected."""
        return True if self._session_state['mode'] == 'Auto' else False

    def get_expression(self) -> str:
        """Get current span expression."""
        return self._session_state['span_expression']
