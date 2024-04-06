from threading import Condition, RLock, Thread
from typing import Any, Callable

import numpy as np
from numpy.typing import NDArray


class Batcher:
    """Background thread-safe worker to collect incoming elements to
    batches and performing callback on them.
    """

    def __init__(
        self,
        size: int,
        timeout: float,
        callback: Callable[[NDArray[Any]], Any]
    ) -> None:
        self._size = size
        self._timeout = timeout
        self._callback = callback

        self._batch: list[Any] = []

        self._is_waiting_first_element = False
        self._is_flushed = False
        self._is_finished = False

        self._lock = RLock()
        self._first_element_condition = Condition(self._lock)
        self._size_condition = Condition(self._lock)

        self._thread = Thread(target=self._run_cycle)
        self._thread.start()

    def _run_cycle(self):
        """Target method for thread that tracks conditions."""
        while True:
            with self._lock:
                self._is_waiting_first_element = True
                self._is_flushed = False
                self._is_finished = False

                self._first_element_condition.wait()

                if self._is_finished:
                    return

                self._size_condition.wait(self._timeout)

                if self._is_finished:
                    return

                if self._is_flushed:
                    continue

                batch = self._batch
                self._batch = []

            self._flush_batch(batch)

    def _flush_batch(self, batch):
        """Perform callback on current batch."""
        if batch:
            self._callback(np.array(batch))

    def add(self, element: Any) -> None:
        """Add element to current batch."""

        complete_batch = None

        with self._lock:
            self._batch.append(element)

            if len(self._batch) >= self._size:
                complete_batch = self._batch
                self._batch = []

                self._is_flushed = True
                self._size_condition.notify_all()
            elif self._is_waiting_first_element:
                self._is_waiting_first_element = False
                self._first_element_condition.notify_all()

        if complete_batch:
            self._flush_batch(complete_batch)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        with self._lock:
            self._is_finished = True
            self._first_element_condition.notify_all()
            self._size_condition.notify_all()

        self._thread.join()
        self._flush_batch(self._batch)
