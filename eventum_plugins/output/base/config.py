from abc import ABC

from pydantic import Field

from eventum_plugins.base.config import PluginConfig
from eventum_plugins.output.fields import (Format, FormatterConfig,
                                           SimpleFormatterConfig)


class OutputPluginConfig(PluginConfig, ABC, frozen=True):
    """Base config model for output plugins.

    Parameters
    ----------
    formatter : FormatterConfig, default=SimpleFormatterConfig(...)
        Formatter configuration
    """
    formatter: FormatterConfig = Field(
        default_factory=lambda: SimpleFormatterConfig(format=Format.PLAIN),
        validate_default=True
    )
