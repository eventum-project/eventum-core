import plotly.graph_objects as go
import streamlit as st
from eventum.studio.calculations import calculate_distribution
from eventum.studio.components.component import persist_state
from eventum.studio.components.time_pattern_adjusters_list import \
    TimePatternAdjustersList

persist_state()

st.set_page_config(
    page_title="Eventum Studio",
)

patterns_list = TimePatternAdjustersList()
with st.sidebar:
    patterns_list.show()

configs = patterns_list.get_pattern_configs()
colors = patterns_list.get_pattern_colors()

fig = go.Figure()
for config, color in zip(configs, colors):
    fig.add_trace(
        go.Histogram(
            x=calculate_distribution(config),
            name=config.label,
            nbinsx=100,
            marker_color=color
        )
    )

fig.update_layout(barmode='stack')

st.plotly_chart(fig, use_container_width=True)
