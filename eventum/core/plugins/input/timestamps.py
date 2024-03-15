import time
from datetime import datetime
from typing import Any, Callable

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

    def live(self, on_event: Callable[[datetime], Any]) -> None:
        future_timestamps = get_future_slice(
            timestamps=self._timestamps,
            now=datetime.now().astimezone()
        )
        for timestamp in future_timestamps:
            wait_seconds = (
                timestamp - datetime.now().astimezone()
            ).total_seconds()

            if wait_seconds > settings.AHEAD_PUBLICATION_SECONDS >= 0:
                time.sleep(wait_seconds)

            on_event(timestamp)
