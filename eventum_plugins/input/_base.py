from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Iterator, final

from numpy import datetime64
from numpy.typing import NDArray
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


class LiveInputPluginMixin(ABC):
    """Input plugin mixin that adds live mode."""

    @final
    def live(
        self,
        batcher: TimestampsBatcher
    ) -> Iterator[NDArray[datetime64]]:
        """Start production of event timestamps in live. Iteration
        starts from only actual timestamps that are not in the past.
        Iteration is blocked until new events occur in real time.
        Elements of iteration are arrays of timestamps that batched
        correspondingly to `batch_size` and `batch_delay`. Iteration
        may or may not be infinite depending on specific plugin and its
        configuration.
        """
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._live, batcher)
            yield from batcher.scroll()

            future.result()

    @abstractmethod
    def _live(self, publisher: TimestampsBatcher) -> None:
        """Internal implementation of `live` mode."""
        ...


class SampleInputPluginMixin(ABC):
    """Input plugin mixin that adds sample mode."""

    @final
    def sample(
        self,
        batcher: TimestampsBatcher
    ) -> Iterator[NDArray[datetime64]]:
        """Product sample of event timestamps. Iteration is carried out
        from the first to the last timestamp of generated sample
        without any delays. Elements of iteration are arrays of
        timestamps that batched correspondingly to `batch_size`. Number
        of elements of iteration is always finite.
        """
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._sample, batcher)
            yield from batcher.scroll()

            future.result()

    @abstractmethod
    def _sample(self, batcher: TimestampsBatcher) -> None:
        """Internal implementation of `sample` mode."""
