from abc import ABC

from pydantic import Field

from eventum_plugins.base.config import PluginConfig
from eventum_plugins.output.fields import (Format, FormatterConfigT,
                                           SimpleFormatterConfig)


class OutputPluginConfig(PluginConfig, ABC, frozen=True):
    """Base config model for output plugins.

    Parameters
    ----------
    formatter : FormatterConfigT, default=SimpleFormatterConfig(...)
        Formatter configuration
    """
    formatter: FormatterConfigT = Field(
        default_factory=lambda: SimpleFormatterConfig(format=Format.PLAIN),
        validate_default=True,
        discriminator='format'
    )
