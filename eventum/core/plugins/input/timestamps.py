import time
from datetime import datetime
from typing import Any, Callable, NoReturn

import eventum.core.settings as settings
from eventum.core.plugins.input.base import LiveInputPlugin, SampleInputPlugin
from eventum.utils.timeseries import get_future_slice


class TimestampsInputPlugin(LiveInputPlugin, SampleInputPlugin):
    """Input plugin for generating events in specified timestamps."""

    def __init__(self, timestamps: list[datetime]) -> None:
        self._timestamps = timestamps
        self._timestamps.sort()

    def sample(self, on_event: Callable[[datetime], Any]) -> None:
        for timestamp in self._timestamps:
            on_event(timestamp)

    def live(self, on_event: Callable[[datetime], Any]) -> NoReturn:
        for timestamp in get_future_slice(self._timestamps, datetime.now()):
            wait_seconds = (timestamp - datetime.now()).total_seconds()

            if wait_seconds > settings.AHEAD_PUBLICATION_SECONDS >= 0:
                time.sleep(wait_seconds)

            on_event(timestamp)
