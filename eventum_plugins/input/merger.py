import logging
import time
from concurrent.futures import Future, ThreadPoolExecutor
from queue import Empty, Queue
from typing import Iterable, Iterator

from numpy import datetime64
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

    delay : float
        Time (in seconds) to wait newly incoming batches after
        receiving first batch in a sequence to perform merge

    batch_size : int
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
        delay: float,
        batch_size: int | None
    ) -> None:
        plugins = list(plugins)
        for plugin in plugins:
            if plugin.mode != TimeMode.LIVE:
                raise ValueError(
                    f'Input plugin "{plugin.name}" with ID {plugin.id} '
                    f'is not in {TimeMode.LIVE} mode'
                )

        if delay < self.MIN_DELAY:
            raise ValueError(
                'Parameter `delay` must be greater or equal '
                f'to {self.MIN_DELAY}'
            )

        if batch_size < self.MIN_BATCH_SIZE:
            raise ValueError(
                'Parameter `batch_size` must be greater or equal '
                f'to {self.MIN_BATCH_SIZE}'
            )

        self._plugins = plugins
        self._delay = delay
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
        elements = []
        start_time = time.monotonic()

        while True:
            elapsed = time.monotonic() - start_time
            remaining_time = self._delay - elapsed

            if remaining_time <= 0:
                break

            try:
                item = self._queue.get(timeout=remaining_time)
            except Empty:
                break

            elements.append(item)

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
            while done_count < len(self._plugins):
                arrays = []
                for element in self._consume_queue():
                    if element is None:
                        done_count += 1
                    else:
                        arrays.append(element)

                if not arrays:
                    continue

                sorted_array = merge_arrays(*arrays)

                if self._batch_size is None:
                    yield sorted_array
                else:
                    batches = chunk_array(
                        array=sorted_array,
                        size=self._batch_size
                    )

                    for batch in batches:
                        yield batch
