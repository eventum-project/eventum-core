import importlib
import random
import subprocess
from collections import deque
from copy import deepcopy
from enum import StrEnum
from types import ModuleType
from typing import Any, Iterator, assert_never

from eventum_content_manager.manage import (EVENT_TEMPLATES_DIR,
                                            ContentManagementError,
                                            load_csv_sample)
from jinja2 import (BaseLoader, Environment, FileSystemLoader, Template,
                    TemplateError, TemplateNotFound, TemplateRuntimeError,
                    TemplateSyntaxError, Undefined)
from pydantic import Field, field_validator

from eventum_plugins.event.base import (BaseEventPlugin, EventPluginBaseConfig,
                                        EventPluginConfigurationError,
                                        EventPluginRuntimeError)
from eventum_plugins.utils.modules import get_module_names


class SampleType(StrEnum):
    CSV = 'csv'
    ITEMS = 'items'


class CSVSampleConfig(EventPluginBaseConfig, frozen=True):
    type: SampleType
    header: bool = False
    delimiter: str = Field(',', min_length=1)
    source: str = Field(..., pattern=r'.*\.csv')

    @field_validator('type')
    def validate_type(cls, v: Any):
        if v == SampleType.CSV:
            return v

        raise ValueError(
            f'Type must be "{SampleType.CSV}" of {SampleType}'
        )


class ItemsSampleConfig(EventPluginBaseConfig, frozen=True):
    type: SampleType
    source: tuple[str, ...] = Field(..., min_length=1)

    @field_validator('type')
    def validate_type(cls, v: Any):
        if v == SampleType.ITEMS:
            return v

        raise ValueError(
            f'Type must be "{SampleType.ITEMS}" of {SampleType}'
        )


class TemplatePickingMode(StrEnum):
    ALL = 'all'
    ANY = 'any'
    CHANCE = 'chance'
    SPIN = 'spin'


class TemplateConfig(EventPluginBaseConfig, frozen=True):
    template: str = Field(..., pattern=r'.*\.jinja')
    chance: float = Field(1.0, gt=0.0)


class JinjaEventConfig(EventPluginBaseConfig, frozen=True):
    params: dict
    samples: dict[str, ItemsSampleConfig | CSVSampleConfig]
    mode: TemplatePickingMode
    templates: dict[str, TemplateConfig] = Field(..., min_length=1)


class SubprocessManager:
    """Class for running any command in subprocess from template."""

    _HISTORY_SIZE = 10

    def __init__(self) -> None:
        self._commands_history: deque[tuple[int, str]] = deque(
            maxlen=self._HISTORY_SIZE
        )
        self._commands_counter = 1

    def _save_command_in_history(self, command: str) -> None:
        self._commands_history.append((self._commands_counter, command))
        self._commands_counter += 1

    def run(self, command: str, block: bool = False) -> str | None:
        """Start command in a subprocess. If `block` is `True` then stdout
        of command will be returned. Otherwise `None` is returned.
        """
        self._save_command_in_history(command)

        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)

        if block:
            stdout, stderr = proc.communicate()
            return stdout.decode()

        return None

    @property
    def commands_history(self) -> tuple[tuple[int, str], ...]:
        """Get history of running commands."""
        return tuple(self._commands_history)


class SubprocessManagerMock(SubprocessManager):
    def run(self, command: str, block: bool = False) -> str | None:
        self._save_command_in_history(command)

        if block:
            return '<SUBPROCESS MOCK RESULT>'

        return None


class State:
    def __init__(self) -> None:
        self._state: dict[str, Any] = dict()

    def set(self, key: str, value: Any) -> None:
        """Set variable value to state."""
        if isinstance(value, Undefined):
            value = None

        self._state[key] = value

    def get(self, key: str, default: Any | None = None) -> Any:
        """Get variable value from state. If state does not contain
        value with specified `key` then `default` value is returned.
        """
        try:
            return self._state[key]
        except KeyError:
            return default

    def as_dict(self) -> dict:
        """Get dictionary representation of state."""
        return deepcopy(self._state)


class JinjaEventPlugin(BaseEventPlugin):
    """Event plugin for producing event using Jinja template engine."""

    _MODULES_PACKAGE = 'eventum_plugins.event.jinja_modules'
    _JINJA_EXTENSIONS = ('jinja2.ext.do', )

    def __init__(
        self,
        config: JinjaEventConfig,
        loader: BaseLoader | None = None
    ) -> None:
        self._config = config

        loader = loader or FileSystemLoader(searchpath=EVENT_TEMPLATES_DIR)
        self._env = Environment(loader=loader)

        self._initialize_environment()

        self._templates = self._load_templates()
        self._template_states: dict[str, State] = {
            template.name: State()              # type: ignore[misc]
            for template in self._templates
        }
        self._spinning_template_index = self._get_spinning_template_index()

    def _load_samples(
        self
    ) -> dict[str, tuple[str, ...] | tuple[tuple[str, ...], ...]]:
        """Load samples specified in config."""

        samples: dict[
            str, tuple[str, ...] | tuple[tuple[str, ...], ...]
        ] = dict()

        for sample_name, value in self._config.samples.items():
            match value:
                case ItemsSampleConfig():
                    samples[sample_name] = value.source
                case CSVSampleConfig():
                    try:
                        sample = load_csv_sample(
                            path=value.source,
                            delimiter=value.delimiter
                        )
                    except ContentManagementError as e:
                        raise EventPluginConfigurationError(
                            f'Failed to load sample: {e}'
                        ) from e

                    if value.header:
                        sample = sample[1:]

                    samples[sample_name] = sample
                case _:
                    assert_never(value)

        return samples

    def _load_templates(self) -> list[Template]:
        """Load templates specified in config."""
        templates: list[Template] = []

        for template_conf in self._config.templates.values():
            try:
                template = self._env.get_template(template_conf.template)
                if template.name is None:
                    raise EventPluginConfigurationError(
                        'Template must have a name'
                    )
                templates.append(template)
            except TemplateNotFound as e:
                raise EventPluginConfigurationError(
                    f'Failed to load template: {e}'
                ) from e
            except TemplateSyntaxError as e:
                raise EventPluginConfigurationError(
                    f'Bad syntax in template "{template_conf.template}": {e}'
                ) from e
            except TemplateError as e:
                raise EventPluginConfigurationError(
                    f'Error in "{template_conf.template}" template: {e}'
                ) from e

        return templates

    def _initialize_environment(self) -> None:
        """Set parameters to templates environment."""

        self._env.globals['params'] = self._config.params
        self._env.globals['samples'] = self._load_samples()
        self._env.globals['shared'] = State()
        self._env.globals['subprocess'] = SubprocessManager()

        for extension in self._JINJA_EXTENSIONS:
            self._env.add_extension(extension)

        modules: dict[str, ModuleType] = dict()
        for module_name in get_module_names(self._MODULES_PACKAGE):
            module = importlib.import_module(
                f'{self._MODULES_PACKAGE}.{module_name}'
            )
            modules[module_name] = module

        self._env.globals['module'] = modules

    def _get_spinning_template_index(self) -> Iterator[int]:
        """Get generator for "spin" picking mode."""

        while True:
            for i, _ in enumerate((self._templates)):
                yield i

    def _pick_template(self) -> Template | list[Template]:
        """Pick template(s) depending on picking mode."""

        match self._config.mode:
            case TemplatePickingMode.ALL:
                return self._templates
            case TemplatePickingMode.ANY:
                return random.choice(self._templates)
            case TemplatePickingMode.CHANCE:
                return random.choices(
                    population=self._templates,
                    weights=[
                        template_conf.chance
                        for template_conf in self._config.templates.values()
                    ],
                    k=1
                )[0]
            case TemplatePickingMode.SPIN:
                return self._templates[next(self._spinning_template_index)]
            case val:
                assert_never(val)

    def render(self, **kwargs) -> list[str]:
        """Render event with passing specified `kwargs` to template
        and return result.
        """
        picked = self._pick_template()
        if not isinstance(picked, list):
            picked = [picked]

        rendered = []
        for template in picked:
            try:
                rendered.append(
                    template.render(
                        locals=self._template_states[
                            template.name       # type: ignore[index]
                        ],
                        **kwargs
                    )
                )
            except TemplateRuntimeError as e:
                raise EventPluginRuntimeError(
                    f'Failed to render template: {e}'
                ) from e

        return rendered

    @property
    def shared_vars(self) -> State:
        """Get state of shared variables. The returned state is a copy."""
        return deepcopy(                        # type: ignore[return-value]
            self._env.globals['shared']
        )

    @shared_vars.setter
    def shared_vars(self, value: State) -> None:
        """Set state of shared variables."""
        self._env.globals['shared'] = value

    @property
    def local_vars(self) -> dict[str, State]:
        """Get state of local variables. The returned state is a copy."""
        return deepcopy(self._template_states)

    @local_vars.setter
    def local_vars(self, value: dict[str, State]) -> None:
        """Set state of local variables."""
        self._template_states = value

    @property
    def subprocess_manager(self) -> SubprocessManager:
        """Get `SubprocessManager`."""
        return self._env.globals['subprocess']  # type: ignore[return-value]

    @subprocess_manager.setter
    def subprocess_manager(self, value: SubprocessManager) -> None:
        """Set `SubprocessManager`."""
        self._env.globals['subprocess'] = value


PLUGIN_CLASS = JinjaEventPlugin
CONFIG_CLASS = JinjaEventConfig
