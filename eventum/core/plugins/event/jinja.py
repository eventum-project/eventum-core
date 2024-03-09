from typing import assert_never

from eventum.core.models.application_config import (CSVSampleConfig,
                                                    JinjaEventConfig,
                                                    ItemsSampleConfig)
from eventum.core.plugins.event.base import BaseEventPlugin, EventPluginError
from eventum.repository.manage import (get_templates_environment,
                                       load_csv_sample)
from jinja2 import Template, TemplateNotFound


class JinjaEventPluginError(EventPluginError):
    """Exception for `JinjaEventPlugin` errors."""


class JinjaEventPlugin(BaseEventPlugin):
    """Event plugin for producing event using Jinja template engine."""

    def __init__(self, config: JinjaEventConfig) -> None:
        self._config = config

        self._samples = self._load_samples()
        self._templates = self._load_templates()

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

        env = get_templates_environment()
        templates = []

        for _, template_conf in self._config.templates.items():
            try:
                templates.append(env.get_template(template_conf.template))
            except TemplateNotFound as e:
                raise JinjaEventPluginError(
                    f'Failed to load template: {e}'
                ) from e

        return templates
