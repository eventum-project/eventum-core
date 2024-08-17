from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel
from pytz.tzinfo import BaseTzInfo

from eventum_plugins.registry import PluginsRegistry, PluginType
from eventum_plugins.timestamps_batcher import TimestampsBatcher


class InputPluginConfig(ABC, BaseModel, extra='forbid', frozen=True):
    """Base config model for input plugins"""
    tags: tuple[str, ...] = tuple()


class InputPlugin(ABC):
    """Base class for all input plugins."""

    def __init_subclass__(
        cls,
        config_cls: type,
        register: bool = True,
        **kwargs
    ):
        super().__init_subclass__(**kwargs)

        if not register:
            return

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

    @abstractmethod
    def start(self, batcher: TimestampsBatcher) -> None:
        """Start generation of timestamps."""
        ...
