import streamlit as st
from eventum.studio.components.component import persist_state
from eventum.studio.components.time_pattern.configurator_list import \
    ConfiguratorList
from eventum.studio.components.time_pattern.distribution_histogram import \
    DistributionHistogram

persist_state()

st.set_page_config(
    page_title='Eventum Studio',
    layout='wide',
    initial_sidebar_state='expanded'
)

configs_list = ConfiguratorList()
with st.sidebar:
    configs_list.show()

col1, col2 = st.columns([1, 1])
bins_count = col1.radio('Bins count', [100, 1000, 10000], horizontal=True)

st.divider()

DistributionHistogram(
    props={
        'configs': configs_list.get_pattern_configs(),
        'colors': configs_list.get_pattern_colors(),
        'bins_count': bins_count
    }
).show()
