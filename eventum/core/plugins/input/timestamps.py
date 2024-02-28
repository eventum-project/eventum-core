import time
from typing import Any, Callable, NoReturn
from datetime import datetime


from eventum.core.plugins.input.base import LiveInputPlugin, SampleInputPlugin


class TimestampsInputPlugin(LiveInputPlugin, SampleInputPlugin):
    """Input plugin for generating events in specified timestamps."""

    def __init__(self, timestamps: list[datetime]) -> None:
        self._timestamps = timestamps
        self._timestamps.sort()

    def sample(self, on_event: Callable[[datetime], Any]) -> None:
        for timestamp in self._timestamps:
            on_event(timestamp)

    def live(self, on_event: Callable[[datetime], Any]) -> NoReturn:
        for timestamp in self._timestamps:
            delta_seconds = (timestamp - datetime.now()).total_seconds()

            if delta_seconds < 0:
                continue

            time.sleep(delta_seconds)

            on_event(timestamp)
