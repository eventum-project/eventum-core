import os
from datetime import datetime

import streamlit as st
import yaml
from jinja2 import Environment, FileSystemLoader
from pydantic import ValidationError
from streamlit_elements import editor, elements

import eventum.core.models.application_config as models
from eventum.core.plugins.event.base import (EventPluginConfigurationError,
                                             EventPluginRuntimeError)
from eventum.core.plugins.event.jinja import JinjaEventPlugin
from eventum.core.settings import TIMESTAMP_FIELD_NAME, TIMEZONE
from eventum.studio.components.component import BaseComponent
from eventum.studio.notifiers import NotificationLevel, default_notifier
from eventum.utils.fs import write_temporary_file


class TemplateRenderer(BaseComponent):
    """Component for rendering templates."""

    _SHOW_PROPS = {
        'template_content': str,
        'configuration_content': str,
    }

    def _init_state(self) -> None:
        self._session_state['rendering_result'] = ''

    def _render(self) -> None:
        """Render currently set template content."""

        content = self._props['configuration_content']

        try:
            config_data = yaml.load(content, yaml.Loader)
        except yaml.YAMLError as e:
            default_notifier(
                message=(
                    'Failed to render template due to configuration '
                    f'parse failure: {e}'
                ),
                level=NotificationLevel.ERROR
            )
            return

        template_path = write_temporary_file(self._props['template_content'])
        base_dir, template_name = os.path.split(template_path)

        try:
            config = models.JinjaEventConfig(
                mode=models.TemplatePickingMode.ALL,
                templates={
                    'template': models.TemplateConfig(template=template_name)
                },
                **config_data
            )
        except (TypeError, ValidationError) as e:
            default_notifier(
                message=(
                    'Failed to render template due to invalid '
                    f'configuration: {e}'
                ),
                level=NotificationLevel.ERROR
            )
            return

        timestamp = datetime.now().astimezone(TIMEZONE)
        timestamp = timestamp.replace(tzinfo=None).isoformat()
        params = {TIMESTAMP_FIELD_NAME: timestamp}

        try:
            result = JinjaEventPlugin(
                config=config,
                environment=Environment(
                    loader=FileSystemLoader(searchpath=base_dir),
                    autoescape=False
                )
            ).render(**params)
        except EventPluginConfigurationError as e:
            default_notifier(
                message=(
                    'Failed to render template due to invalid '
                    f'configuration: {e}'
                ),
                level=NotificationLevel.ERROR
            )
            return
        except EventPluginRuntimeError as e:
            default_notifier(
                message=(
                    f'Failed to render template due to rendering error {e}'
                ),
                level=NotificationLevel.ERROR
            )
            return

        self._session_state['rendering_result'] = result.pop()

    def _show(self) -> None:
        st.caption('Template rendering preview')
        with elements(self._wk('template_renderer')):
            editor.MonacoDiff(
                theme='vs-dark',
                language='javascript',
                original=self._props['template_content'],
                modified=self._session_state['rendering_result'],
                options={
                    'readOnly': True,
                    'cursorSmoothCaretAnimation': True
                },
                height=600,
            )

        _, col2 = st.columns([3, 1])
        col2.button(
            'Render',
            use_container_width=True,
            type='primary',
            on_click=self._render
        )
