from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, NoReturn


class BaseDistribution(ABC):
    """Base class for all distributions."""

    @abstractmethod
    def live(self, on_event: Callable[[str], Any]) -> None | NoReturn:
        """Start simulation of distribution in live. Every time event
        is occured in distribution, the `on_triger` callable is called
        with current timestamp as `str` in ISO-8601 format as a single
        parameter. If distribution has no end time then function
        execution never ends, otherwise `None` is returned in the end.
        """
        ...

    @abstractmethod
    def sample(self, on_event: Callable[[str], Any]) -> None:
        """Start simulation of distribution in sample mode. The method
        behavior is similar to `live` method except for the fact that
        execution is not tied to real time and there is no any delay
        between `on_event` calls. Therefore distribution is expected to have
        specific start and end time to generate finite sample of timestamps.
        """
        ...


class SampleDistribution(BaseDistribution):
    """Distribution for generating specified count of events. Use it when
    you only need to produce event facts and timestamps aren't important.
    For all events timestamps are the same and has value of moment when
    distribution was started. Only the `sample` method is expected to be
    called in this distribution.
    """

    def __init__(self, count: int) -> None:
        self._count = count

    def sample(self, on_event: Callable[[str], Any]) -> None:
        timestamp = datetime.now().isoformat()

        for _ in range(self._count):
            on_event(timestamp)

    def live(self, on_event: Callable[[str], Any]) -> None:
        raise NotImplementedError(
            'Method is not expected to be called for this distribution'
        )


class ManualDistribution(BaseDistribution):
    ...


class CronDistribution(BaseDistribution):
    ...


class TimePatternDistribution(BaseDistribution):
    ...


class TimePatternPoolDistribution(BaseDistribution):
    ...
