from abc import abstractmethod
from typing import Any, Callable, TypeAlias

from numpy import datetime64
from pydantic import BaseModel


class InputPluginError(Exception):
    """Base exception for all input plugin errors."""


class InputPluginConfigurationError(InputPluginError):
    """Exception for input plugin configuration errors."""


class InputPluginRuntimeError(InputPluginError):
    """Exception for input plugin runtime errors."""


class InputPluginBaseConfig(BaseModel, extra='forbid', frozen=True):
    """Base config model for input plugins"""


class LiveInputPluginMixin:
    """Mixin for input plugins that can be used in live mode."""

    @abstractmethod
    def live(self, on_event: Callable[[datetime64], Any]) -> None:
        """Start production of events in live. Every time event is
        occurred in process, the `on_event` callable is called with
        current timestamp as a single parameter. If process has no end
        time then function execution never ends, otherwise `None` is
        returned in the end.
        """
        ...


class SampleInputPluginMixin:
    """Mixin for input plugin that can be used in sample mode."""

    @abstractmethod
    def sample(self, on_event: Callable[[datetime64], Any]) -> None:
        """Start production of events as a sample. Every time event is
        occurred in process, the `on_event` callable is called with
        current timestamp as a single parameter. The process execution
        is not tied to real time and there is no any delay between
        `on_event` calls. Therefore distribution is expected to have
        specific start and end time to generate finite sample of
        timestamps.
        """
        ...


InputPlugin: TypeAlias = (LiveInputPluginMixin | SampleInputPluginMixin)
