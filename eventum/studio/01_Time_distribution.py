import streamlit as st
import plotly.graph_objects as go

from eventum.core.plugins.input.base import InputPluginRuntimeError
from eventum.core.plugins.input.time_pattern import TimePatternInputPlugin
from eventum.studio.components.component import persist_state
from eventum.studio.components.time_pattern_adjusters_list import \
    TimePatternAdjustersList
from eventum.studio.notifiers import NotificationLevel, default_notifier

persist_state()

st.set_page_config(
    page_title="Eventum Studio",
)

patterns_list = TimePatternAdjustersList()
with st.sidebar:
    patterns_list.show()

configs = patterns_list.get_pattern_configs()
labels = patterns_list.get_pattern_labels()
colors = patterns_list.get_pattern_colors()

patterns = [TimePatternInputPlugin(config) for config in configs]

fig = go.Figure()
for pattern, label, color in zip(patterns, labels, colors):
    data = []
    try:
        pattern.sample(lambda ts: data.append(ts))
    except InputPluginRuntimeError as e:
        default_notifier(
            message=f'Pattern "{label}" is not visualized: {e}',
            level=NotificationLevel.ERROR
        )
    fig.add_trace(
        go.Histogram(
            x=data,
            name=label,
            marker_color=color,
            nbinsx=100
        )
    )

fig.update_layout(barmode='stack')

st.plotly_chart(fig, use_container_width=True)
