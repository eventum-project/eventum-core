from threading import Condition, Event, RLock
from typing import Iterator

from numpy import concatenate, datetime64
from numpy.typing import NDArray
from pytz.tzinfo import BaseTzInfo

from eventum_plugins.utils.arrays import chunk_array


class BatcherClosedError(Exception):
    """Trying to add new timestamps to a closed batcher."""


class BatcherFullError(Exception):
    """Maximum size of batcher input queue exceeded."""


class TimestampsBatcher:
    """Batcher of timestamps. Instances of this class are intended to
    be used in several threads - one is for adding timestamps, and
    another one for scrolling through output timestamp batches.
    """
    MIN_BATCH_SIZE = 1
    MIN_BATCH_DELAY = 0.1

    def __init__(
        self,
        batch_size: int | None = 100_000,
        batch_delay: float | None = None,
        scheduling: bool = False,
        timezone: BaseTzInfo | None = None,
        queue_max_bytes: int = 1_073_741_824
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
        if queue_max_bytes < 8:
            raise ValueError(
                '`max_queue_bytes` must be greater or equal to 8'
            )

        self._batch_size = batch_size
        self._batch_delay = batch_delay
        self._scheduling = scheduling
        self._timezone = timezone
        self._queue_max_bytes = queue_max_bytes

        self._timestamp_arrays_queue: list[NDArray[datetime64]] = list()
        self._partial_batch: NDArray[datetime64] | None = None
        self._queue_current_bytes = 0
        self._queue_consumed_event = Event()

        self._queue_current_size = 0
        self._lock = RLock()
        self._flush_condition = Condition(self._lock)

        self._is_closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def _produce_batches(self) -> Iterator[NDArray[datetime64]]:
        """Produce batches of timestamps from input queue without
        timestamp value based scheduling.
        """
        while not self._is_closed:
            with self._lock:
                if (
                    self._batch_size is None
                    or self._queue_current_size < self._batch_size
                ):
                    self._flush_condition.wait(timeout=self._batch_delay)

                if not self._timestamp_arrays_queue:
                    continue

                array = concatenate(self._timestamp_arrays_queue)

                if self._batch_size is not None:
                    batches = chunk_array(array, self._batch_size)
                    if (
                        len(batches) > 1
                        and len(batches[-1]) < self._batch_size
                    ):
                        self._timestamp_arrays_queue = [batches.pop(), ]
                    else:
                        self._timestamp_arrays_queue = []
                else:
                    batches = [array, ]
                    self._timestamp_arrays_queue = []

                self._queue_consumed_event.set()

            for batch in batches:
                yield batch

    def _produce_batches_with_scheduling(
        self
    ) -> Iterator[NDArray[datetime64]]:
        ...

    def _wait_queue_availability(self, bytes: int) -> None:
        """Block thread execution until specified number of bytes is
        available to be added in batcher queue.
        """
        while True:
            self._queue_consumed_event.wait()
            self._queue_consumed_event.clear()

            if self.queue_bytes_available >= bytes:
                return

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
        if self._is_closed:
            return

        with self._lock:
            self._is_closed = True
            self._flush_condition.notify_all()

    def add(self, timestamps: NDArray[datetime64], block: bool = True) -> None:
        """Add timestamps to batcher."""
        with self._lock:
            if self._is_closed:
                raise BatcherClosedError('Batcher is closed')

            if (
                timestamps.nbytes > self.queue_bytes_available
                and block is False
            ):
                raise BatcherFullError('Batcher queue is full')

            self._wait_queue_availability(timestamps.nbytes)
            self._timestamp_arrays_queue.append(timestamps)

            if (
                self._batch_size is not None
                and self._queue_current_size >= self._batch_size
            ):
                self._flush_condition.notify_all()

    @property
    def queue_current_bytes(self) -> int:
        """Return current size (in bytes) of batcher input queue."""
        return sum(
            [arr.nbytes for arr in self._timestamp_arrays_queue]
        )

    @property
    def queue_current_size(self) -> int:
        """Return current size of batcher input queue."""
        return sum(
            [arr.size for arr in self._timestamp_arrays_queue]
        )

    @property
    def queue_bytes_available(self) -> int:
        """Number of bytes currently available to be added to the
        batcher input queue.
        """
        return max(self._queue_max_bytes - self.queue_current_bytes, 0)
