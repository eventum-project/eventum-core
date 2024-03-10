from abc import ABC, abstractmethod


class OutputPluginError(Exception):
    """Base exception for all output plugin errors."""


class FormatError(OutputPluginError):
    """Exception for formatting errors."""


class BaseOutputPlugin(ABC):
    """Base class for all output plugins."""

    @abstractmethod
    def write(self, event: str) -> None:
        """Write single event to output stream."""
        ...

    @abstractmethod
    def write_many(self, events: list[str]) -> None:
        """Write many events to output stream in optimized way."""
        ...
