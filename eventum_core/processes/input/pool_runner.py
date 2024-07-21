import logging
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Callable, Iterable

import numpy as np
from eventum_core.processes.input.runner import InputPluginRunner

logger = logging.getLogger(__name__)


class InputPluginPoolRunner:
    """Runner for concurrent execution of multiple input plugin runners."""
    def __init__(
        self,
        runners: Iterable[InputPluginRunner],
    ) -> None:
        self._runners = list(runners)

    def run(
        self,
        on_event: Callable[[np.datetime64, np.int_], Any],
        on_done: Callable[[int, Future], Any]
    ) -> None:
        """Run input plugin runners in thread pool. Each time when
        any input plugin in the pool emits timestamp `on_event`
        callback is called . The second parameter of `on_event`
        callback is an input plugin id (index in plugins list in
        provided config). Once input plugin has ended its execution
        (including due to errors) `on_done` callback is called with
        corresponding future passed to it. So it is expected to call
        `result()` method to obtain result or propagate exception.
        """
        with ThreadPoolExecutor(max_workers=len(self._runners)) as executor:
            for id, runner in enumerate(self._runners, 0):
                future = executor.submit(
                    lambda id=id, runner=runner:        # type: ignore[misc]
                    runner.run(
                        on_event=lambda timestamp: on_event(timestamp, id)
                    )
                )
                future.add_done_callback(
                    lambda done_future, id=id:          # type: ignore[misc]
                    on_done(id, done_future)
                )
