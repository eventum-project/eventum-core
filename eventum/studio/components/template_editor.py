from typing import Callable

import streamlit as st
from streamlit_elements import editor, elements, event, lazy

from eventum.studio.components.component import BaseComponent
from eventum.studio.notifiers import NotificationLevel, default_notifier


class TemplateEditor(BaseComponent):
    """Component for editing template content."""

    _SHOW_PROPS = {
        'content': str,
        'read_only': bool,
        'on_change': Callable[[str], None]
    }

    def _show(self) -> None:
        st.caption(
            'Template content',
            help='Use `Ctrl+S` to commit changes after editing'
        )
        with elements(self._wk('template_editor')):
            event.Hotkey(
                sequence='ctrl+s',
                callback=(
                    lambda:
                    default_notifier(
                        message='Template is updated',
                        level=NotificationLevel.INFO
                    )
                ),
                bindInputs=True,
                overrideDefault=True
            )

            editor.Monaco(
                theme='vs-dark',
                language='javascript',
                value=self._props['content'],
                onChange=lazy(self._props['on_change']),
                options={
                    'readOnly': self._props['read_only'],
                    'cursorSmoothCaretAnimation': True
                },
                height=670,
            )
