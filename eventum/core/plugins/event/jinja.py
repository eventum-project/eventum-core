import random
from typing import Callable, Iterator, assert_never

from eventum.core.models.application_config import (CSVSampleConfig,
                                                    JinjaEventConfig,
                                                    ItemsSampleConfig,
                                                    TemplatePickingMode)
from eventum.core.plugins.event.base import BaseEventPlugin, EventPluginError
from eventum.repository.manage import (get_templates_environment,
                                       load_csv_sample)
from jinja2 import Template, TemplateNotFound


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


class JinjaEventPlugin(BaseEventPlugin):
    """Event plugin for producing event using Jinja template engine."""

    def __init__(self, config: JinjaEventConfig) -> None:
        self._config = config

        self._env = get_templates_environment()

        self._samples = self._load_samples()
        self._templates = self._load_templates()
        self._set_environment_globals()

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
                        filename=value.source,
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

    def _set_environment_globals(self) -> None:
        """Set globally available resources to templates environment."""
        self._env.globals['params'] = self._config.params
        self._env.globals['samples'] = self._samples

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
            content = template.render(**kwargs)
            callback(content)
