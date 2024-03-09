from abc import ABC, abstractmethod
from typing import Any


class EventPluginError(Exception):
    """Base exception for all event plugin errors."""


class BaseEventPlugin(ABC):
    """Base class for all event plugins."""

    @abstractmethod
    def produce() -> Any:
        """Produce events with specified parameters and return it."""
        ...
