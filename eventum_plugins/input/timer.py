import time
from typing import Any, Callable

from numpy import datetime64, timedelta64
from pydantic import Field
from pytz.tzinfo import BaseTzInfo

from eventum_plugins.input.base import InputPluginBaseConfig, LiveInputPlugin
from eventum_plugins.utils.numpy_time import get_now, timedelta_to_seconds


class TimerInputConfig(InputPluginBaseConfig, frozen=True):
    seconds: float = Field(..., ge=0.1)
    count: int = Field(..., ge=1)
    repeat: bool


class TimerInputPlugin(LiveInputPlugin):
    """Input plugin for generating events after specified number of
    seconds.
    """

    def __init__(self, config: TimerInputConfig, tz: BaseTzInfo) -> None:
        self._seconds = config.seconds
        self._count = config.count
        self._repeat = config.repeat
        self._tz = tz

    def live(self, on_event: Callable[[datetime64], Any]) -> None:
        timeout = timedelta64(int(self._seconds * 1000), 'ms')
        timestamp = get_now(tz=self._tz)

        while True:
            timestamp += timeout
            sleep_seconds = timedelta_to_seconds(
                timestamp - get_now(tz=self._tz)
            )

            if sleep_seconds > 0:
                time.sleep(sleep_seconds)   # type: ignore[arg-type]

            for _ in range(self._count):
                on_event(timestamp)

            if not self._repeat:
                break


PLUGIN_CLASS = TimerInputPlugin
CONFIG_CLASS = TimerInputConfig
