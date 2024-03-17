from abc import ABC, abstractmethod


class EventPluginError(Exception):
    """Base exception for all event plugin errors."""


class EventPluginConfigurationError(EventPluginError):
    """Exception for event plugin configuration errors."""


class EventPluginRuntimeError(EventPluginError):
    """Exception for event plugin runtime errors."""


class BaseEventPlugin(ABC):
    """Base class for all event plugins."""

    @abstractmethod
    def render(self, **kwargs) -> list[str]:
        """Render events with specified parameters and return it."""
        ...
