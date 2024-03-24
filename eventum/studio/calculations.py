from datetime import datetime

import streamlit as st
from eventum.core.models.time_pattern_config import TimePatternConfig
from eventum.core.plugins.input.base import InputPluginRuntimeError
from eventum.core.plugins.input.time_pattern import TimePatternInputPlugin
from eventum.studio.notifiers import NotificationLevel, default_notifier


def hash_config(config: TimePatternConfig) -> int:
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
    hash_funcs={TimePatternConfig: hash_config}
)
def calculate_distribution(config: TimePatternConfig) -> list[datetime]:
    pattern = TimePatternInputPlugin(config)
    try:
        data = []
        pattern.sample(lambda ts: data.append(ts))
    except InputPluginRuntimeError as e:
        default_notifier(
            message=f'Pattern "{config.label}" is not visualized: {e}',
            level=NotificationLevel.ERROR
        )
        return []
    return data
