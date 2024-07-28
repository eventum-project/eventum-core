from abc import ABC, abstractmethod
from typing import Any, Callable

from numpy import datetime64
from numpy.typing import NDArray
from pydantic import BaseModel
from pytz.tzinfo import BaseTzInfo

from eventum_plugins.registry import PluginsRegistry, PluginType


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
    def live(self, on_events: Callable[[NDArray[datetime64]], Any]) -> None:
        """Start production of event timestamps in live. Every time
        events are occurred in process, the `on_events` callable is
        called with array of corresponding timestamps that are near
        enough to be placed into single batch. If process has no end
        time then function execution never ends, otherwise `None` is
        returned in the end.
        """
        ...


class SampleInputPluginMixin(ABC):
    """Input plugin mixin that adds sample mode."""

    @abstractmethod
    def sample(self, on_events: Callable[[NDArray[datetime64]], Any]) -> None:
        """Product sample of events. `on_event` callable is called only
        once when entire sample of timestamps is done. Since process
        execution is not tied to real time and there is no any delay
        between `on_event` calls (like in `live` mode) it is expected to
        have specific start and end time to generate finite sample of
        timestamps.
        """
        ...
