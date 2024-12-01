from abc import ABC

from eventum_plugins.base.config import PluginConfig


class OutputPluginConfig(PluginConfig, ABC, frozen=True):
    """Base config model for output plugins."""
