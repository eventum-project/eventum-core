from abc import ABC

from eventum_plugins.base.config import PluginConfig


class OutputPluginConfig(PluginConfig, ABC):
    """Base config model for output plugins."""
