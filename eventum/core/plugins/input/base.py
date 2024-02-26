from abc import ABC, abstractmethod
from typing import Any, Callable, NoReturn


class BaseInputPlugin(ABC):
    """Base class for all input plugins."""


class LiveInputPlugin(BaseInputPlugin):
    """Base class for all input plugin that can be used in live mode."""

    @abstractmethod
    def live(self, on_event: Callable[[str], Any]) -> NoReturn:
        """Start production of events in live. Every time event is
        occured in proccess, the `on_triger` callable is called with
        current timestamp as `str` in ISO-8601 format as a single
        parameter. If process has no end time then function execution
        never ends, otherwise `None` is returned in the end.
        """
        ...


class SampleInputPlugin(BaseInputPlugin):
    """Base class for all input plugin that can be used in sample mode."""

    @abstractmethod
    def sample(self, on_event: Callable[[str], Any]) -> None:
        """Start production of events as a sample. Every time event
        is occured in proccess, the `on_triger` callable is called with
        current timestamp as `str` in ISO-8601 format as a single
        parameter. The proccess execution is not tied to real time and
        there is no any delay between `on_event` calls. Therefore
        distribution is expected to have specific start and end time
        to generate finite sample of timestamps.
        """
        ...
