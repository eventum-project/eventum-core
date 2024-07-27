from abc import ABC, abstractmethod
from typing import Any, Callable

from numpy import datetime64
from pydantic import BaseModel
from pytz.tzinfo import BaseTzInfo

from eventum_plugins.registry import PluginType, PluginsRegistry


class InputPluginConfig(ABC, BaseModel, extra='forbid', frozen=True):
    """Base config model for input plugins"""
    tags: tuple[str, ...] = tuple()


class InputPlugin(ABC):
    """Base class for all input plugins."""

    def __init_subclass__(cls, config_cls: type, **kwargs):
        super().__init_subclass__(**kwargs)

        plugin_name = cls.__module__.split('.')[-1]
        PluginsRegistry().register_plugin(
            type=PluginType.INPUT,
            name=plugin_name,
            cls=cls,
            config_cls=config_cls
        )

    @abstractmethod
    def __init__(self, config: Any, tz: BaseTzInfo) -> None:
        ...


class LiveInputPluginMixin(ABC):
    """Input plugin mixin that adds live mode."""

    @abstractmethod
    def live(self, on_event: Callable[[datetime64], Any]) -> None:
        """Start production of events in live. Every time event is
        occurred in process, the `on_event` callable is called with
        current timestamp as a single parameter. If process has no end
        time then function execution never ends, otherwise `None` is
        returned in the end.
        """
        ...


class SampleInputPluginMixin(ABC):
    """Input plugin mixin that adds sample mode."""

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
