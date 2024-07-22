from abc import ABC, abstractmethod

from pydantic import BaseModel


class EventPluginBaseConfig(ABC, BaseModel, extra='forbid', frozen=True):
    """Base config model for event plugins"""


class BaseEventPlugin(ABC):
    """Base class for all event plugins."""

    @abstractmethod
    def render(self, **kwargs) -> list[str]:
        """Render events with specified parameters and return it."""
        ...
