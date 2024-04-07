from datetime import datetime

import streamlit as st
from eventum.core import settings
from eventum.studio.components.component import persist_state
from eventum.studio.components.time_pattern_configurator_list import \
    TimePatternConfiguratorList
from eventum.studio.components.time_pattern_distribution_histogram import \
    TimePatternDistributionHistogram
from eventum.studio.components.span_input import SpanInput

persist_state()

st.set_page_config(
    page_title='Eventum Studio',
    layout='wide',
    initial_sidebar_state='expanded'
)

configs_list = TimePatternConfiguratorList()
with st.sidebar:
    configs_list.show()

col1, col2 = st.columns([1, 1])


with col1:
    span = SpanInput()
    span.show()

col2.markdown(
    '<div style="text-align: right">'
    f'Local time zone: <code>{datetime.now().astimezone().tzinfo}</code>'
    '</div>',
    unsafe_allow_html=True
)

col2.markdown(
    '<div style="text-align: right">'
    f'Sample time zone: <code>{settings.TIMEZONE}</code>'
    '</div>',
    unsafe_allow_html=True
)

st.divider()

TimePatternDistributionHistogram(
    props={
        'configs': configs_list.get_pattern_configs(),
        'colors': configs_list.get_pattern_colors(),
        'use_custom_span': not span.is_auto(),
        'span_expression': span.get_expression()
    }
).show()
