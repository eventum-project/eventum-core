import streamlit as st
from eventum.studio.components.component import persist_state
from eventum.studio.components.template_configurator import \
    TemplateConfigurator

from streamlit_elements import elements, editor


persist_state()

st.set_page_config(
    page_title='Eventum Studio',
    layout='wide',
    initial_sidebar_state='expanded'
)

if 'template_content' not in st.session_state:
    st.session_state['template_content'] = ''

configs_list = TemplateConfigurator(
    props={
        'get_content_callback': (
            lambda: st.session_state['template_content']
        ),
        'set_content_callback': (
            lambda content:
            st.session_state.__setitem__('template_content', content)
        )
    }
)
with st.sidebar:
    configs_list.show()


with elements('editor'):
    editor.Monaco(
        theme='vs-dark',
        language='javascript',
        value=st.session_state['template_content'],
        onChange=(
            lambda content:
            st.session_state.__setitem__('template_content', content)
        ),
        height=580,
    )
