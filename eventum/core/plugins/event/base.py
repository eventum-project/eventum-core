from abc import ABC, abstractmethod

from eventum.core.models.application_config import EventConfig


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

    @classmethod
    @abstractmethod
    def create_from_config(cls, config: EventConfig) -> 'BaseEventPlugin':
        """Create instance of configured plugin from config."""
        ...
