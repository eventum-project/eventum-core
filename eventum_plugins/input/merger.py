import logging
import time
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime
from queue import Empty, Queue
from typing import Iterable, Iterator

from numpy import datetime64, searchsorted
from numpy.typing import NDArray

from eventum_plugins.input.base.plugin import InputPlugin
from eventum_plugins.input.enums import TimeMode
from eventum_plugins.input.utils.array_utils import chunk_array, merge_arrays

logger = logging.getLogger(__name__)


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

        self._plugins = plugins
        self._delay = target_delay
        self._batch_size = batch_size
        self._queue = Queue()

    def _execute_plugin(self, plugin: InputPlugin) -> None:
        """Execute plugin with putting generating timestamps to queue.

        Parameters
        ----------
        plugin : InputPlugin
            Input plugin to execute

        Notes
        -----
        Once plugin execution is done `None` is placed in the queue
        as sentinel
        """
        try:
            for batch in plugin.generate():
                self._queue.put(batch)
        except Exception as e:
            raise e
        finally:
            self._queue.put(None)

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

    def _consume_queue(self) -> list[NDArray[datetime64] | None]:
        """Consume elements from queue within configured delay time.

        Returns
        -------
        list[NDArray[datetime64]]
            List of consumed elements
        """
        try:
            item = self._queue.get(timeout=self._delay)
        except Empty:
            return []

        elements = [item]
        start_time = time.monotonic()
        remaining_time = self._delay

        while True:
            try:
                item = self._queue.get(timeout=remaining_time)
            except Empty:
                break

            elements.append(item)

            elapsed = time.monotonic() - start_time
            remaining_time = self._delay - elapsed

            if remaining_time <= 0:
                break

        return elements

    def generate(self) -> Iterator[NDArray[datetime64]]:
        """Start timestamps generation of input plugins concurrently.

        Yields
        ------
        NDArray[datetime64]
            Timestamp batches
        """
        with ThreadPoolExecutor(max_workers=len(self._plugins)) as executor:
            for plugin in self._plugins:
                future = executor.submit(self._execute_plugin, plugin)
                future.add_done_callback(
                    lambda future, plugin=plugin:
                    self._handle_done_future(future, plugin)
                )

            done_count = 0
            plugins_count = len(self._plugins)

            while done_count < plugins_count:
                batches = []
                for element in self._consume_queue():
                    if element is None:
                        done_count += 1
                    else:
                        batches.append(element)

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

                if done_count < plugins_count:
                    # finding latest timestamp that will be a cutoff point
                    latest_timestamp = datetime64(datetime.min)
                    for batch in batches:
                        if batch[-1] > latest_timestamp:
                            latest_timestamp = batch[-1]

                    overlapped_batches = []
                    future_done_count = 0
                    for element in self._consume_queue():
                        if element is None:
                            future_done_count += 1
                        else:
                            overlapped_batches.append(element)

                    if overlapped_batches:
                        overlapped_timestamps = merge_arrays(
                            *overlapped_batches
                        )
                        index = searchsorted(
                            a=overlapped_timestamps,
                            v=latest_timestamp,
                            side='right'
                        )
                        overlapped_part_batches = overlapped_timestamps[:index]
                        future_part_batches = overlapped_timestamps[index:]

                        if overlapped_part_batches.size > 0:
                            batches.append(overlapped_part_batches)

                        if future_part_batches.size > 0:
                            self._queue.put(future_part_batches)

                            # restore sentinels to queue
                            for _ in range(future_done_count):
                                self._queue.put(None)

                sorted_array = merge_arrays(*batches)

                if self._batch_size is None:
                    yield sorted_array
                else:
                    batches = chunk_array(
                        array=sorted_array,
                        size=self._batch_size
                    )

                    for batch in batches:
                        yield batch
