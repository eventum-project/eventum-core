from typing import Any, Callable, Optional

import streamlit as st
from eventum.repository.manage import (ContentReadError, ContentUpdateError,
                                       get_template_filenames, load_template,
                                       save_template)
from eventum.studio.components.component import (BaseComponent,
                                                 ComponentActionError)
from eventum.studio.notifiers import NotificationLevel, default_notifier


class TemplateConfigurator(BaseComponent):
    """Component for controlling configuration of template."""

    _SHOW_PROPS = {
        'get_content_callback': Callable[[], str],
        'set_content_callback': Callable[[str], Any]
    }

    def _init_state(self):
        self._session_state['is_empty'] = True
        self._session_state['template_filename'] = ''
        self._session_state['is_saved'] = False

    def _show_manage_buttons(self):
        is_empty = self._session_state['is_empty']

        st.button(
            'Create new',
            key=self._wk.get_ephemeral(),
            disabled=not is_empty,
            on_click=self._add,
            use_container_width=True
        )
        col1, col2 = st.columns([7, 3])

        selected_template = col1.selectbox(
            'Template',
            options=get_template_filenames(),
            key=self._wk('template_selected_for_load'),
            label_visibility='collapsed',
            disabled=not is_empty
        )

        col2.button(
            'Load',
            key=self._wk.get_ephemeral(),
            disabled=(
                not is_empty
                or not selected_template
            ),
            on_click=lambda: self._load(
                filename=selected_template   # type: ignore
            ),
            use_container_width=True,
        )

        if not is_empty:
            st.write('*:grey[Template is added]*')

    def _show_manage_section(self) -> None:
        st.header('General')
        st.text_input(
            'File name',
            key=self._wk('template_filename'),
            disabled=self._session_state['is_saved']
        )

        if self._session_state['is_saved']:
            st.button(
                'Update',
                key=self._wk.get_ephemeral(),
                on_click=lambda: self._save(overwrite=True),
                use_container_width=True,
            )
        else:
            st.button(
                'Save',
                key=self._wk.get_ephemeral(),
                on_click=self._save,
                use_container_width=True,
            )
        st.button(
            'Delete',
            key=self._wk.get_ephemeral(),
            on_click=self._clear,
            use_container_width=True,
            type='primary',
        )

    def _show(self):
        st.title('Template')
        if self._session_state['is_empty']:
            st.markdown(
                (
                    '<div style="text-align: center; color: grey;">'
                    'No template. Create or load one.'
                    '</div>'
                ),
                unsafe_allow_html=True
            )
        else:
            template_filename = self._session_state['template_filename']
            label = template_filename if template_filename else 'New template'

            with st.expander(label, expanded=True):
                self._show_manage_section()

        st.divider()
        self._show_manage_buttons()

    def _add(
        self,
        initial_state: Optional[str] = None,
        template_filename: Optional[str] = None,
        notify_callback: Callable[
            [str, NotificationLevel], None
        ] = default_notifier
    ) -> None:
        """Add new template to configurator."""
        if not self._session_state['is_empty']:
            raise ComponentActionError('Template is already added')

        if initial_state is None:
            initial_state = ''

        try:
            self._props['set_content_callback'](initial_state)
        except Exception as e:
            notify_callback(
                f'Failed to present content of template: {e}',
                NotificationLevel.ERROR
            )
            return

        if template_filename is not None:
            self._session_state['is_saved'] = True
            self._session_state['template_filename'] = template_filename

        self._session_state['is_empty'] = False

    def _load(
        self,
        filename: str,
        notify_callback: Callable[
            [str, NotificationLevel], None
        ] = default_notifier
    ) -> None:
        """Load selected template from repository to configurator."""
        try:
            template_content = load_template(filename)
        except ContentReadError as e:
            notify_callback(str(e), NotificationLevel.ERROR)
            return

        self._add(
            initial_state=template_content,
            template_filename=filename
        )

    def _clear(self) -> None:
        """Clear template configurator."""
        self._session_state['is_empty'] = True
        self._session_state['is_saved'] = False
        self._session_state['template_filename'] = ''
        self._props['set_content_callback']('')

    def _save(
        self,
        overwrite: bool = False,
        notify_callback: Callable[
            [str, NotificationLevel], None
        ] = default_notifier
    ):
        """Save current template to repository."""
        try:
            content = self._props['get_content_callback']()
        except Exception as e:
            notify_callback(
                f'Failed to get template content: {e}',
                NotificationLevel.ERROR
            )
            return

        try:
            save_template(
                content=content,
                path=self._session_state['template_filename'],
                overwrite=overwrite
            )
        except ContentUpdateError as e:
            notify_callback(f'Failed to save: {e}', NotificationLevel.ERROR)
            return

        self._session_state['is_saved'] = True
        notify_callback('Saved in repository', NotificationLevel.SUCCESS)
