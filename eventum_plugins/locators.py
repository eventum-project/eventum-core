from abc import ABC, abstractmethod
from functools import cache
from types import ModuleType


class PluginLocator(ABC):
    """Locator of plugins."""

    @abstractmethod
    def get_root_package(self) -> ModuleType:
        """Get root package of plugins."""
        ...


class DynamicLocator(PluginLocator):
    """Dynamic locator for defining root package in runtime."""

    def __init__(self, root_package: ModuleType) -> None:
        self._root_package = root_package

    def get_root_package(self) -> ModuleType:
        return self._root_package


class InputPluginLocator(PluginLocator):
    """Locator of input plugins."""

    @cache
    def get_root_package(self) -> ModuleType:
        import eventum_plugins.input.plugins as input_plugins
        return input_plugins


class EventPluginLocator(PluginLocator):
    """Locator of event plugins."""

    @cache
    def get_root_package(self) -> ModuleType:
        import eventum_plugins.event.plugins as event_plugins
        return event_plugins


class OutputPluginLocator(PluginLocator):
    """Locator of output plugins."""

    @cache
    def get_root_package(self) -> ModuleType:
        import eventum_plugins.output.plugins as output_plugins
        return output_plugins
