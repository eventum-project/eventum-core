import random
from typing import Any, Callable, Iterator, assert_never

from eventum.core.models.application_config import (CSVSampleConfig,
                                                    JinjaEventConfig,
                                                    ItemsSampleConfig,
                                                    TemplatePickingMode)
from eventum.core.plugins.event.base import BaseEventPlugin, EventPluginError
from eventum.core.settings import JINJA_ENABLED_EXTENSIONS
from eventum.repository.manage import (get_templates_environment,
                                       load_csv_sample)
from jinja2 import Template, TemplateNotFound, TemplateError


class JinjaEventPluginError(EventPluginError):
    """Exception for `JinjaEventPlugin` errors."""


class Subprocess:
    def __init__(self, config: str) -> None:
        self._config = config

    def start(self) -> None:
        """Start subprocess with config specified in initializer."""
        raise NotImplementedError

    @property
    def is_running(self) -> bool:
        """Get status whether the subprocess is running."""
        raise NotImplementedError


class State:
    def __init__(self) -> None:
        self._state = dict()

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


class JinjaEventPlugin(BaseEventPlugin):
    """Event plugin for producing event using Jinja template engine."""

    def __init__(self, config: JinjaEventConfig) -> None:
        self._config = config

        self._env = get_templates_environment()
        self._initialize_environment()

        self._templates = self._load_templates()
        self._template_states = {
            template.name: State() for template in self._templates
        }
        self._spinning_template_index = self._get_spinning_template_index()

    def _load_samples(self) -> dict[str, list]:
        """Load samples specified in config."""

        samples = dict()

        for sample_name, value in self._config.samples.items():
            match value:
                case ItemsSampleConfig():
                    samples[sample_name] = value.source
                case CSVSampleConfig():
                    sample = load_csv_sample(
                        path=value.source,
                        delimiter=value.delimiter
                    )
                    if value.header:
                        sample = sample[1:]

                    samples[sample_name] = sample
                case _:
                    assert_never(value)

        return samples

    def _load_templates(self) -> list[Template]:
        """Load templates specified in config."""

        templates = []

        for _, template_conf in self._config.templates.items():
            try:
                templates.append(
                    self._env.get_template(template_conf.template)
                )
            except TemplateNotFound as e:
                raise JinjaEventPluginError(
                    f'Failed to load template: {e}'
                ) from e

        return templates

    def _get_template_chances(self) -> list[float]:
        """Get list with chances to pick template in `chance` mode."""
        if self._config.mode != TemplatePickingMode.CHANCE:
            raise JinjaEventPluginError(
                'Template chances can only be used in '
                f'"{TemplatePickingMode.CHANCE}" picking mode'
            )

        chances = []

        for _, template_conf in self._config.templates.items():
            chances.append(template_conf.chance)

        return chances

    def _initialize_environment(self) -> None:
        """Set parameters to templates environment."""
        self._env.globals['params'] = self._config.params
        self._env.globals['samples'] = self._load_samples()
        self._env.globals['shared'] = State()

        for ext in JINJA_ENABLED_EXTENSIONS:
            self._env.add_extension(ext)

        self._env.globals['subprocesses'] = dict()
        for name, subproc_conf in self._config.subprocesses.items():
            self._env.globals['subprocesses'][name] = Subprocess(
                config=subproc_conf.config
            )

    def _get_spinning_template_index(self) -> Iterator[int]:
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
                    weights=self._get_template_chances(),
                    k=1
                )[0]
            case TemplatePickingMode.SPIN:
                return self._templates[next(self._spinning_template_index)]
            case val:
                assert_never(val)

    def produce(self, callback: Callable[[str], None], **kwargs) -> None:
        """Produce event with passing specified `kwargs` to template
        and execute callback with result.
        """
        picked = self._pick_template()
        if not isinstance(picked, list):
            picked = [picked]

        for template in picked:
            state = self._template_states[template.name]
            try:
                content = template.render(locals=state, **kwargs)
            except TemplateError as e:
                continue

            callback(content)
