from abc import ABC, abstractmethod
from functools import cache
from types import ModuleType


class PluginLocator(ABC):
    """Locator of plugins."""

    @staticmethod
    @abstractmethod
    def get_root_package() -> ModuleType:
        """Get root package of plugins."""
        ...


class InputPluginLocator(PluginLocator):
    """Locator of input plugins."""

    @staticmethod
    @cache
    def get_root_package() -> ModuleType:
        import eventum_plugins.input.plugins as input_plugins
        return input_plugins


class EventPluginLocator(PluginLocator):
    """Locator of event plugins."""

    @staticmethod
    @cache
    def get_root_package() -> ModuleType:
        import eventum_plugins.event.plugins as event_plugins
        return event_plugins


class OutputPluginLocator(PluginLocator):
    """Locator of output plugins."""

    @staticmethod
    @cache
    def get_root_package() -> ModuleType:
        import eventum_plugins.output.plugins as output_plugins
        return output_plugins
