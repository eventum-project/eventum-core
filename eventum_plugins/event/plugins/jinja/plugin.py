import os
from copy import copy
from typing import Any, MutableMapping, TypedDict

from jinja2 import (BaseLoader, Environment, FileSystemLoader, Template,
                    TemplateError, TemplateNotFound, TemplateRuntimeError,
                    TemplateSyntaxError)
from pytz import BaseTzInfo

import eventum_plugins.event.plugins.jinja.modules as modules
from eventum_plugins.event.base.plugin import BaseEventPlugin
from eventum_plugins.event.plugins.jinja.config import (
    JinjaEventConfig, TemplateConfigForGeneralModes)
from eventum_plugins.event.plugins.jinja.context import EventContext
from eventum_plugins.event.plugins.jinja.module_provider import ModuleProvider
from eventum_plugins.event.plugins.jinja.sample_reader import SampleReader
from eventum_plugins.event.plugins.jinja.state import (MultiProcessState,
                                                       SingleThreadState)
from eventum_plugins.event.plugins.jinja.subprocess_runner import \
    SubprocessRunner
from eventum_plugins.event.plugins.jinja.template_pickers import \
    get_picker_class
from eventum_plugins.exceptions import (PluginConfigurationError,
                                        PluginRuntimeError)


class ProduceParams(TypedDict):
    """Params for `produce` method of `JinjaEventPlugin`.

    Attributes
    ----------
    timestamp : str
        Timestamp of event

    timezone : BaseTzInfo
        Timezone of timestamp

    tags : tuple[str, ...]
        Tags from input plugin that generated timestamp

    """
    timestamp: str
    tags: tuple[str, ...]
    timezone: BaseTzInfo


class JinjaEventPlugin(BaseEventPlugin, config_cls=JinjaEventConfig):
    """Event plugin for producing events using Jinja template engine."""

    _JINJA_EXTENSIONS = ('jinja2.ext.do', 'jinja2.ext.loopcontrols')

    def __init__(
        self,
        config: JinjaEventConfig,
        composed_state: MultiProcessState,
        templates_loader: BaseLoader | None = None,
    ) -> None:
        self._config = config

        self._env = Environment(
            loader=templates_loader or FileSystemLoader(os.getcwd()),
            extensions=self._JINJA_EXTENSIONS
        )

        self._samples = SampleReader(self._config.root.samples)
        self._module_provider = ModuleProvider(modules.__name__)
        self._subprocess_runner = SubprocessRunner()
        self._shared_state = SingleThreadState()
        self._composed_state = composed_state

        self._env.globals['params'] = self._config.root.params
        self._env.globals['samples'] = self._samples
        self._env.globals['module'] = self._module_provider
        self._env.globals['subprocess'] = self._subprocess_runner
        self._env.globals['shared'] = self._shared_state
        self._env.globals['composed'] = self._composed_state

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

        Picker = get_picker_class(self._config.root.mode)
        try:
            self._template_picker = Picker(
                config=self._template_configs,
                common_config=self._config.root.get_picking_common_fields()
            )
        except ValueError as e:
            raise PluginConfigurationError(
                f'Failed to configure template picker: {e}'
            )

        self._event_context: EventContext = {
            'timestamp': '',                                        # ephemeral
            'tags': tuple(),                                        # ephemeral
            'locals': next(iter(self._template_states.values())),   # ephemeral
            'shared': self._shared_state,
            'composed': self._composed_state,
        }

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
        template_path : str
            Name of the template to load

        globals : MutableMapping[str, Any] | None, default=None
            Parameter `globals` of `Environment.get_template` method

        Returns
        -------
        Template
            Loaded template
        """
        try:
            return self._env.get_template(name, globals=globals)
        except TemplateNotFound as e:
            raise PluginConfigurationError(
                f'Failed to load template: {e}'
            ) from e
        except TemplateSyntaxError as e:
            raise PluginConfigurationError(
                f'Bad syntax in template "{name}": {e}'
            ) from e
        except TemplateError as e:
            raise PluginConfigurationError(
                f'Error in template "{name}": {e}'
            ) from e

    def produce(self, params: ProduceParams) -> list[str]:
        self._event_context['timestamp'] = params['timestamp']
        self._event_context['tags'] = params['tags']

        picked_aliases = self._template_picker.pick(**self._event_context)

        rendered = []
        for alias in picked_aliases:
            locals = self._template_states[alias]
            template = self._templates[alias]

            try:
                event = template.render(locals=locals, **params)
            except TemplateRuntimeError as e:
                raise PluginRuntimeError(
                    f'Failed to render template "{alias}" '
                    f'({template.name}): {e}'
                )
            rendered.append(event)
        else:
            # set locals state in event context to alias of most recently
            # rendered template
            self._event_context['locals'] = self._template_states[alias]

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
    def composed_state(self) -> MultiProcessState:
        """Composed state of templates."""
        return self._composed_state

    @property
    def subprocess_runner(self) -> SubprocessRunner:
        """Subprocess runner."""
        return self._subprocess_runner
