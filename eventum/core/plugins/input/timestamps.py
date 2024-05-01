import time
from datetime import datetime
from typing import Any, Callable

from numpy import array, datetime64

import eventum.core.settings as settings
from eventum.core.models.application_config import TimestampsInputConfig
from eventum.core.plugins.input.base import (InputPluginConfigurationError,
                                             LiveInputPlugin,
                                             SampleInputPlugin)
from eventum.utils.numpy_time import get_now, timedelta_to_seconds
from eventum.utils.timeseries import get_future_slice


class TimestampsInputPlugin(LiveInputPlugin, SampleInputPlugin):
    """Input plugin for generating events in specified timestamps."""

    def __init__(self, timestamps: list[datetime]) -> None:
        if not timestamps:
            raise InputPluginConfigurationError(
                'At least one timestamp must be in list'
            )

        self._timestamps = array(
            [
                ts.astimezone(settings.TIMEZONE).replace(tzinfo=None)
                if ts.tzinfo else ts.replace(tzinfo=None)
                for ts in timestamps
            ],
            dtype='datetime64'
        )
        self._timestamps.sort()

    def sample(self, on_event: Callable[[datetime64], Any]) -> None:
        for timestamp in self._timestamps:
            on_event(timestamp)

    def live(self, on_event: Callable[[datetime64], Any]) -> None:
        now = get_now()
        future_timestamps = get_future_slice(
            timestamps=self._timestamps,
            now=now
        )
        for timestamp in future_timestamps:
            wait_seconds = timedelta_to_seconds(timestamp - now)

            if wait_seconds > settings.TIME_PRECISION >= 0:
                time.sleep(wait_seconds)    # type: ignore
                now = get_now()

            on_event(timestamp)

    @classmethod
    def create_from_config(
        cls,
        config: TimestampsInputConfig       # type: ignore
    ) -> 'TimestampsInputPlugin':
        return TimestampsInputPlugin(timestamps=config)


def load_plugin():
    """Return class of plugin from current module."""
    return TimestampsInputPlugin
