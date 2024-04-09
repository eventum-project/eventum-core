import streamlit as st
from streamlit_elements import editor, elements

from eventum.studio.components.component import BaseComponent


class TemplateRenderer(BaseComponent):
    """Component for rendering templates."""

    _SHOW_PROPS = {
        'template_content': str
    }

    def _show(self) -> None:
        st.caption('Template rendering preview')
        with elements(self._wk('template_renderer')):
            editor.MonacoDiff(
                theme='vs-dark',
                language='javascript',
                original=self._props['template_content'],
                modified='',
                options={
                    'readOnly': True,
                    'cursorSmoothCaretAnimation': True
                },
                height=600,
            )

        _, col2 = st.columns([3, 1])
        col2.button('Render', use_container_width=True, type='primary')
