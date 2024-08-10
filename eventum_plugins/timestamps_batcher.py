import time
from concurrent.futures import ThreadPoolExecutor
from threading import Condition, Event, RLock
from typing import Iterator

from numpy import concatenate, datetime64
from numpy.typing import NDArray
from pytz import timezone
from pytz.tzinfo import BaseTzInfo

from eventum_plugins.utils.arrays import chunk_array
from eventum_plugins.utils.numpy_time import get_now
from eventum_plugins.utils.timeseries import get_past_slice


class BatcherClosedError(Exception):
    """Trying to add new timestamps to a closed batcher."""


class BatcherFullError(Exception):
    """Maximum size of batcher input queue exceeded."""


class TimestampsBatcher:
    """Batcher of incoming timestamps stream."""

    MIN_BATCH_SIZE = 1
    MIN_BATCH_DELAY = 0.1

    def __init__(
        self,
        batch_size: int | None = 100_000,
        batch_delay: float | None = None,
        scheduling: bool = False,
        timezone: BaseTzInfo = timezone('UTC'),
        queue_max_bytes: int = 1_073_741_824
    ) -> None:
        """
        `batch_size` - maximum size of producing batches, not limited if
        value is `None`;

        `batch_delay` - maximum time (in seconds) for single batch to
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
                'Parameter `batch_size` must be greater or equal to '
                f'{self.MIN_BATCH_SIZE}'
            )

        if batch_delay is not None and batch_delay < self.MIN_BATCH_DELAY:
            raise ValueError(
                'Parameter `batch_delay` must be greater or equal to '
                f'{self.MIN_BATCH_DELAY}'
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
        self._queue_consumed_event = Event()
        self._queue_consumed_event.set()

        self._lock = RLock()

        # When `scheduling` is `False`, the first element is considered
        # to be any element in the queue.
        #
        # When `scheduling` is `True`, the first element is considered
        # to be the element in the queue with the timestamp in the past.
        self._wait_first_item_condition = Condition(self._lock)
        self._flush_condition = Condition(self._lock)

        self._is_closed = False
        self._is_waiting_first_item = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def add(self, timestamps: NDArray[datetime64], block: bool = True) -> None:
        """Add timestamps to batcher."""
        with self._lock:
            if self._is_closed:
                raise BatcherClosedError('Batcher is closed')

            if timestamps.nbytes > self._queue_max_bytes:
                if block:
                    arrays = chunk_array(timestamps, self.queue_max_size)
                    for array in arrays:
                        self._flush_condition.notify_all()
                        self.add(array, block=True)
                else:
                    raise BatcherFullError(
                        'Cannot place timestamps array of size greater than '
                        'batcher input queue maximum size without blocking'
                    )

            if timestamps.nbytes > self.queue_bytes_available:
                if block:
                    self._wait_queue_availability(timestamps.nbytes)
                else:
                    raise BatcherFullError('Batcher queue is full')

            self._timestamp_arrays_queue.append(timestamps)

            if not self._scheduling and self._is_waiting_first_item:
                self._wait_first_item_condition.notify_all()

            if (
                not self._scheduling
                and self._batch_size is not None
                and self.queue_current_size >= self._batch_size
            ):
                self._flush_condition.notify_all()

    def close(self) -> None:
        """Indicate that no new timestamps are going to be added.
        Attempts to add new events after closing will cause
        `BatcherClosedError` exception.
        """
        if self._is_closed:
            return

        with self._lock:
            self._is_closed = True

            if self._is_waiting_first_item:
                self._wait_first_item_condition.notify_all()

            if not self._scheduling:
                self._flush_condition.notify_all()

    def scroll(self) -> Iterator[NDArray[datetime64]]:
        """Scroll through timestamp batches. After iterating over all
        accumulated timestamps execution is blocked until `close`
        method is called or new events are added and new batch is ready
        to be published.
        """
        if self._scheduling:
            with ThreadPoolExecutor(max_workers=1) as executor:
                executor.submit(self._track_past_timestamps)
                yield from self._produce_batches_with_scheduling()
        else:
            yield from self._produce_batches()

    def _wait_queue_availability(self, bytes: int) -> None:
        """Block thread execution until specified number of bytes is
        available to be added in batcher queue.
        """
        while True:
            self._queue_consumed_event.wait()
            self._queue_consumed_event.clear()

            if self.queue_bytes_available >= bytes:
                return

    def _produce_batches(self) -> Iterator[NDArray[datetime64]]:
        """Produce batches of timestamps from input queue without
        timestamp value based scheduling.
        """
        while True:
            with self._lock:
                queue_current_size = self.queue_current_size
                if (
                    not self._is_closed and (
                        self._batch_size is None
                        or queue_current_size < self._batch_size
                    )
                ):
                    if queue_current_size == 0:
                        self._is_waiting_first_item = True
                        self._wait_first_item_condition.wait()
                        self._is_waiting_first_item = False

                    self._flush_condition.wait(timeout=self._batch_delay)

                if self._is_closed and not self._timestamp_arrays_queue:
                    break

                array = concatenate(self._timestamp_arrays_queue)

                if (
                    self._batch_size is not None
                    and array.size > self._batch_size
                ):
                    batches = chunk_array(array, self._batch_size)
                    if len(batches[-1]) < self._batch_size:
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
        """Produce batches of timestamps from input queue with
        timestamp value based scheduling.
        """
        while True:
            with self._lock:
                past_timestamps_count = self._past_timestamps_count
                if (
                    (
                        not self._is_closed or self._timestamp_arrays_queue
                    ) and (
                        self._batch_size is None
                        or past_timestamps_count < self._batch_size
                    )
                ):
                    if past_timestamps_count == 0:
                        self._is_waiting_first_item = True
                        self._wait_first_item_condition.wait()
                        self._is_waiting_first_item = False

                    self._flush_condition.wait(timeout=self._batch_delay)

                if self._is_closed and not self._timestamp_arrays_queue:
                    break

                array = concatenate(self._timestamp_arrays_queue)

                past_timestamps_count = self._past_timestamps_count
                past_timestamps = array[:past_timestamps_count]
                future_timestamps = array[past_timestamps_count:]

                if (
                    self._batch_size is not None
                    and past_timestamps.size > self._batch_size
                ):
                    batches = chunk_array(past_timestamps, self._batch_size)
                    if len(batches[-1]) < self._batch_size:
                        self._timestamp_arrays_queue = [batches.pop()]
                    else:
                        self._timestamp_arrays_queue = []
                else:
                    batches = [past_timestamps, ]
                    self._timestamp_arrays_queue = []

                if future_timestamps.size > 0:
                    self._timestamp_arrays_queue.append(future_timestamps)

                self._queue_consumed_event.set()

            for batch in batches:
                yield batch

    def _track_past_timestamps(self) -> None:
        """Continuously track the number of timestamps in the past."""
        while True:
            with self._lock:
                if self._is_closed and not self._timestamp_arrays_queue:
                    self._flush_condition.notify_all()
                    break

                past_count = self._past_timestamps_count

                if past_count > 0:
                    if self._is_waiting_first_item:
                        self._wait_first_item_condition.notify_all()

                    if (
                        (
                            self._batch_size is not None
                            and past_count >= self._batch_size
                        ) or (
                            self._batch_size is not None
                            and self._batch_delay is None
                            and self._is_closed
                            and past_count == self.queue_current_size
                        )
                    ):
                        self._flush_condition.notify_all()

            time.sleep(0.05)

    @property
    def _past_timestamps_count(self) -> int:
        """Get count of timestamps in input queue that are in the past."""
        now = get_now(self._timezone)

        if not self._timestamp_arrays_queue:
            return 0

        count = 0

        for array in self._timestamp_arrays_queue:
            if array.size == 0:
                continue

            if now < array[0]:
                return count
            elif now > array[-1]:
                count += array.size
            else:
                past_slice = get_past_slice(array, now)
                return count + past_slice.size

        return count

    @property
    def queue_current_bytes(self) -> int:
        """Current size (in bytes) of input queue."""
        return sum(
            [arr.nbytes for arr in self._timestamp_arrays_queue]
        )

    @property
    def queue_current_size(self) -> int:
        """Current size of input queue."""
        return sum(
            [arr.size for arr in self._timestamp_arrays_queue]
        )

    @property
    def queue_bytes_available(self) -> int:
        """Number of bytes currently available to be added to the
        input queue.
        """
        return max(self._queue_max_bytes - self.queue_current_bytes, 0)

    @property
    def queue_max_bytes(self) -> int:
        """Maximum size (in bytes) of input queue."""
        return self._queue_max_bytes

    @property
    def queue_max_size(self) -> int:
        """Maximum size of input queue."""
        return self._queue_max_bytes // 8
