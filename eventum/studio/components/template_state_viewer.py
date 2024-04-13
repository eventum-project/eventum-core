import streamlit as st

from eventum.studio.components.component import BaseComponent


class TemplateStateViewer(BaseComponent):
    """Component for displaying template state."""

    _SHOW_PROPS = {
        'local_vars': dict,
        'shared_vars': dict,
        'subprocess_commands_history': tuple[tuple[int, str]]
    }

    def _show(self) -> None:
        st.caption('State')
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.caption('Locals')
            st.write(self._props['local_vars'])

        with col2:
            st.caption('Shared')
            st.write(self._props['shared_vars'])

        with col3:
            st.caption('Subprocess commands history')
            st.dataframe(
                data=self._props['subprocess_commands_history'],
                use_container_width=True,
                hide_index=True,
                column_config={1: "#", 2: "Command"}
            )

        _, col2 = st.columns([3, 1])
        col2.button('Clear state', use_container_width=True)
