import importlib
import random
import subprocess
from collections import deque
from copy import deepcopy
from typing import Any, Iterator, assert_never

from jinja2 import (Environment, Template, TemplateError, TemplateNotFound,
                    TemplateRuntimeError, TemplateSyntaxError)

from eventum.core.models.application_config import (CSVSampleConfig,
                                                    ItemsSampleConfig,
                                                    JinjaEventConfig,
                                                    TemplatePickingMode)
from eventum.core.plugins.event.base import (BaseEventPlugin,
                                             EventPluginConfigurationError,
                                             EventPluginRuntimeError)
from eventum.core.settings import JINJA_EXTENSIONS, JINJA_MODULES
from eventum.repository.manage import (ContentReadError,
                                       get_templates_environment,
                                       load_csv_sample)


class SubprocessManager:
    """Class for running any command in subprocess from template."""

    _HISTORY_SIZE = 10

    def __init__(self) -> None:
        self._commands_history = deque(maxlen=self._HISTORY_SIZE)
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

    @property
    def commands_history(self) -> tuple[tuple[int, str]]:
        """Get history of running commands."""
        return tuple(self._commands_history)


class SubprocessManagerMock(SubprocessManager):
    def run(self, command: str, block: bool = False) -> str | None:
        self._save_command_in_history(command)

        if block:
            return '<SUBPROCESS MOCK RESULT>'


class State:
    def __init__(self) -> None:
        self._state: dict[str, Any] = dict()

    def set(self, key: str, value: Any) -> None:
        """Set variable value to state."""
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

    def __init__(
        self,
        config: JinjaEventConfig,
        environment: Environment | None = None
    ) -> None:
        self._config = config

        if environment is None:
            self._env = get_templates_environment()
        else:
            self._env = environment

        self._initialize_environment()

        self._templates = self._load_templates()
        self._template_states = {
            template.name: State() for template in self._templates
        }
        self._spinning_template_index = self._get_spinning_template_index()

    def _load_samples(self) -> dict[str, list[str] | list[tuple[str, ...]]]:
        """Load samples specified in config."""

        samples: dict[str, list[str] | list[tuple[str, ...]]] = dict()

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
                    except ContentReadError as e:
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
        templates = []

        for template_conf in self._config.templates.values():
            try:
                templates.append(
                    self._env.get_template(template_conf.template)
                )
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

        for extension_name in JINJA_EXTENSIONS:
            try:
                self._env.add_extension(extension_name)
            except ModuleNotFoundError as e:
                raise EventPluginConfigurationError(
                    f'Failed to load jinja extension {extension_name}: {e}'
                )

        for module_name in JINJA_MODULES:
            try:
                module = importlib.import_module(
                    f'eventum.core.plugins.event.jinja_modules.{module_name}'
                )
            except ModuleNotFoundError as e:
                raise EventPluginConfigurationError(
                    f'Failed to load jinja module {module_name}: {e}'
                )

            self._env.globals[module_name] = module

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
                        locals=self._template_states[template.name],
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
        return deepcopy(self._env.globals['shared'])

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
        return self._env.globals['subprocess']

    @subprocess_manager.setter
    def subprocess_manager(self, value: SubprocessManager) -> None:
        """Set `SubprocessManager`."""
        self._env.globals['subprocess'] = value

    @classmethod
    def create_from_config(
        cls,
        config: JinjaEventConfig        # type: ignore
    ) -> 'JinjaEventPlugin':
        return JinjaEventPlugin(config)


def load_plugin():
    """Return class of plugin from current module."""
    return JinjaEventPlugin
