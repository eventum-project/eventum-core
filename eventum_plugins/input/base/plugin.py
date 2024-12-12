from abc import abstractmethod
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime
from typing import (Any, Callable, Iterator, Literal, NotRequired, Required,
                    TypeAlias, TypeVar, assert_never)

import structlog
from numpy import datetime64
from numpy.typing import NDArray
from pydantic import RootModel
from pytz import BaseTzInfo

from eventum_plugins.base.plugin import Plugin, PluginParams, required_params
from eventum_plugins.exceptions import (PluginConfigurationError,
                                        PluginRuntimeError)
from eventum_plugins.input.base.config import InputPluginConfig
from eventum_plugins.input.batcher import BatcherFullError, TimestampsBatcher
from eventum_plugins.input.normalizers import (NoneStartPoint,
                                               VersatileDatetime,
                                               normalize_versatile_daterange)

logger = structlog.stdlib.get_logger()

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


config_T = TypeVar('config_T', bound=(InputPluginConfig | RootModel))


class InputPlugin(Plugin[config_T, InputPluginParams], register=False):
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

    def __init__(self, config: config_T, params: InputPluginParams) -> None:
        super().__init__(config, params)

        with required_params():
            self._live_mode = params['live_mode']
            self._timezone = params['timezone']

        batcher_parameters = {
            'batch_size': params.get('batch_size', 100_000),
            'batch_delay': params.get('batch_delay', 0.1),
            'scheduling': self._live_mode,
            'timezone': self._timezone,
            'queue_max_size': params.get('queue_max_size', 1_000_000)
        }

        self._logger.debug(
            'Initializing batcher',
            batcher_parameters=batcher_parameters
        )
        try:
            self._batcher = TimestampsBatcher(
                **batcher_parameters    # type: ignore[arg-type]
            )
        except ValueError as e:
            raise PluginConfigurationError(f'Wrong batching parameters: {e}')

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
            self._logger.debug('Generation task was ended with success')
        except Exception:
            self._logger.error('Generation task was ended with errors')
        finally:
            self._logger.debug('Closing batcher')
            self._batcher.close()

    def _add_timestamps(self, timestamps: NDArray[datetime64]) -> None:
        """Add timestamps to batcher with handling overflowing.

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
                        first=timestamps[0],
                        last=timestamps[-1],
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
            self._logger.debug(
                'Submitting generation task to thread pool',
                live_mode=self._live_mode
            )
            future = executor.submit(
                (
                    self._generate_live
                    if self._live_mode
                    else self._generate_sample
                ),
                self._add_timestamps
            )
            future.add_done_callback(self._handle_done_future)

            self._logger.debug('Start scrolling batches')
            yield from self._batcher.scroll()

            self._logger.debug('Finishing generation task')
            try:
                future.result()
            except Exception as e:
                logger.exception('Error during generation')
                raise PluginRuntimeError(str(e))

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
    def live_mode(self) -> bool:
        """Status of live mode of the plugin."""
        return self._live_mode

    def _normalize_daterange(
        self,
        start: VersatileDatetime,
        end: VersatileDatetime,
        none_start: NoneStartPoint = 'min'
    ) -> tuple[datetime, datetime]:
        """Normalize date range for specified parameters.

        Notes
        -----
        See documentation string of `normalize_versatile_daterange`
        """
        self._logger.debug('Normalizing generation date range')
        dt_start, dt_end = normalize_versatile_daterange(
            start=start,
            end=end,
            timezone=self._timezone,
            none_start=none_start
        )

        self._logger.info(
            'Generation date range is normalized',
            start=dt_start.isoformat(),
            end=dt_end.isoformat()
        )

        return (dt_start, dt_end)
