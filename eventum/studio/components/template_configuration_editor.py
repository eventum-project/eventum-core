from typing import Callable
import streamlit as st
from streamlit_elements import editor, elements, event, lazy

from eventum.studio.components.component import BaseComponent
from eventum.studio.components.sample_explorer import SampleExplorer
from eventum.studio.notifiers import NotificationLevel, default_notifier


class TemplateConfigurationEditor(BaseComponent):
    """Component for editing configuration for template."""

    _SHOW_PROPS = {
        'on_change': Callable[[str], None]
    }

    _DEFAULT_CONTENT = (
        'params: { }\n'
        'samples: { }\n'
        'subprocesses: { }\n'
    )

    def _init_state(self) -> None:
        return super()._init_state()

    def _show(self) -> None:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.caption('Configuration')

            with elements(self._wk('configuration_editor')):
                event.Hotkey(
                    sequence='ctrl+s',
                    callback=(
                        lambda:
                        default_notifier(
                            message='Configuration is updated',
                            level=NotificationLevel.INFO
                        )
                    ),
                    bindInputs=True,
                    overrideDefault=True
                )

                editor.Monaco(
                    theme='vs-dark',
                    language='yaml',
                    height=670,
                    value=self._DEFAULT_CONTENT,
                    onChange=lazy(self._props['on_change']),
                    options={
                        'cursorSmoothCaretAnimation': True,
                        'tabSize': 2
                    }
                )

        with col2:
            SampleExplorer(
                widget_keys_context=self._wk,
                props={'display_size': 15}
            ).show()
