from typing import Callable, Optional, assert_never

import eventum.core.models.time_pattern_config as models
import streamlit as st
from eventum.repository.manage import ContentUpdateError, save_time_pattern
from eventum.studio.components.component import BaseComponent
from eventum.studio.notifiers import NotificationLevel, default_notifier
from pydantic import ValidationError


class Configurator(BaseComponent):
    """Component for controlling configuration of time pattern."""

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
            init = Configurator.get_default_configuration()
        else:
            saved = True

        ss['pattern_label'] = init.label
        ss['pattern_color'] = self._props['color']
        ss['is_saved'] = saved

        if saved:
            ss['pattern_filename'] = self._props['pattern_filename']

        ss['oscillator_period'] = init.oscillator.period
        ss['oscillator_period_unit'] = init.oscillator.unit
        ss['oscillator_start'] = str(init.oscillator.start)
        ss['oscillator_end'] = str(init.oscillator.end)

        ss['multiplier_ratio'] = init.multiplier.ratio

        ss['randomizer_deviation'] = init.randomizer.deviation
        ss['randomizer_direction'] = init.randomizer.direction

        ss['spreader_distribution'] = init.spreader.distribution
        self._set_distribution_parameters_in_state(init.spreader.parameters)

    def _set_default_distribution_parameters_in_state(self) -> None:
        ss = self._session_state

        ss['spreader_uniform_distr_bounds'] = (0.0, 1.0)

        ss['spreader_triangular_distr_last_changed'] = 'left'
        ss['spreader_triangular_distr_left_bounds'] = (0.0, 0.5)
        ss['spreader_triangular_distr_right_bounds'] = (0.5, 1.0)

        ss['spreader_beta_distr_a'] = 1.0
        ss['spreader_beta_distr_b'] = 1.0

    def _set_distribution_parameters_in_state(
        self,
        parameters: models.DistributionParameters
    ) -> None:
        self._set_default_distribution_parameters_in_state()

        ss = self._session_state
        match ss['spreader_distribution']:
            case models.Distribution.UNIFORM:
                ss['spreader_uniform_distr_bounds'] = (
                    parameters.low, parameters.high
                )
            case models.Distribution.TRIANGULAR:
                ss['spreader_triangular_distr_left_bounds'] = (
                    parameters.left, parameters.mode
                )
                ss['spreader_triangular_distr_right_bounds'] = (
                    parameters.mode, parameters.right
                )
            case models.Distribution.BETA:
                ss['spreader_beta_distr_a'] = parameters.a
                ss['spreader_beta_distr_b'] = parameters.b
            case val:
                assert_never(val)

    def _get_current_distribution_parameters(
        self
    ) -> models.DistributionParameters:
        ss = self._session_state

        match ss['spreader_distribution']:
            case models.Distribution.UNIFORM:
                low, high = ss['spreader_uniform_distr_bounds']
                return models.UniformDistributionParameters(
                    low=low,
                    high=high
                )
            case models.Distribution.TRIANGULAR:
                left, mode = ss['spreader_triangular_distr_left_bounds']
                _, right = ss['spreader_triangular_distr_right_bounds']
                return models.TriangularDistributionParameters(
                    left=left,
                    mode=mode,
                    right=right
                )
            case models.Distribution.BETA:
                return models.BetaDistributionParameters(
                    a=ss['spreader_beta_distr_a'],
                    b=ss['spreader_beta_distr_b']
                )
            case val:
                assert_never(val)

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
                key=self._wk.get_ephemeral(),
                on_click=lambda: self.save(overwrite=True),
                use_container_width=True,
            )
        else:
            st.button(
                'Save',
                key=self._wk.get_ephemeral(),
                on_click=lambda: self.save(),
                use_container_width=True,
            )
        st.button(
            'Delete',
            key=self._wk.get_ephemeral(),
            on_click=lambda: self._props['delete_callback'](),
            use_container_width=True,
            type='primary',
        )

    def _show_oscillator_section(self) -> None:
        st.header('Oscillator')
        col1, col2 = st.columns([3, 7])
        col1.number_input(
            'Period',
            step=1.0,
            min_value=0.0,
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
            key=self._wk('oscillator_start'),
        )
        col2.text_input(
            'End time',
            key=self._wk('oscillator_end'),
        )

    def _show_multiplier_section(self) -> None:
        st.header('Multiplier')
        st.number_input(
            'Ratio',
            step=1,
            min_value=1,
            key=self._wk('multiplier_ratio')
        )

    def _show_randomizer_section(self) -> None:
        st.header('Randomizer')
        st.number_input(
            'Deviation',
            min_value=0.0,
            max_value=1.00,
            step=0.05,
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

    def _show_spreader_parameters(self) -> None:
        ss = self._session_state
        match ss['spreader_distribution']:
            case models.Distribution.UNIFORM:
                st.slider(
                    'Bounds',
                    min_value=0.0,
                    max_value=1.0,
                    key=self._wk('spreader_uniform_distr_bounds')
                )
            case models.Distribution.TRIANGULAR:
                left, mode_l = ss['spreader_triangular_distr_left_bounds']
                mode_r, right = ss['spreader_triangular_distr_right_bounds']
                mode = (
                    mode_l
                    if ss['spreader_triangular_distr_last_changed'] == 'left'
                    else mode_r
                )

                ss['spreader_triangular_distr_left_bounds'] = (left, mode)
                ss['spreader_triangular_distr_right_bounds'] = (mode, right)

                st.slider(
                    'Increasing bounds',
                    min_value=0.0,
                    max_value=1.0,
                    key=self._wk('spreader_triangular_distr_left_bounds'),
                    on_change=(
                        lambda: ss.__setitem__(
                            'spreader_triangular_distr_last_changed',
                            'left'
                        )
                    )
                )
                st.slider(
                    'Decreasing bounds',
                    min_value=0.0,
                    max_value=1.0,
                    key=self._wk('spreader_triangular_distr_right_bounds'),
                    on_change=(
                        lambda: ss.__setitem__(
                            'spreader_triangular_distr_last_changed',
                            'right'
                        )
                    )
                )
            case models.Distribution.BETA:
                col1, col2 = st.columns([1, 1])
                col1.number_input(
                    'A',
                    min_value=0.0,
                    step=0.1,
                    key=self._wk('spreader_beta_distr_a')
                )
                col2.number_input(
                    'B',
                    min_value=0.0,
                    step=0.1,
                    key=self._wk('spreader_beta_distr_b')
                )
            case val:
                assert_never(val)

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
        self._show_spreader_parameters()

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
        """Save currently configured time pattern to repository as
        configuration file.
        """
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

    @property
    def label(self) -> str:
        """Get current label of time pattern."""
        return self._session_state['pattern_label']

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
                start=ss['oscillator_start'],
                end=ss['oscillator_end']
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
                parameters=self._get_current_distribution_parameters()
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
                end='+1h'
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
