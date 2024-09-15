from abc import abstractmethod
from concurrent.futures import Future, ThreadPoolExecutor
from typing import (Any, Callable, Iterator, Literal, NotRequired, Required,
                    TypedDict, assert_never, final)

from numpy import datetime64
from numpy.typing import NDArray
from pytz import BaseTzInfo

from eventum_plugins.base.plugin import Plugin
from eventum_plugins.exceptions import PluginConfigurationError
from eventum_plugins.input.base.config import InputPluginConfig
from eventum_plugins.input.batcher import TimestampsBatcher
from eventum_plugins.input.enums import TimeMode


class InputPluginKwargs(TypedDict):
    id: Required[int]
    mode: Required[TimeMode]
    timezone: Required[BaseTzInfo]
    batch_size: NotRequired[int | None]
    batch_delay: NotRequired[float | None]
    queue_max_size: NotRequired[int]
    on_queue_overflow: NotRequired[Literal['block', 'skip']]


class InputPlugin(Plugin, config_cls=object, base=True):
    """Base class for all input plugins.

    Parameters
    ----------
    id : int
        Arbitrary number for distinction deferent instances of the same
        plugin class

    config : Any
        Configuration for a plugin which class (in implemented plugins)
        is subclass of `InputPluginConfig` model

    mode : TimeMode
            Time mode of timestamps generation.

    timezone : BaseTzInfo
        Timezone that is used for generating timestamps

    batch_size : int | None, default=100_000
        Parameter `batch_size` for underlying batcher

    batch_delay : float | None, default=0.1
        Parameter `batch_delay` for underlying batcher

    queue_max_size : int, default=100_000_000
        Parameter `queue_max_size` for underlying batcher

    on_queue_overflow : Literal['block', 'skip'], default='block'
        Block or skip adding new timestamps when batcher input
        queue is overflowed

    Raises
    ------
    PluginConfigurationError
        If any error occurred during initializing plugin with the
        provided config
    """

    def __init__(
        self,
        config: InputPluginConfig,
        *,
        id: int,
        mode: TimeMode,
        timezone: BaseTzInfo,
        batch_size: int | None = 100_000,
        batch_delay: float | None = 0.1,
        queue_max_size: int = 100_000_000,
        on_queue_overflow: Literal['block', 'skip'] = 'block'
    ) -> None:
        self._id = id
        self._config = config
        self._mode = mode
        self._timezone = timezone

        try:
            self._batcher = TimestampsBatcher(
                batch_size=batch_size,
                batch_delay=batch_delay,
                scheduling=True if mode == TimeMode.LIVE else False,
                timezone=self._timezone,
                queue_max_size=queue_max_size
            )
        except ValueError as e:
            raise PluginConfigurationError(f'Wrong batching parameters: {e}')

        self._block_on_overflow = on_queue_overflow == 'block'

    def _handle_done_future(self, future: Future) -> None:
        """Handle future when it is done propagating possible
        exceptions. Batcher is closed finally.

        Parameters
        ----------
        future : Future
            Done future
        """
        try:
            future.result()
        finally:
            self._batcher.close()

    @final
    def generate(self) -> Iterator[NDArray[datetime64]]:
        """Start timestamps generation in background thread and yield
        batches of generated timestamps. In sample mode timestamps
        are yielded immediately, in live mode - respectively to real
        time.

        Yields
        -------
        NDArray[datetime64]
            Batches of generated timestamps

        Raises
        ------
        PluginRuntimeError
            If any error occurred during timestamps generation
        """
        match self._mode:
            case TimeMode.SAMPLE:
                method = self._generate_sample
            case TimeMode.LIVE:
                method = self._generate_live
            case v:
                assert_never(v)

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                method,
                lambda batch: self._batcher.add(batch, self._block_on_overflow)
            )
            future.add_done_callback(self._handle_done_future)

            yield from self._batcher.scroll()
            future.result()

    @abstractmethod
    def _generate_sample(
        self,
        on_events: Callable[[NDArray[datetime64]], Any]
    ) -> None:
        """Start timestamps generation in sample mode. `on_events`
        callback should be called once timestamps are generated.

        Parameters
        ----------
        on_events : Callable[[NDArray[datetime64]], Any]
            Callback that should be called for generated timestamps

        Raises
        ------
        PluginRuntimeError
            If any error occurred during timestamps generation
        """
        ...

    @abstractmethod
    def _generate_live(
        self,
        on_events: Callable[[NDArray[datetime64]], Any]
    ) -> None:
        """Start timestamps generation in live mode. `on_events`
        callback should be called with some delays but without
        increasing accumulation of future timestamps. Also it is
        not necessary to schedule precisely when to call `on_events`
        callback since timestamps scheduling is implemented internally.

        Parameters
        ----------
        on_events : Callable[[NDArray[datetime64]], Any]
            Callback that should be called for generated timestamps

        Raises
        ------
        PluginRuntimeError
            If any error occurred during timestamps generation
        """
        ...

    @property
    def id(self) -> int:
        """ID of the plugin."""
        return self._id

    @property
    def mode(self) -> TimeMode:
        """Time mode of the plugin."""
        return self._mode
