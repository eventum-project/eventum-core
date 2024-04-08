import streamlit as st

from eventum.studio.components.component import BaseComponent


class TemplateStateViewer(BaseComponent):
    """Component for displaying template state."""

    def _show(self) -> None:
        st.caption('State')
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.caption('Locals')
            st.write({'some_local_var': 1})

        with col2:
            st.caption('Shared')
            st.write({'globally_available': 'yes it is'})

        with col3:
            st.caption('Subprocesses triggering')
            st.write({'triggered': True})

        _, col2 = st.columns([3, 1])
        col2.button('Clear state', use_container_width=True)
