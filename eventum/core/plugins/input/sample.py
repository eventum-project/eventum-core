from datetime import datetime
from typing import Any, Callable

from eventum.core.plugins.input.base import SampleInputPlugin


class SampleInputPlugin(SampleInputPlugin):
    """Input plugin for generating specified count of events. Use it
    when you only need to produce event facts and timestamps aren't
    important. For all events timestamps are the same and have a
    symbolic value of time when sample generating process was started.
    """

    def __init__(self, count: int) -> None:
        self._count = count

    def sample(self, on_event: Callable[[datetime], Any]) -> None:
        timestamp = datetime.now()

        for _ in range(self._count):
            on_event(timestamp)
