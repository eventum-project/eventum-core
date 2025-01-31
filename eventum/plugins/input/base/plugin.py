from abc import abstractmethod
from concurrent.futures import Future, ThreadPoolExecutor
from typing import (Iterator, Literal, NotRequired, Required, TypeAlias,
                    TypeVar, assert_never)

from numpy import datetime64
from numpy.typing import NDArray
from pydantic import RootModel
from pytz import BaseTzInfo

from eventum.plugins.base.plugin import Plugin, PluginParams
from eventum.plugins.exceptions import PluginConfigurationError
from eventum.plugins.input.base.config import InputPluginConfig
from eventum.plugins.input.batcher import BatcherFullError, TimestampsBatcher

QueueOverflowMode: TypeAlias = Literal['block', 'skip']


class InputPluginParams(PluginParams):
    """Parameters for input plugin.

    Attributes
    ----------
    live_mode : bool
        Wether to use live mode and generate events at moments
        defined by timestamp values

    timezone : BaseTzInfo
        Timezone that is used for generated timestamps

    batch_size : int | None, default=100_000
        Parameter `batch_size` of `TimestampsBatcher`

    batch_delay : float | None, default=0.1
        Parameter `batch_delay` of `TimestampsBatcher`

    queue_max_size : int, default=1_000_000
        Parameter `queue_max_size` of `TimestampsBatcher`

    on_queue_overflow : QueueOverflowMode, default='block'
        Block or skip adding new timestamps when batcher is overflowed
    """
    live_mode: Required[bool]
    timezone: Required[BaseTzInfo]
    batch_size: NotRequired[int | None]
    batch_delay: NotRequired[float | None]
    queue_max_size: NotRequired[int]
    on_queue_overflow: NotRequired[QueueOverflowMode]


ConfigT = TypeVar(
    'ConfigT',
    bound=(InputPluginConfig | RootModel[InputPluginConfig])
)


class InputPlugin(Plugin[ConfigT, InputPluginParams], register=False):
    """Base class for all input plugins.

    Parameters
    ----------
    **kwargs : Unpack[InputPluginKwargs]
        Arguments for plugin configuration (see `InputPluginKwargs`)

    Raises
    ------
    PluginConfigurationError
        If any error occurs during initializing plugin with the
        provided parameters
    """

    def __init__(self, config: ConfigT, params: InputPluginParams) -> None:
        super().__init__(config, params)

        with self.required_params():
            self._live_mode = params['live_mode']
            self._timezone = params['timezone']

        try:
            self._batcher = TimestampsBatcher(
                batch_size=params.get('batch_size', 100_000),
                batch_delay=params.get('batch_delay', 0.1),
                scheduling=self._live_mode,
                timezone=self._timezone,
                queue_max_size=params.get('queue_max_size', 1_000_000)
            )
        except ValueError as e:
            raise PluginConfigurationError(
                'Wrong batching parameters',
                context=dict(self.instance_info, reason=str(e))
            ) from None

        self._on_queue_overflow: QueueOverflowMode = params.get(
            'on_queue_overflow', 'block'
        )

    def _handle_done_future(self, future: Future) -> None:
        """Handle future when it is done.

        Parameters
        ----------
        future : Future
            Done future
        """
        try:
            future.result()
        except Exception:
            pass
        finally:
            self._batcher.close()

    def _enqueue(self, timestamps: NDArray[datetime64]) -> None:
        """Enqueue timestamps to batcher with handling overflowing.

        Parameters
        ----------
        timestamps : NDArray[datetime64]
            Timestamps to add
        """
        match self._on_queue_overflow:
            case 'block':
                self._batcher.add(timestamps, block=True)
            case 'skip':
                try:
                    self._batcher.add(timestamps, block=False)
                except BatcherFullError:
                    self._logger.warning(
                        'Timestamps were skipped due to batcher is overflowed',
                        count=len(timestamps),
                        first_timestamp=timestamps[0],
                        last_timestamp=timestamps[-1],
                    )
            case mode:
                assert_never(mode)

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
                self._generate_live
                if self._live_mode
                else self._generate_sample
            )
            future.add_done_callback(self._handle_done_future)

            yield from self._batcher.scroll()

            future.result()

    @abstractmethod
    def _generate_sample(self) -> None:
        """Start timestamps generation in sample mode. `self._enqueue`
        method should be called once timestamps are generated.

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
    def _generate_live(self) -> None:
        """Start timestamps generation in live mode. `self._enqueue`
        method should be called cyclically as time passes and earlier
        than moment of the first timestamp value in the batch. There is
        no need to calculate the moments of enqueuing precisely since
        timestamps scheduling is handled by underlying batcher.

        Raises
        ------
        PluginRuntimeError
            If any error occurs during timestamps generation
        """
        ...

    @property
    def live_mode(self) -> bool:
        """Status of live mode of the plugin."""
        return self._live_mode
