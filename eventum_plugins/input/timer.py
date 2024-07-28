import time
from itertools import repeat
from typing import Any, Callable

from numpy import datetime64, full, timedelta64
from numpy.typing import NDArray
from pydantic import Field
from pytz.tzinfo import BaseTzInfo

from eventum_plugins.input._base import (InputPlugin, InputPluginConfig,
                                         LiveInputPluginMixin)
from eventum_plugins.utils.numpy_time import get_now, timedelta_to_seconds


class TimerInputPluginConfig(InputPluginConfig, frozen=True):
    """
    `seconds` - number of seconds to wait before generating event
    `count` - number of events to generate after time has come
    `repeat` - number of cycles to repeat, infinite if value is not set
    """
    seconds: float = Field(..., ge=0.1)
    count: int = Field(..., ge=1)
    repeat: int | None = Field(None, ge=1)


class TimerInputPlugin(
    LiveInputPluginMixin,
    InputPlugin,
    config_cls=TimerInputPluginConfig
):
    """Input plugin for generating events after specified number of
    seconds.
    """

    def __init__(self, config: TimerInputPluginConfig, tz: BaseTzInfo) -> None:
        self._seconds = config.seconds
        self._count = config.count
        self._repeat = config.repeat
        self._tz = tz

    def live(self, on_events: Callable[[NDArray[datetime64]], Any]) -> None:
        timeout = timedelta64(int(self._seconds * 1000), 'ms')
        timestamp = get_now(tz=self._tz)

        for _ in (
            repeat(None)
            if self._repeat is None
            else range(self._repeat)
        ):
            timestamp += timeout
            sleep_seconds = timedelta_to_seconds(
                timestamp - get_now(tz=self._tz)
            )

            if sleep_seconds > 0:
                time.sleep(sleep_seconds)   # type: ignore[arg-type]

            on_events(
                full(
                    shape=self._count,
                    fill_value=timestamp,
                    dtype='datetime64[us]'
                )
            )
