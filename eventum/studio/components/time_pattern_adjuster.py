from datetime import datetime
import os
from dataclasses import asdict
from typing import Callable

import streamlit as st
from yaml import YAMLError

import eventum.studio.models as models
from eventum.studio.components.component import BaseComponent
from eventum.studio.notifiers import NotificationLevel, default_notifier
from eventum.utils.fs import (TIME_PATTERNS_DIR, save_object_as_yaml,
                              validate_yaml_filename)


class TimePatternAdjuster(BaseComponent):
    def _show_manage_section(self) -> None:
        st.header("General")
        st.text_input("Label", key=self._wk("pattern_label"))
        st.text_input(
            "File name",
            key=self._wk("pattern_filename"),
            disabled=self._wk("is_saved") is True,
        )

        if self._session_state["is_saved"]:
            st.button(
                "Update",
                key=self._wk("update_pattern"),
                on_click=lambda: self.save(overwrite=True),
                use_container_width=True,
            )
        else:
            st.button(
                "Save",
                key=self._wk("save_pattern"),
                on_click=lambda: self.save(),
                use_container_width=True,
            )
        st.button(
            "Delete",
            key=self._wk("delete_pattern"),
            on_click=(
                lambda: self._props['delete_callback'](
                    callback=self._release_state
                )
            ),
            use_container_width=True,
            type="primary",
        )

    def _show_oscillator_section(self) -> None:
        st.header('Ocillator')
        col1, col2 = st.columns([8, 2])
        col1.number_input(
            'Interval',
            step=1,
            key=self._wk('oscillator_interval')
        )
        col2.selectbox(
            'Unit',
            options=[unit.value for unit in models.TimeUnit],
            key=self._wk('oscillator_interval_unit')
        )
        col1, col2 = st.columns(2)
        col1.text_input(
            'Start timestamp',
            key=self._wk('oscillator_start_timestamp'),
        )
        col2.text_input(
            'End timestamp',
            key=self._wk('oscillator_end_timestamp'),
        )

    def _show_multiplier_section(self) -> None:
        st.header('Multiplier')
        st.number_input(
            'Ratio',
            step=1,
            key=self._wk('multiplier_ratio')
        )

    def _show_randomizer_section(self) -> None:
        st.header('Randomizer')
        st.number_input(
            'Deviation',
            step=1,
            key=self._wk('randomizer_deviation')
        )
        st.selectbox(
            'Direction',
            options=[
                direction.value
                for direction in models.RandomizerDirection
            ],
            key=self._wk('randomizer_direction'),
            help='...'
        )

    def _show_spreader_section(self) -> None:
        st.header('Spreader')
        st.selectbox(
            'Function',
            options=[
                func.value
                for func in models.DistributionFunction
            ],
            key=self._wk('spreader_function'),
            help='...'
        )

    def _show(self):
        label = self._session_state["pattern_label"]
        color = self._session_state["pattern_color"]

        with st.expander(f":{color}[{label}]"):
            self._show_manage_section()
            st.divider()
            self._show_oscillator_section()
            st.divider()
            self._show_multiplier_section()
            st.divider()
            self._show_randomizer_section()
            st.divider()
            self._show_spreader_section()

    def save(
        self,
        overwrite: bool = False,
        notify_callback: Callable[
            [str, NotificationLevel], None
        ] = default_notifier
    ):
        filename = self._session_state['pattern_filename']
        try:
            validate_yaml_filename(filename)
        except ValueError as e:
            notify_callback(str(e), NotificationLevel.ERROR)
            return

        filepath = os.path.join(TIME_PATTERNS_DIR, filename)
        if overwrite is False and os.path.exists(filepath):
            notify_callback(
                'File already exists in library',
                NotificationLevel.ERROR
            )
            return

        try:
            save_object_as_yaml(
                data=asdict(self.get_current_configuration()),
                filepath=filepath
            )
        except (OSError, YAMLError) as e:
            notify_callback(str(e), NotificationLevel.ERROR)
            return

        self._session_state['pattern_is_saved'] = True
        notify_callback('Saved in library', NotificationLevel.SUCCESS)

    def get_current_configuration(self) -> models.TimePatternConfig:
        """Build TimePatternConfig from current input widgets values
        that are in the session state.
        """
        ss = self._session_state

        return models.TimePatternConfig(
            label=ss['pattern_label'],
            oscillator=models.OscillatorConfig(
                interval=ss['oscillator_interval'],
                unit=ss['oscillator_interval_unit'],
                start=ss['oscillator_start_timestamp'],
                end=ss['oscillator_end_timestamp']
            ),
            multiplier=models.MultiplierConfig(
                ratio=ss['multiplier_ratio']
            ),
            randomizer=models.RandomizerConfig(
                deviation=ss['randomizer_deviation'],
                direction=ss['randomizer_direction']
            ),
            spreader=models.SpreaderConfig(
                function=ss['spreader_function'],
                parameters=dict()   # TODO: think how to handle parameters
            )
        )

    @staticmethod
    def get_default_configuration(
        label: str = 'New pattern'
    ) -> models.TimePatternConfig:
        """Create `TimePatternConfig` object with default values."""
        return models.TimePatternConfig(
            label=label,
            oscillator=models.OscillatorConfig(
                interval=1,
                unit=models.TimeUnit.SECONDS.value,
                start=datetime.now().replace(microsecond=0).isoformat(),
                end=datetime.now().replace(microsecond=0).isoformat()
            ),
            multiplier=models.MultiplierConfig(ratio=1),
            randomizer=models.RandomizerConfig(
                deviation=0,
                direction=models.RandomizerDirection.MIXED.value
            ),
            spreader=models.SpreaderConfig(
                function=models.DistributionFunction.LINEAR.value,
                parameters=models.DistributionParameters()
            )
        )
