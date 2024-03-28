from datetime import datetime
from typing import Iterable

import pandas as pd
import plotly.graph_objects as go       # type: ignore
import streamlit as st
from eventum.core.models.time_pattern_config import TimePatternConfig
from eventum.core.plugins.input.base import InputPluginRuntimeError
from eventum.core.plugins.input.time_pattern import TimePatternInputPlugin
from eventum.studio.components.component import BaseComponent
from eventum.studio.notifiers import NotificationLevel, default_notifier


def _hash_config(config: TimePatternConfig) -> int:
    return hash(
        (
            config.oscillator,
            config.multiplier,
            config.randomizer,
            config.spreader
        )
    )


@st.cache_data(
    max_entries=1024,
    show_spinner='Calculating distribution',
    persist=True,
    hash_funcs={TimePatternConfig: _hash_config}
)
def _calculate_sample(config: TimePatternConfig) -> list[datetime]:
    """Calculate sample for specified `config`. If finite sample cannot
    be calculated then empty list is returned and corresponding
    notification is displayed."""
    pattern = TimePatternInputPlugin(config)
    try:
        data = []
        pattern.sample(lambda ts: data.append(ts))
    except InputPluginRuntimeError as e:
        default_notifier(
            message=(
                'Skip distribution calculation '
                f'for pattern "{config.label}": {e}'
            ),
            level=NotificationLevel.WARNING
        )
        return []
    return data


class DistributionHistogram(BaseComponent):
    """Component for visualizing time patterns distribution."""

    _SHOW_PROPS = {
        'configs': Iterable[TimePatternConfig],
        'colors': Iterable[str],
        'bins_count': int,
        'downsampling': bool,
        'downsampling_span': str
    }

    def _show(self) -> None:
        configs: Iterable[TimePatternConfig] = self._props['configs']
        bins_count: int = self._props['bins_count']
        colors: Iterable[str] = self._props['colors']
        downsampling: bool = self._props['downsampling']
        downsampling_span: str = self._props['downsampling_span']

        series: list[pd.DataFrame] = []
        labels: list[str] = []
        total_events = 0

        for config in configs:
            sample = _calculate_sample(config)
            ser = pd.Series(1, index=sample)
            total_events += ser.size

            if downsampling:
                ser = ser.resample(rule=downsampling_span).sum()

            series.append(ser)
            labels.append(config.label)

        fig = go.Figure()

        for ser, label, color in zip(series, labels, colors):
            fig.add_trace(
                go.Histogram(
                    x=ser.index,
                    y=ser.values,
                    histfunc='sum',
                    name=label,
                    nbinsx=bins_count,
                    marker_color=color
                )
            )

        fig.update_layout(barmode='stack')
        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns([8, 2])
        col1.text(f'Total events: {total_events}')
        col2.button(
            'Update',
            use_container_width=True,
            key=self._wk.get_ephemeral(),
            on_click=_calculate_sample.clear
        )
