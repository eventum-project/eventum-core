from abc import ABC

from eventum_plugins.base.config import PluginConfig


class EventPluginConfig(PluginConfig, ABC):
    """Base config model for event plugins."""
