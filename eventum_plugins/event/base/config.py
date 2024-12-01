from abc import ABC

from eventum_plugins.base.config import PluginConfig


class EventPluginConfig(PluginConfig, ABC, frozen=True):
    """Base config model for event plugins."""
