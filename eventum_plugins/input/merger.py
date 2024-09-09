import logging
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime
from typing import Generic, Iterable, Iterator, TypeVar

from numpy import datetime64, searchsorted
from numpy.typing import NDArray

from eventum_plugins.input.base.plugin import InputPlugin
from eventum_plugins.input.enums import TimeMode
from eventum_plugins.input.utils.array_utils import chunk_array, merge_arrays

logger = logging.getLogger(__name__)


T = TypeVar('T')


class AccumulatorClosedError(Exception):
    """Trying to add batches to a closed `BatchesAccumulator`."""


class BatchesAccumulator(Generic[T]):
    """Thread safe accumulator of batches."""

    def __init__(self):
        self._lock = threading.RLock()
        self._batches = []
        self._is_closed = False

    def add(self, batch: T) -> None:
        """Add batch to accumulator.

        Parameters
        ----------
        batch : T
            Batch to add

        Raises
        ------
        AccumulatorClosedError
            If accumulator is closed
        """
        with self._lock:
            if self._is_closed:
                raise AccumulatorClosedError

            self._batches.append(batch)

    def consume(self) -> list[T]:
        """Get all accumulated batches.

        Returns
        -------
        list[T]
            List of accumulated baches
        """
        with self._lock:
            batches = self._batches
            self._batches = []

        return batches

    def close(self) -> None:
        """Close the accumulator."""
        with self._lock:
            self._is_closed = True

    @property
    def closed(self) -> bool:
        """Closed status of accumulator."""
        with self._lock:
            return self._is_closed


class InputPluginsLiveMerger:
    """Merger of live timestamp generation flows of multiple input
    plugins. Timestamp batches generating by provided input plugins
    are merged with sorting and re-batched, so timestamps in output
    batches are guaranteed to be sorted within one and across other
    batches.

    Attributes
    ----------
    MIN_DELAY : float
        Minimum value for parameter `delay` that can be configured

    MIN_BATCH_SIZE : int
        Minimum value for parameter `batch_size` that can be configured

    Parameters
    ----------
    plugins : Iterable[InputPlugin]
        Input plugins to merge

    target_delay : float
        Time (in seconds) that indicates how long plugins can delay
        publishing batches

    batch_size : int | None
        Maximum size of producing batches after merge, not limited if
        value is `None`

    Raises
    ------
    ValueError
        If some of the provided plugins are not in live mode

    ValueError
        If `delay` or `batch_size` parameters is out of range

    ValueError
        If number of provided plugins are less than one
    """

    MIN_DELAY = 0.1
    MIN_BATCH_SIZE = 1

    def __init__(
        self,
        plugins: Iterable[InputPlugin],
        target_delay: float,
        batch_size: int | None
    ) -> None:
        plugins = list(plugins)
        if not plugins:
            raise ValueError('At least one plugin must be provided')

        for plugin in plugins:
            if plugin.mode != TimeMode.LIVE:
                raise ValueError(
                    f'Input plugin "{plugin.name}" with ID {plugin.id} '
                    f'is not in {TimeMode.LIVE} mode'
                )

        if target_delay < self.MIN_DELAY:
            raise ValueError(
                'Parameter `delay` must be greater or equal '
                f'to {self.MIN_DELAY}'
            )

        if batch_size is not None and batch_size < self.MIN_BATCH_SIZE:
            raise ValueError(
                'Parameter `batch_size` must be greater or equal '
                f'to {self.MIN_BATCH_SIZE}'
            )

        self._delay = target_delay
        self._batch_size = batch_size
        self._plugins = {idx: plugin for idx, plugin in enumerate(plugins)}
        self._accumulators: dict[
            int,
            BatchesAccumulator[NDArray[datetime64]]
        ] = {idx: BatchesAccumulator() for idx in self._plugins.keys()}
        self._active_plugin_indices = list(self._plugins.keys())
        self._overlapped_future_part: NDArray[datetime64] | None = None

    def _execute_plugin(
        self,
        plugin: InputPlugin,
        accumulator: BatchesAccumulator
    ) -> None:
        """Execute plugin with putting generating timestamps to
        accumulator.

        Parameters
        ----------
        plugin : InputPlugin
            Input plugin to execute

        accumulator : BatchesAccumulator
            Accumulator for the plugin batches
        """
        try:
            for batch in plugin.generate():
                accumulator.add(batch)
        except Exception as e:
            raise e
        finally:
            accumulator.close()

    def _handle_done_future(
        self,
        future: Future,
        plugin: InputPlugin
    ) -> None:
        """Handle done future with executed plugin.

        Parameters
        ----------
        future : Future
            Future to handle

        plugin : InputPlugin
            Input plugin related to provided `future`
        """
        try:
            future.result()
        except Exception as e:
            logger.error(
                f'Error occurred in "{plugin.name}" plugin '
                f'with ID {plugin.id}: {e}'
            )

    def _consume_elements(self) -> list[NDArray[datetime64]]:
        """Consume elements from accumulators within configured delay
        time.

        Returns
        -------
        list[NDArray[datetime64]]
            List of consumed elements
        """
        if not self._active_plugin_indices:
            return []

        time.sleep(self._delay)

        elements: list[NDArray[datetime64]] = []
        done_indices: list[int] = []

        for idx in self._active_plugin_indices:
            accumulator = self._accumulators[idx]
            elements.extend(accumulator.consume())

            if accumulator.closed:
                done_indices.append(idx)

        for idx in done_indices:
            self._active_plugin_indices.remove(idx)

        return elements

    def generate(self) -> Iterator[NDArray[datetime64]]:
        """Start timestamps generation of input plugins concurrently.

        Yields
        ------
        NDArray[datetime64]
            Timestamp batches
        """
        with ThreadPoolExecutor(max_workers=len(self._plugins)) as executor:
            for idx, plugin in self._plugins.items():
                future = executor.submit(
                    self._execute_plugin,
                    plugin,
                    self._accumulators[idx]
                )
                future.add_done_callback(
                    lambda future, plugin=plugin:
                    self._handle_done_future(future, plugin)
                )

            while (
                self._active_plugin_indices
                or self._overlapped_future_part is not None
            ):
                batches = self._consume_elements()

                if self._overlapped_future_part is not None:
                    batches.append(self._overlapped_future_part)
                    self._overlapped_future_part = None

                if not batches:
                    continue

                # after getting batches within delay time we need to wait for
                # overlapping batches that are not yet captured
                # Scheme: :
                #      capturing starts after first batch is received
                #      |     capturing ends after the delay has elapsed
                #      |     | overlapping batch is published after capturing !
                # -----|     | |   that's why we should wait delay once again
                #   ----- +++++|   |
                #      ----- | |   |
                #

                if self._active_plugin_indices:
                    # finding latest timestamp that will be a cutoff point
                    latest_timestamp = datetime64(datetime.min)
                    for batch in batches:
                        if batch[-1] > latest_timestamp:
                            latest_timestamp = batch[-1]

                    overlapped_batches = self._consume_elements()

                    if overlapped_batches:
                        overlapped = merge_arrays(overlapped_batches)
                        index = searchsorted(
                            a=overlapped,
                            v=latest_timestamp,
                            side='right'
                        )
                        overlapped_part = overlapped[:index]
                        future_part = overlapped[index:]

                        if overlapped_part.size > 0:
                            batches.append(overlapped_part)

                        if future_part.size > 0:
                            self._overlapped_future_part = future_part

                sorted_array = merge_arrays(batches)

                if self._batch_size is None:
                    yield sorted_array
                else:
                    batches = chunk_array(
                        array=sorted_array,
                        size=self._batch_size
                    )

                    for batch in batches:
                        yield batch
