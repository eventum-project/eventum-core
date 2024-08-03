from math import ceil
from queue import Queue
from typing import Iterator

from numpy import array_split, datetime64
from numpy.typing import NDArray
from pytz.tzinfo import BaseTzInfo


class BatcherClosedError(Exception):
    """Trying to add new timestamps to a closed batcher."""


class BatcherFullError(Exception):
    """Maximum size of batcher input queue exceeded."""


GiB = 1_073_741_824


class TimestampsBatcher:
    """Batcher of timestamps. Instances of this class are intended to
    be used in several threads - one is for adding timestamps, and
    another one for scrolling through output timestamp batches.
    """
    MIN_BATCH_SIZE = 1
    MIN_BATCH_DELAY = 0.1

    # To limit size (in bytes) of queue wee need to know element size
    # which is a numpy array with datetime64 objects

    # Maximum size of numpy array in a queue. If array size is greater
    # on adding then it is splitted to sub arrays
    QUEUE_MAX_ARRAY_SIZE = 1_000_000

    # Numpy datetime64 object size in bytes
    TIMESTAMP_SIZE = 8

    def __init__(
        self,
        batch_size: int | None = 100_000,
        batch_delay: float | None = None,
        scheduling: bool = False,
        timezone: BaseTzInfo | None = None,
        max_queue_bytes: int = 1 * GiB
    ) -> None:
        """
        `batch_size` - maximum size of produces batches, not limited if
        value is `None`;

        `batch_delay` - maximum time (in seconds) for batch to
        accumulate incoming timestamps, not limited if value is `None`;

        `scheduling` - whether to respect timestamp values and publish
        them according to real time;

        `timezone` - timezone of incoming timestamps, must be provided
        when `scheduling` is `True`;

        `max_queue_bytes` - maximum size (in bytes) of batcher queue
        for incoming events;
        """
        if batch_size is None and batch_delay is None:
            raise ValueError(
                'Parameters `batch_size` and `batch_delay` '
                'cannot be both `None`'
            )

        if batch_size is not None and batch_size < self.MIN_BATCH_SIZE:
            raise ValueError(
                'Parameter `batch_size` must be greater or equal to'
                f'{self.MIN_BATCH_SIZE}'
            )

        if batch_delay is not None and batch_delay < self.MIN_BATCH_DELAY:
            raise ValueError(
                'Parameter `batch_delay` must be greater or equal to '
                f'{self.MIN_BATCH_DELAY}'
            )

        if scheduling and timezone is None:
            raise ValueError(
                'Parameter `timezone` must be set when `scheduling` is `True`'
            )

        min_queue_bytes = self.QUEUE_MAX_ARRAY_SIZE * self.TIMESTAMP_SIZE

        if max_queue_bytes < min_queue_bytes:
            raise ValueError(
                '`max_queue_bytes` must be greater or equal to '
                f'{min_queue_bytes}'
            )

        self._batch_size = batch_size
        self._batch_delay = batch_delay
        self._scheduling = scheduling
        self._timezone = timezone

        queue_size = max_queue_bytes // (
            self.QUEUE_MAX_ARRAY_SIZE * self.TIMESTAMP_SIZE
        )
        self._timestamp_arrays_queue: Queue[NDArray[datetime64]] = Queue(
            maxsize=max(queue_size, 1)
        )

        self._is_closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def _produce_batches(self) -> Iterator[NDArray[datetime64]]:
        ...

    def _produce_batches_with_scheduling(
        self
    ) -> Iterator[NDArray[datetime64]]:
        ...

    def scroll(self) -> Iterator[NDArray[datetime64]]:
        """Scroll through timestamps batches. After iterating over all
        accumulated timestamps execution is blocked until `finish`
        method is called or new events are added and new batch is ready
        to be published.
        """
        if self._scheduling:
            yield from self._produce_batches_with_scheduling()
        else:
            yield from self._produce_batches()

    def close(self) -> None:
        """Indicate that no new timestamps are going to be added.
        Attempts to add new events after closing will cause
        `BatcherClosedError` exception.
        """
        self._is_closed = True
        self._timestamp_arrays_queue.put()

    def add(self, timestamps: NDArray[datetime64], block: bool = True) -> None:
        """Add timestamps to batcher."""
        if self._is_closed:
            raise BatcherClosedError('Batcher is closed')

        if timestamps.size > self.QUEUE_MAX_ARRAY_SIZE:
            arrays = array_split(
                ary=timestamps,
                indices_or_sections=ceil(
                    timestamps.size / self.QUEUE_MAX_ARRAY_SIZE
                )
            )
        else:
            arrays = [timestamps, ]

        queue = self._timestamp_arrays_queue
        if (queue.maxsize - queue.qsize()) < len(arrays) and block is False:
            raise BatcherFullError('Batcher queue is full')

        for arr in arrays:
            self._timestamp_arrays_queue.put(arr)
