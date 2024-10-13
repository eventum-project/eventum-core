from abc import abstractmethod
from concurrent.futures import Future, ThreadPoolExecutor
from typing import (Any, Callable, Iterator, Literal, NotRequired, Required,
                    TypedDict, Unpack, assert_never, final)

from numpy import datetime64
from numpy.typing import NDArray
from pytz import BaseTzInfo

from eventum_plugins.base.plugin import Plugin
from eventum_plugins.exceptions import PluginConfigurationError
from eventum_plugins.input.base.config import InputPluginConfig
from eventum_plugins.input.batcher import TimestampsBatcher
from eventum_plugins.input.enums import TimeMode


class InputPluginKwargs(TypedDict):
    id: Required[str]
    mode: Required[TimeMode]
    timezone: Required[BaseTzInfo]
    batch_size: NotRequired[int | None]
    batch_delay: NotRequired[float | None]
    queue_max_size: NotRequired[int]
    on_queue_overflow: NotRequired[Literal['block', 'skip']]


class InputPlugin(Plugin, config_cls=object, register=False):
    """Base class for all input plugins.

    Parameters
    ----------
    id : str
        Arbitrary string for distinction different instances of plugins
        (e.g. in logger)

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

    queue_max_size : int, default=1_000_000
        Parameter `queue_max_size` for underlying batcher

    on_queue_overflow : Literal['block', 'skip'], default='block'
        Block or skip adding new timestamps when batcher input
        queue is overflowed

    Raises
    ------
    PluginConfigurationError
        If any error occurs during initializing plugin with the
        provided config
    """

    def __init__(
        self,
        *,
        config: InputPluginConfig,
        **kwargs: Unpack[InputPluginKwargs]
    ) -> None:
        self._id = kwargs['id']
        self._config = config
        self._mode = kwargs['mode']
        self._timezone = kwargs['timezone']

        try:
            self._batcher = TimestampsBatcher(
                batch_size=kwargs.get('batch_size', 100_000),
                batch_delay=kwargs.get('batch_delay', 0.1),
                scheduling=True if self._mode == TimeMode.LIVE else False,
                timezone=self._timezone,
                queue_max_size=kwargs.get('queue_max_size', 1_000_000)
            )
        except ValueError as e:
            raise PluginConfigurationError(f'Wrong batching parameters: {e}')

        self._block_on_overflow = kwargs.get(
            'on_queue_overflow', 'block'
        ) == 'block'

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
            If any error occurs during timestamps generation
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
            If any error occurs during timestamps generation
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
            If any error occurs during timestamps generation
        """
        ...

    @property
    def id(self) -> str:
        """ID of the plugin."""
        return self._id

    @property
    def mode(self) -> TimeMode:
        """Time mode of the plugin."""
        return self._mode
