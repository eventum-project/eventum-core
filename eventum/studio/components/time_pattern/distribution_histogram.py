from datetime import datetime
from typing import Iterable

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
def _calculate_distribution(config: TimePatternConfig) -> list[datetime]:
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
        'bins_count': int
    }

    def _show(self) -> None:
        configs: Iterable[TimePatternConfig] = self._props['configs']
        bins_count: int = self._props['bins_count']
        colors: Iterable[str] = self._props['colors']

        samples: list[list[datetime]] = []
        labels: list[str] = []

        for config in configs:
            sample = _calculate_distribution(config)
            samples.append(sample)
            labels.append(config.label)

        total_events = 0
        fig = go.Figure()

        for sample, label, color in zip(samples, labels, colors):
            fig.add_trace(
                go.Histogram(
                    x=sample,
                    name=label,
                    nbinsx=bins_count,
                    marker_color=color
                )
            )
            total_events += len(sample)

        fig.update_layout(barmode='stack')
        st.plotly_chart(fig, use_container_width=True)
        st.text(f'Total events: {total_events}')
