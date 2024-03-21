from typing import Callable, Optional

import streamlit as st
from pydantic import ValidationError

import eventum.core.models.time_pattern_config as models
from eventum.repository.manage import ContentUpdateError, save_time_pattern
from eventum.studio.components.component import BaseComponent
from eventum.studio.notifiers import NotificationLevel, default_notifier


class TimePatternAdjuster(BaseComponent):
    _STATE_INITIALIZATION_PROPS = {
        'initial_state': Optional[models.TimePatternConfig],
        'pattern_filename': Optional[str],
        'color': str
    }
    _SHOW_PROPS = {
        'save_callback': Callable[[str], None],
        'delete_callback': Callable
    }

    def _init_state(self) -> None:
        ss = self._session_state
        init = self._props['initial_state']

        if init is None:
            saved = False
            init = TimePatternAdjuster.get_default_configuration()
        else:
            saved = True

        ss['pattern_label'] = init.label
        ss['pattern_color'] = self._props['color']
        ss['is_saved'] = saved

        if saved:
            ss['pattern_filename'] = self._props['pattern_filename']

        ss['oscillator_period'] = init.oscillator.period
        ss['oscillator_period_unit'] = init.oscillator.unit
        ss['oscillator_start_timestamp'] = init.oscillator.start
        ss['oscillator_end_timestamp'] = init.oscillator.end

        ss['multiplier_ratio'] = init.multiplier.ratio

        ss['randomizer_deviation'] = init.randomizer.deviation
        ss['randomizer_direction'] = init.randomizer.direction

        ss['spreader_distribution'] = init.spreader.distribution

    def _show_manage_section(self) -> None:
        st.header('General')
        st.text_input('Label', key=self._wk('pattern_label'))
        st.text_input(
            'File name',
            key=self._wk('pattern_filename'),
            disabled=self._session_state['is_saved']
        )

        if self._session_state['is_saved']:
            st.button(
                'Update',
                key=self._wk('update_pattern'),
                on_click=lambda: self.save(overwrite=True),
                use_container_width=True,
            )
        else:
            st.button(
                'Save',
                key=self._wk('save_pattern'),
                on_click=lambda: self.save(),
                use_container_width=True,
            )
        st.button(
            'Delete',
            key=self._wk('delete_pattern'),
            on_click=lambda: self._props['delete_callback'](),
            use_container_width=True,
            type='primary',
        )

    def _show_oscillator_section(self) -> None:
        st.header('Oscillator')
        col1, col2 = st.columns([3, 7])
        col1.number_input(
            'Period',
            step=1,
            key=self._wk('oscillator_period')
        )
        col2.selectbox(
            'Unit',
            options=[unit.value for unit in models.TimeUnit],
            key=self._wk('oscillator_period_unit')
        )
        col1, col2 = st.columns(2)
        col1.text_input(
            'Start time',
            key=self._wk('oscillator_start_timestamp'),
        )
        col2.text_input(
            'End time',
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
            'Distribution',
            options=[
                func.value
                for func in models.Distribution
            ],
            key=self._wk('spreader_distribution'),
            help='...'
        )

    def _show(self):
        label = self._session_state['pattern_label']
        color = self._session_state['pattern_color']

        with st.expander(f':{color}[{label}]'):
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
        try:
            save_time_pattern(
                pattern_config=self.get_current_configuration(),
                path=self._session_state['pattern_filename'],
                overwrite=overwrite
            )
        except ValidationError as e:
            notify_callback(
                f'Field validation fail for "{e.title}"',
                NotificationLevel.ERROR
            )
            return
        except ContentUpdateError as e:
            notify_callback(f'Failed to save: {e}', NotificationLevel.ERROR)
            return

        self._props['save_callback'](self._session_state['pattern_filename'])

        self._session_state['is_saved'] = True
        notify_callback('Saved in repository', NotificationLevel.SUCCESS)

    def is_saved(self) -> bool:
        """Get status whether the time pattern is saved in repository."""
        return self._session_state['is_saved']

    def get_saved_filename(self) -> Optional[str]:
        """Get filename of time pattern if it is saved. If pattern is not
        saved then `None` will be returned.
        """
        if self._session_state['is_saved']:
            return self._session_state['pattern_filename']
        else:
            return None

    def get_current_configuration(self) -> models.TimePatternConfig:
        """Build TimePatternConfig from current input widgets values
        that are in the session state.
        """
        ss = self._session_state

        return models.TimePatternConfig(
            label=ss['pattern_label'],
            oscillator=models.OscillatorConfig(
                period=ss['oscillator_period'],
                unit=ss['oscillator_period_unit'],
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
                distribution=ss['spreader_distribution'],
                parameters=None   # TODO: think how to handle parameters
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
                period=1,
                unit=models.TimeUnit.SECONDS,
                start=models.TimeKeyword.NOW,
                end=models.TimeKeyword.NEVER
            ),
            multiplier=models.MultiplierConfig(ratio=1),
            randomizer=models.RandomizerConfig(
                deviation=0,
                direction=models.RandomizerDirection.MIXED
            ),
            spreader=models.SpreaderConfig(
                distribution=models.Distribution.UNIFORM,
                parameters=models.UniformDistributionParameters(
                    low=0,
                    high=1
                )
            )
        )
