import os
import time
from datetime import datetime
from typing import Any, Callable

from numpy import array, datetime64
from numpy.typing import NDArray
from pydantic import Field, field_validator
from pytz.tzinfo import BaseTzInfo

from eventum_plugins.exceptions import PluginConfigurationError
from eventum_plugins.input.base import (InputPluginBaseConfig, LiveInputPlugin,
                                        SampleInputPlugin)
from eventum_plugins.utils.datetime import convert_to_naive
from eventum_plugins.utils.numpy_time import get_now, timedelta_to_seconds
from eventum_plugins.utils.timeseries import get_future_slice


class TimestampsInputConfig(InputPluginBaseConfig, frozen=True):
    source: tuple[datetime, ...] | str = Field(..., min_length=1)

    @field_validator('source')
    def validate_source(cls, v: Any):
        if not isinstance(v, str):
            return v

        if not os.path.isabs(v):
            raise ValueError

        return v


class TimestampsInputPlugin(LiveInputPlugin, SampleInputPlugin):
    """Input plugin for generating events in specified timestamps."""

    def __init__(self, config: TimestampsInputConfig, tz: BaseTzInfo) -> None:
        # if `source` is of type string we consider it as filename
        # with list of timestamps
        if isinstance(config.source, str):
            try:
                timestamps: list[datetime] = [
                    convert_to_naive(datetime.fromisoformat(ts), tz)
                    for ts in self._read_timestamps_from_file(config.source)
                ]
            except ValueError as e:
                raise PluginConfigurationError(
                    f'Failed to parse timestamps: {e}'
                ) from None

            self._timestamps: NDArray[datetime64] = array(
                timestamps,
                dtype='datetime64'
            )
        else:
            self._timestamps: NDArray[datetime64] = array(
                [convert_to_naive(ts, tz) for ts in config.source],
                dtype='datetime64'
            )
        self._tz = tz

    def _read_timestamps_from_file(self, filename: str) -> list[str]:
        """Read timestamp from specified file."""
        try:
            with open(filename) as f:
                return f.read().strip().split(os.linesep)
        except OSError as e:
            raise PluginConfigurationError(
                f'Failed to load timestamps file: {e}'
            ) from None

    def sample(self, on_event: Callable[[datetime64], Any]) -> None:
        for timestamp in self._timestamps:
            on_event(timestamp)

    def live(self, on_event: Callable[[datetime64], Any]) -> None:
        now = get_now(tz=self._tz)
        future_timestamps = get_future_slice(
            timestamps=self._timestamps,
            after=now
        )
        for timestamp in future_timestamps:
            wait_seconds = timedelta_to_seconds(timestamp - now)

            if wait_seconds > 0:
                time.sleep(wait_seconds)    # type: ignore[arg-type]
                now = get_now(tz=self._tz)

            on_event(timestamp)


PLUGIN_CLASS = TimestampsInputPlugin
CONFIG_CLASS = TimestampsInputConfig
