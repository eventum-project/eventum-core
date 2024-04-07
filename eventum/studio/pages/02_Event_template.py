import streamlit as st
from eventum.studio.components.component import persist_state
from eventum.studio.components.template_configurator import \
    TemplateConfigurator

persist_state()

st.set_page_config(
    page_title='Eventum Studio',
    layout='wide',
    initial_sidebar_state='expanded'
)

configs_list = TemplateConfigurator(
    props={
        'get_content_callback': lambda: st.session_state['test'],
        'set_content_callback': lambda content: st.session_state.__setitem__('test', content)
    }
)
with st.sidebar:
    configs_list.show()


st.text_area(label='Template content', key='test')
