import time
from datetime import datetime
from typing import Any, Callable

from numpy import array, datetime64, timedelta64
from numpy.typing import NDArray
from pydantic import Field
from pytz.tzinfo import DstTzInfo

from eventum_plugins.input.base import (InputPluginBaseConfig,
                                        LiveInputPluginMixin,
                                        SampleInputPluginMixin)
from eventum_plugins.utils.timeseries import get_future_slice


class TimestampsInputConfig(InputPluginBaseConfig):
    source: tuple[datetime] = Field(..., min_length=1)


class TimestampsInputPlugin(LiveInputPluginMixin, SampleInputPluginMixin):
    """Input plugin for generating events in specified timestamps."""

    def __init__(self, config: TimestampsInputConfig, tz: DstTzInfo) -> None:
        self._timestamps: NDArray[datetime64] = array(
            [
                ts.astimezone(tz=tz).replace(tzinfo=None)
                if ts.tzinfo else ts.replace(tzinfo=None)
                for ts in config.source
            ],
            dtype='datetime64'
        )
        self._tz = tz

    def sample(self, on_event: Callable[[datetime64], Any]) -> None:
        for timestamp in self._timestamps:
            on_event(timestamp)

    def live(self, on_event: Callable[[datetime64], Any]) -> None:
        now = datetime64(
            datetime.now(tz=self._tz).replace(tzinfo=None)
        )
        future_timestamps = get_future_slice(
            timestamps=self._timestamps,
            after=now
        )
        for timestamp in future_timestamps:
            wait_seconds = (timestamp - now) / timedelta64(1000000, 'us')

            if wait_seconds > 0:
                time.sleep(wait_seconds)    # type: ignore
                now = datetime64(
                    datetime.now(tz=self._tz).replace(tzinfo=None)
                )

            on_event(timestamp)


PLUGIN_CLASS = TimestampsInputPlugin
CONFIG_CLASS = TimestampsInputConfig
