import streamlit as st
from streamlit_elements import editor, elements

from eventum.studio.components.component import BaseComponent


class TemplateConfigurationEditor(BaseComponent):
    def _show(self) -> None:
        st.caption('Configuration')
        with elements(self._wk('configuration_editor')):
            editor.Monaco(
                theme='vs-dark',
                language='yaml',
                height=650,
                value='{ }'
            )
