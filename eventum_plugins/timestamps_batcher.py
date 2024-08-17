import time
from concurrent.futures import ThreadPoolExecutor
from threading import Condition, RLock
from typing import Iterator

from numpy import concatenate, datetime64
from numpy.typing import NDArray
from pytz import timezone
from pytz.tzinfo import BaseTzInfo

from eventum_plugins.utils.array_utils import chunk_array, get_past_slice
from eventum_plugins.utils.time_utils import get_now


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
        queue_max_size: int = 1_000_000_000
    ) -> None:
        """
        `batch_size` - maximum size of producing batches, not limited if
        value is `None`;

        `batch_delay` - maximum time (in seconds) for single batch to
        accumulate incoming timestamps, not limited if value is `None`;

        `scheduling` - whether to respect timestamp values and publish
        them according to real time;

        `timezone` - timezone of incoming timestamps, used to track
        current time when `scheduling` is `True`;

        `max_queue_size` - maximum size of batcher queue for incoming
        events;
        """
        if batch_size is None and batch_delay is None:
            raise ValueError(
                'Parameters `batch_size` and `batch_delay` '
                'cannot be both `None`'
            )

        if (
            batch_size is not None
            and not (self.MIN_BATCH_SIZE <= batch_size <= queue_max_size)
        ):
            raise ValueError(
                'Parameter `batch_size` must be in range '
                f'[{self.MIN_BATCH_SIZE}; {queue_max_size}]'
            )

        if batch_delay is not None and batch_delay < self.MIN_BATCH_DELAY:
            raise ValueError(
                'Parameter `batch_delay` must be greater or equal to '
                f'{self.MIN_BATCH_DELAY}'
            )

        if queue_max_size < 1:
            raise ValueError('`queue_max_size` must be greater than 1')

        self._batch_size = batch_size
        self._batch_delay = batch_delay
        self._scheduling = scheduling
        self._timezone = timezone
        self._queue_max_size = queue_max_size

        self._timestamp_arrays_queue: list[NDArray[datetime64]] = list()
        self._lock = RLock()

        # When `scheduling` is `False`, the first item is considered
        # to be any item in the queue.
        #
        # When `scheduling` is `True`, the first item is considered
        # to be the item in the queue with the timestamp in the past.
        self._wait_first_item_condition = Condition(self._lock)
        self._flush_condition = Condition(self._lock)
        self._queue_consumed_condition = Condition(self._lock)

        self._is_closed = False
        self._is_waiting_first_item = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def add(self, timestamps: NDArray[datetime64], block: bool = True) -> None:
        """Add timestamps to batcher. If it is enough available size to
        in input queue to put timestamps and block is `True` then method
        blocks execution until queue can fit timestamps. If `block` is
        `False` and there isn't enough available size at current moment
        in input queue, then `BatcherFullError` is raised.
        """
        if timestamps.size == 0:
            return

        with self._lock:
            if self._is_closed:
                raise BatcherClosedError('Batcher is closed')

            if not block and timestamps.size > self.queue_available_size:
                raise BatcherFullError(
                    'Not enough available size in batcher queue'
                )

            while timestamps.size > 0:
                if self.queue_available_size == 0:
                    self._queue_consumed_condition.wait()

                queue_available_size = self.queue_available_size
                addition = timestamps[:queue_available_size]
                timestamps = timestamps[queue_available_size:]

                self._timestamp_arrays_queue.append(addition)

                # With active scheduling first item and flush conditions
                # are controlled by `_track_past_timestamps`
                if not self._scheduling:
                    if self._is_waiting_first_item:
                        self._wait_first_item_condition.notify_all()
                        self._is_waiting_first_item = False
                    elif (
                        self._batch_size is not None
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

            if not self._scheduling:
                if self._is_waiting_first_item:
                    self._wait_first_item_condition.notify_all()
                    self._is_waiting_first_item = False
                else:
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

    def _produce_batches(self) -> Iterator[NDArray[datetime64]]:
        """Produce batches of timestamps from input queue without
        timestamp value based scheduling.
        """
        while True:
            with self._lock:
                if not self._is_closed and not self._timestamp_arrays_queue:
                    self._is_waiting_first_item = True
                    self._wait_first_item_condition.wait()

                if self._is_closed and not self._timestamp_arrays_queue:
                    break

                queue_current_size = self.queue_current_size
                if (
                    not self._is_closed and (
                        self._batch_size is None
                        or queue_current_size < self._batch_size
                    )
                ):
                    self._flush_condition.wait(timeout=self._batch_delay)

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

                self._queue_consumed_condition.notify_all()

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
                    (not self._is_closed or self._timestamp_arrays_queue)
                    and past_timestamps_count == 0
                ):
                    self._is_waiting_first_item = True
                    self._wait_first_item_condition.wait()

                if self._is_closed and not self._timestamp_arrays_queue:
                    break

                past_timestamps_count = self._past_timestamps_count
                if (
                    self._batch_size is None
                    or past_timestamps_count < self._batch_size
                ):
                    self._flush_condition.wait(timeout=self._batch_delay)

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

                self._queue_consumed_condition.notify_all()

            for batch in batches:
                yield batch

    def _track_past_timestamps(self) -> None:
        """Continuously track the number of timestamps in the past."""
        while True:
            with self._lock:
                if (
                    self._is_closed
                    and not self._timestamp_arrays_queue
                ):
                    if self._is_waiting_first_item:
                        self._wait_first_item_condition.notify_all()
                        self._is_waiting_first_item = False
                    break

                past_count = self._past_timestamps_count

                if past_count > 0:
                    if self._is_waiting_first_item:
                        self._wait_first_item_condition.notify_all()
                        self._is_waiting_first_item = False
                    elif (
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

            time.sleep(self.MIN_BATCH_DELAY / 2)

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
    def queue_current_size(self) -> int:
        """Current size of input queue."""
        return sum(
            [arr.size for arr in self._timestamp_arrays_queue]
        )

    @property
    def queue_available_size(self) -> int:
        """Number of elements currently available to be added to the
        input queue.
        """
        return max(self.queue_max_size - self.queue_current_size, 0)

    @property
    def queue_max_size(self) -> int:
        """Maximum size of input queue."""
        return self._queue_max_size
