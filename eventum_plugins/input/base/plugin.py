from abc import abstractmethod
from concurrent.futures import Future, ThreadPoolExecutor
from typing import (Any, Callable, Iterator, Literal, NotRequired, Required,
                    TypedDict, Unpack)

from numpy import datetime64
from numpy.typing import NDArray
from pytz import BaseTzInfo

from eventum_plugins.base.plugin import Plugin
from eventum_plugins.exceptions import (PluginConfigurationError,
                                        PluginRuntimeError)
from eventum_plugins.input.base.config import InputPluginConfig
from eventum_plugins.input.batcher import TimestampsBatcher


class InputPluginKwargs(TypedDict):
    id: Required[str]
    live_mode: Required[bool]
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
        Arbitrary string for representing instances (e.g. in logger)

    config : InputPluginConfig
        Configuration for a plugin

    live_mode : bool
        Wether to use timestamp values to generate in live mode

    timezone : BaseTzInfo
        Timezone that is used for generated timestamps

    batch_size : int | None, default=100_000
        Parameter `batch_size` of `TimestampsBatcher`

    batch_delay : float | None, default=0.1
        Parameter `batch_delay` of `TimestampsBatcher`

    queue_max_size : int, default=1_000_000
        Parameter `queue_max_size` of `TimestampsBatcher`

    on_queue_overflow : Literal['block', 'skip'], default='block'
        Block or skip adding new timestamps when batcher is overflowed

    Raises
    ------
    PluginConfigurationError
        If any error occurs during initializing plugin with the
        provided parameters
    """

    def __init__(
        self,
        *,
        config: InputPluginConfig,
        **kwargs: Unpack[InputPluginKwargs]
    ) -> None:
        self._id = kwargs['id']
        self._config = config
        self._live_mode = kwargs['live_mode']
        self._timezone = kwargs['timezone']

        try:
            self._batcher = TimestampsBatcher(
                batch_size=kwargs.get('batch_size', 100_000),
                batch_delay=kwargs.get('batch_delay', 0.1),
                scheduling=self._live_mode,
                timezone=self._timezone,
                queue_max_size=kwargs.get('queue_max_size', 1_000_000)
            )
        except ValueError as e:
            raise PluginConfigurationError(f'Wrong batching parameters: {e}')

        self._block_on_overflow = kwargs.get(
            'on_queue_overflow', 'block'
        ) == 'block'

    def _handle_done_future(self, future: Future) -> None:
        """Handle future when it is done with propagating possible
        exceptions. Batcher is closed finally.

        Parameters
        ----------
        future : Future
            Done future
        """
        try:
            future.result()
        except Exception as e:
            raise PluginRuntimeError from e
        finally:
            self._batcher.close()

    def generate(self) -> Iterator[NDArray[datetime64]]:
        """Start timestamps generation in background thread and yield
        batches of generated timestamps. In sample mode timestamps
        are yielded immediately as they are generated, in live mode
        - respectively to real time.

        Yields
        -------
        NDArray[datetime64]
            Batches of generated timestamps

        Raises
        ------
        PluginRuntimeError
            If any error occurs during timestamps generation
        """
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                (
                    self._generate_live
                    if self._live_mode
                    else self._generate_sample
                ),
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
        callback should be called cyclically as time passes and earlier
        than moment of the first timestamp value in the batch, but
        there is no need to calculate the moments precisely since
        timestamps scheduling is handled by callback.

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
    def live_mode(self) -> bool:
        """Status of live mode of the plugin."""
        return self._live_mode
