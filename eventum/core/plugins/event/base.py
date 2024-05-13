from abc import ABC, abstractmethod
from typing import Self

from eventum.core.models.event_config import EventConfig


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
    def create_from_config(cls, config: EventConfig) -> Self:
        """Create instance of configured plugin from config."""
        ...
