import os
from copy import copy
from datetime import datetime
from typing import Any, MutableMapping, NotRequired, Required

from jinja2 import (BaseLoader, Environment, FileSystemLoader, Template,
                    TemplateError, TemplateNotFound, TemplateSyntaxError)

import eventum.plugins.event.plugins.jinja.modules as modules
from eventum.plugins.event.base.plugin import (EventPlugin, EventPluginParams,
                                               ProduceParams)
from eventum.plugins.event.plugins.jinja.config import (
    JinjaEventPluginConfig, TemplateConfigForGeneralModes)
from eventum.plugins.event.plugins.jinja.context import EventContext
from eventum.plugins.event.plugins.jinja.module_provider import ModuleProvider
from eventum.plugins.event.plugins.jinja.sample_reader import (SampleLoadError,
                                                               SampleReader)
from eventum.plugins.event.plugins.jinja.state import (MultiProcessState,
                                                       SingleThreadState)
from eventum.plugins.event.plugins.jinja.subprocess_runner import \
    SubprocessRunner
from eventum.plugins.event.plugins.jinja.template_pickers import \
    get_picker_class
from eventum.plugins.exceptions import (PluginConfigurationError,
                                        PluginRuntimeError)


class JinjaEventPluginParams(EventPluginParams):
    """Parameters for jinja event plugin.

    Attributes
    ----------
    global_state : MultiProcessState
        Global state for cross generators communication

    templates_loader : BaseLoader
        Templates loader, if `None` is provided then default
        (FileSystemLoader) loader is used
    """
    global_state: Required[MultiProcessState]
    templates_loader: NotRequired[BaseLoader]


class JinjaEventPlugin(
    EventPlugin[JinjaEventPluginConfig, JinjaEventPluginParams]
):
    """Event plugin for producing events using Jinja template engine."""

    _JINJA_EXTENSIONS = ('jinja2.ext.do', 'jinja2.ext.loopcontrols')

    def __init__(
        self,
        config: JinjaEventPluginConfig,
        params: JinjaEventPluginParams
    ) -> None:
        super().__init__(config, params)

        self._env = Environment(
            loader=(
                params.get('templates_loader', None)
                or FileSystemLoader(os.getcwd())
            ),
            extensions=self._JINJA_EXTENSIONS
        )

        try:
            self._samples = SampleReader(self._config.root.samples)
        except SampleLoadError as e:
            raise PluginConfigurationError(
                str(e),
                context=dict(self.instance_info)
            ) from None

        if self._config.root.samples:
            self._logger.info('Samples are loaded')

        self._module_provider = ModuleProvider(modules.__name__)
        self._subprocess_runner = SubprocessRunner()
        self._shared_state = SingleThreadState()

        with self.required_params():
            self._global_state = params['global_state']

        self._env.globals['params'] = self._config.root.params
        self._env.globals['samples'] = self._samples
        self._env.globals['module'] = self._module_provider
        self._env.globals['subprocess'] = self._subprocess_runner
        self._env.globals['shared'] = self._shared_state
        self._env.globals['globals'] = self._global_state

        self._template_configs = self._get_template_configs_as_dict()
        self._template_states = {
            alias: SingleThreadState()
            for alias in self._template_configs.keys()
        }
        self._templates = {
            alias: self._load_template(
                name=conf.template,
                globals={'locals': self._template_states[alias]}
            )
            for alias, conf in self._template_configs.items()
        }
        self._logger.info('Templates are loaded')

        try:
            Picker = get_picker_class(self._config.root.mode)

            self._template_picker = Picker(
                config=self._template_configs,
                common_config=self._config.root.get_picking_common_fields()
            )
        except ValueError as e:
            raise PluginConfigurationError(
                'Failed to configure template picker',
                context=dict(self.instance_info, reason=str(e))
            )

        self._event_context = EventContext(
            timestamp=datetime.now(),   # ephemeral
            tags=tuple(),               # ephemeral
            locals=next(iter(self._template_states.values())),  # ephemeral
            shared=self._shared_state,
            globals=self._global_state
        )

    def _get_template_configs_as_dict(
        self
    ) -> dict[str, TemplateConfigForGeneralModes]:
        """Get template configs as dict.

        Returns
        -------
        dict[str, TemplateConfigForGeneralModes]
            Mapping with template configurations in values and their
            aliases in keys
        """
        templates: dict[str, TemplateConfigForGeneralModes] = dict()

        for template_item in self._config.root.templates:
            template_alias, template_conf = next(iter(template_item.items()))
            templates[template_alias] = template_conf

        return templates

    def _load_template(
        self,
        name: str,
        globals: MutableMapping[str, Any] | None = None
    ) -> Template:
        """Load template using current environment.

        Parameters
        ----------
        name : str
            Name of the template to load

        globals : MutableMapping[str, Any] | None, default=None
            Parameter `globals` of `Environment.get_template` method

        Returns
        -------
        Template
            Loaded template

        Raises
        ------
        PluginConfigurationError
            If template cannot be loaded
        """
        try:
            return self._env.get_template(name, globals=globals)
        except TemplateNotFound:
            raise PluginConfigurationError(
                'Failed to load template',
                context=dict(
                    self.instance_info,
                    reason='Template is not found',
                    file_name=name
                )
            ) from None
        except TemplateSyntaxError as e:
            raise PluginConfigurationError(
                'Failed to load template',
                context=dict(
                    self.instance_info,
                    reason=f'Bad syntax in template: {e}',
                    file_name=name
                )
            ) from e
        except TemplateError as e:
            raise PluginConfigurationError(
                'Failed to load template',
                context=dict(
                    self.instance_info,
                    reason=f'Template error: {e}',
                    file_name=name
                )
            ) from e

    def produce(self, params: ProduceParams) -> list[str]:
        self._event_context['timestamp'] = params['timestamp']
        self._event_context['tags'] = params['tags']

        picked_aliases = self._template_picker.pick(self._event_context)

        rendered: list[str] = []
        for alias in picked_aliases:
            template = self._templates[alias]

            try:
                event = template.render(
                    timestamp=params['timestamp'],
                    tags=params['tags'],
                    locals=self._template_states[alias]
                )
            except Exception as e:
                raise PluginRuntimeError(
                    'Failed to render template',
                    context=dict(
                        self.instance_info,
                        reason=str(e),
                        template_alias=alias
                    )
                )
            rendered.append(event)
        else:
            locals = self._template_states[alias]   # type: ignore
            self._event_context['locals'] = locals

        return rendered

    @property
    def local_states(self) -> dict[str, SingleThreadState]:
        """Local states of templates."""
        return copy(self._template_states)

    @property
    def shared_state(self) -> SingleThreadState:
        """Shared state of templates."""
        return self._shared_state

    @property
    def global_state(self) -> MultiProcessState:
        """Global state of templates."""
        return self._global_state

    @property
    def subprocess_runner(self) -> SubprocessRunner:
        """Subprocess runner."""
        return self._subprocess_runner
