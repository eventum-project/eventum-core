from abc import ABC, abstractmethod


class BaseOutputPlugin(ABC):
    """Base class for all output plugins."""

    @abstractmethod
    def write(self, content: str) -> None:
        """Write single object to output stream."""
        ...

    @abstractmethod
    def write_many(self, content: list[str]) -> None:
        """Write many objects to output stream in optimized way."""
        ...
