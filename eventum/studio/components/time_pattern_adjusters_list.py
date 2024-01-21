from typing import MutableMapping, Optional

import streamlit as st
from eventum.studio.components.component import BaseComponent
from eventum.studio.components.time_pattern_adjuster import TimePatternAdjuster

from eventum.studio.key_management import WidgetKeysContext
import eventum.studio.models as models


class TimePatternAdjustersListOverflowError(Exception):
    """Exception for indicating overflows in TimePatternAdjustersList."""


class TimePatternAdjustersList(BaseComponent):
    """List of time pattern adjusters."""

    _TIME_PATTERN_COLORS = ('blue', 'green', 'orange', 'red', 'violet')
    _MAX_LIST_SIZE = 5

    def __init__(
        self,
        session_state: MutableMapping = st.session_state,
        id: int = 1,
        widget_keys_context: Optional[WidgetKeysContext] = None,
        props: Optional[dict] = None
    ) -> None:
        self._check_time_pattern_colors()
        super().__init__(session_state, id, widget_keys_context, props)

    def _init_state(self):
        self._session_state['time_pattern_id_counter'] = 1
        self._session_state['time_patterns_counter'] = 0
        self._session_state['time_pattern_ids'] = []
        self._session_state['available_colors'] = set(
            TimePatternAdjustersList._TIME_PATTERN_COLORS
        )
        self._session_state['given_colors'] = dict()

    def release_state(self):
        del self._session_state['time_pattern_id_counter']
        del self._session_state['time_patterns_counter']
        del self._session_state['time_pattern_ids']
        del self._session_state['available_colors']
        del self._session_state['given_colors']

        super().release_state()

    def _show(self):
        st.title('Time Patterns')
        for id in self._session_state['time_pattern_ids']:
            TimePatternAdjuster(
                id=id,
                widget_keys_context=self._wk,
                props={
                    'delete_callback': (
                        lambda id=id: self.delete(id)
                    )
                }
            )._show()

    def add(
        self,
        initial_state: Optional[models.TimePatternConfig] = None,
        pattern_filename: Optional[str] = None
    ) -> None:
        """Add time pattern adjuster element to list."""
        if self._session_state['time_patterns_counter'] == self._MAX_LIST_SIZE:
            raise TimePatternAdjustersListOverflowError(
                f'Max size ({self._MAX_LIST_SIZE}) of list is exceeded'
            )

        id = self._session_state['time_pattern_id_counter']
        self._session_state['time_pattern_ids'].append(id)
        self._session_state['time_pattern_id_counter'] += 1
        self._session_state['time_patterns_counter'] += 1

        color = self._session_state['available_colors'].pop()
        self._session_state['given_colors'][id] = color

        TimePatternAdjuster(
            id=id,
            widget_keys_context=self._wk,
            props={
                'initial_state': initial_state,
                'pattern_filename': pattern_filename,
                'color': color
            }
        )

    def delete(self, id: int) -> None:
        """Delete specified time pattern adjuster from list."""
        TimePatternAdjuster(
            id=id,
            widget_keys_context=self._wk
        ).release_state()

        self._session_state['time_pattern_ids'].remove(id)
        self._session_state['time_patterns_counter'] -= 1
        self._session_state['available_colors'].add(
            self._session_state['given_colors'].pop(id)
        )

    @classmethod
    def _check_time_pattern_colors(cls) -> None:
        """Check if number of unique time pattern colors is greater or equal
        to `_MAX_LIST_SIZE`. Raise ValueError otherwise.
        """
        unique_colors = len(set(cls._TIME_PATTERN_COLORS))
        if unique_colors < cls._MAX_LIST_SIZE:
            raise ValueError(
                f'`_MAX_SIZE` is set to {cls._MAX_LIST_SIZE} but there are '
                f'only {unique_colors} unique colors in `_LABEL_COLORS`'
            )
