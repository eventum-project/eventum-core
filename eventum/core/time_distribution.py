from abc import ABC, abstractmethod
from typing import Callable, NoReturn


class BaseTimeDistribution(ABC):
    """Base class for all time distributions."""

    @abstractmethod
    def live(self, on_event: Callable[[str]]) -> None | NoReturn:
        """Start simulation of time distribution in live. Every time
        event is occured in distribution, the `on_triger` callable is
        called with current timestamp as `str` in ISO-8601 format as a
        single parameter. If distribution has no end time then function
        execution never ends, otherwise `None` is returned in the end.
        """
        ...

    @abstractmethod
    def sample(self, on_event: Callable[[str]]) -> None:
        """Start simulation of time distribution in sample mode. The
        method behavior is similar to `live` method except for the fact
        that execution is not tied to real time and there is no any delay
        between `on_event` calls. Therefore distribution is expected to have
        specific start and end time to generate finite sample of timestamps.
        """
        ...


class CronTimeDistribution(BaseTimeDistribution):
    ...


class ManualTimeDistribution(BaseTimeDistribution):
    ...


class SampleTimeDistribution(BaseTimeDistribution):
    ...


class TimePatternDistribution(BaseTimeDistribution):
    ...


class TimePatternPoolDistribution(BaseTimeDistribution):
    ...
