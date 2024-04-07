import streamlit as st
from eventum.studio.components.component import persist_state
from eventum.studio.components.template_configurator import \
    TemplateConfigurator

from streamlit_elements import elements, editor, sync, lazy, event
from eventum.studio.notifiers import NotificationLevel, default_notifier


persist_state()

st.set_page_config(
    page_title='Eventum Studio',
    layout='wide',
    initial_sidebar_state='expanded'
)

if 'template_content' not in st.session_state:
    st.session_state['template_content'] = ''

configurator = TemplateConfigurator(
    props={
        'get_content_callback': lambda: st.session_state['template_content'],
        'set_content_callback': (
            lambda content:
            st.session_state.__setitem__('template_content', content)
        )
    }
)
with st.sidebar:
    configurator.show()

editor_tab, debugger_tab = st.tabs(['Editor', 'Debugger'])


def handle_ctrl_s():
    sync()
    default_notifier(
        message='Template is updated',
        level=NotificationLevel.INFO
    )


with editor_tab:
    st.caption(
        'Template content',
        help='Use `Ctrl+S` to commit changes after editing'
    )
    with elements('editor'):
        event.Hotkey(
            sequence='ctrl+s',
            callback=handle_ctrl_s,
            bindInputs=True,
            overrideDefault=True
        )

        editor.Monaco(
            theme='vs-dark',
            language='javascript',
            value=st.session_state['template_content'],
            onChange=lazy(sync('template_content')),
            options={
                'readOnly': configurator.is_empty,
                'cursorSmoothCaretAnimation': True
            },
            height=520,
        )

with debugger_tab:
    st.button('Clear locals')
    st.button('Clear shared')
    st.button('Run')
