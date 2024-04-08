import streamlit as st
from streamlit_elements import sync

from eventum.studio.components.component import persist_state
from eventum.studio.components.template_editor import TemplateEditor
from eventum.studio.components.template_manager import TemplateManager
from eventum.studio.components.template_renderer import TemplateRenderer
from eventum.studio.components.template_state_viewer import TemplateStateViewer

persist_state()

st.set_page_config(
    page_title='Eventum Studio',
    layout='wide',
    initial_sidebar_state='expanded'
)

if 'template_content' not in st.session_state:
    st.session_state['template_content'] = ''

manager = TemplateManager(
    props={
        'get_content_callback': lambda: st.session_state['template_content'],
        'set_content_callback': (
            lambda content:
            st.session_state.__setitem__('template_content', content)
        )
    }
)
editor = TemplateEditor(
    props={
        'content': st.session_state['template_content'],
        'read_only': manager.is_empty,
        'on_change': sync('template_content')
    }
)
renderer = TemplateRenderer(
    props={
        'template_content': st.session_state['template_content']
    }
)
state_viewer = TemplateStateViewer()

with st.sidebar:
    manager.show()

editor_tab, render_tab, state_tab = st.tabs(['Editor', 'Rendering', 'State'])

with editor_tab:
    editor.show()

with render_tab:
    renderer.show()

with state_tab:
    state_viewer.show()
