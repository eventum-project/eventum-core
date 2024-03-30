import time
from datetime import datetime
from typing import Any, Callable

import eventum.core.settings as settings
from eventum.core.plugins.input.base import LiveInputPlugin, SampleInputPlugin
from eventum.utils.numpy_time import timedelta_to_seconds, utcnow
from eventum.utils.timeseries import get_future_slice
from numpy import array, datetime64


class TimestampsInputPlugin(LiveInputPlugin, SampleInputPlugin):
    """Input plugin for generating events in specified timestamps."""

    def __init__(self, timestamps: list[datetime]) -> None:
        self._timestamps = array(
            [ts.astimezone().replace(tzinfo=None) for ts in timestamps],
            dtype='datetime64'
        )
        self._timestamps.sort()

    def sample(self, on_event: Callable[[datetime64], Any]) -> None:
        for timestamp in self._timestamps:
            on_event(timestamp)

    def live(self, on_event: Callable[[datetime64], Any]) -> None:
        now = utcnow()
        future_timestamps = get_future_slice(
            timestamps=self._timestamps,
            now=now
        )
        for timestamp in future_timestamps:
            wait_seconds = timedelta_to_seconds(timestamp - now)

            if wait_seconds > settings.TIME_PRECISION >= 0:
                time.sleep(wait_seconds)
                now = utcnow()

            on_event(timestamp)
