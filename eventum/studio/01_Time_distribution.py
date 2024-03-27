from datetime import datetime

import streamlit as st

from eventum.studio.components.component import persist_state
from eventum.studio.components.time_pattern.configurator_list import \
    ConfiguratorList
from eventum.studio.components.time_pattern.distribution_histogram import \
    DistributionHistogram
from eventum.studio.components.time_pattern.downsampling_input import \
    DownsamplingInput

persist_state()

st.set_page_config(
    page_title='Eventum Studio',
    layout='wide',
    initial_sidebar_state='expanded'
)

configs_list = ConfiguratorList()
with st.sidebar:
    configs_list.show()

col1, col2, col3 = st.columns([1, 1, 1])
bins_count = col1.radio(
    label='Bins count',
    options=[100, 1000, 10000],
    horizontal=True
)

with col2:
    downsampling = DownsamplingInput().show()

col3.markdown(
    '<div style="text-align: right">'
    f'Time zone: <code>{datetime.now().astimezone().tzinfo}</code>'
    '</div>',
    unsafe_allow_html=True
)

st.divider()

DistributionHistogram(
    props={
        'configs': configs_list.get_pattern_configs(),
        'colors': configs_list.get_pattern_colors(),
        'bins_count': bins_count
    }
).show()
