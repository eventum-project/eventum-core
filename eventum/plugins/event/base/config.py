from abc import ABC

from eventum.plugins.base.config import PluginConfig


class EventPluginConfig(PluginConfig, ABC, frozen=True):
    """Base config model for event plugins."""
