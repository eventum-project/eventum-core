from typing import Callable, MutableMapping, Optional

import streamlit as st

import eventum.studio.models as models
from eventum.catalog.manage import (CatalogReadError,
                                    get_timepattern_filenames,
                                    load_timepattern)
from eventum.studio.components.component import BaseComponent
from eventum.studio.components.time_pattern_adjuster import TimePatternAdjuster
from eventum.studio.key_management import WidgetKeysContext
from eventum.studio.notifiers import NotificationLevel, default_notifier


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

    def _show_manage_buttons(self):
        is_max_len = len(
            self._session_state['time_pattern_ids']
        ) >= self._MAX_LIST_SIZE

        st.button(
            'Create new',
            disabled=is_max_len,
            on_click=lambda: self.add(),
            use_container_width=True
        )
        col1, col2 = st.columns([7, 3])

        col1.selectbox(
            'Time patterns',
            options=get_timepattern_filenames(),
            key=self._wk('pattern_selected_for_load'),
            label_visibility='collapsed'
        )

        col2.button(
            'Load',
            disabled=(
                is_max_len
                or not self._session_state['pattern_selected_for_load']
            ),
            on_click=lambda: self._load_time_pattern(),
            use_container_width=True,
        )

        if is_max_len:
            st.write('*:grey[Maximum number of patterns]*')

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
        st.divider()
        self._show_manage_buttons()

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

    def _load_time_pattern(
        self,
        notify_callback: Callable[
            [str, NotificationLevel], None
        ] = default_notifier
    ) -> models.TimePatternConfig:
        """Load selected time pattern from catalog."""
        try:
            return load_timepattern(
                self._session_state['pattern_selected_for_load']
            )
        except CatalogReadError as e:
            notify_callback(str(e), NotificationLevel.ERROR)

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
