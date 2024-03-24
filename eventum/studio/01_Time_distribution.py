import streamlit as st
import plotly.graph_objects as go

from eventum.core.plugins.input.time_pattern import TimePatternInputPlugin
from eventum.studio.components.component import persist_state
from eventum.studio.components.time_pattern_adjusters_list import \
    TimePatternAdjustersList

STREAMLIT_COLORS = {
    'blue': '#60b4ff',
    'green': '#3dd56d',
    'orange': '#ffbd45',
    'red': '#ff4b4b',
    'violet': '#b27eff'
}

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
    data = pattern.interactive_sample(periods_count=3)
    fig.add_trace(
        go.Histogram(
            x=data,
            name=label,
            marker_color=STREAMLIT_COLORS[color],
            nbinsx=100
        )
    )

fig.update_layout(barmode='stack')

st.plotly_chart(fig, use_container_width=True)
