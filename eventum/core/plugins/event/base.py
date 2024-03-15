from abc import ABC, abstractmethod
from typing import Any


class EventPluginError(Exception):
    """Base exception for all event plugin errors."""


class EventPluginConfigurationError(EventPluginError):
    """Exception for event plugin configuration errors."""


class EventPluginRuntimeError(EventPluginError):
    """Exception for event plugin runtime errors."""


class BaseEventPlugin(ABC):
    """Base class for all event plugins."""

    @abstractmethod
    def produce(self, *args, **kwargs) -> Any:
        """Produce events with specified parameters and return it."""
        ...
