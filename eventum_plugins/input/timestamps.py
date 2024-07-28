import logging
import os
import time
from datetime import datetime
from typing import Any, Callable

from numpy import array, datetime64, sort
from numpy.typing import NDArray
from pydantic import Field, field_validator
from pytz.tzinfo import BaseTzInfo

from eventum_plugins.exceptions import PluginConfigurationError
from eventum_plugins.input._base import (InputPlugin, InputPluginConfig,
                                         LiveInputPluginMixin,
                                         SampleInputPluginMixin)
from eventum_plugins.utils.datetime import convert_to_naive
from eventum_plugins.utils.numpy_time import get_now, timedelta_to_seconds
from eventum_plugins.utils.timeseries import get_future_slice

logger = logging.getLogger(__name__)


class TimestampsInputPluginConfig(InputPluginConfig, frozen=True):
    """
    `source` - list of timestamps or path to file with new line
    separated timestamps
    """
    source: tuple[datetime, ...] | str = Field(..., min_length=1)

    @field_validator('source')
    def validate_source(cls, v: Any):
        if not isinstance(v, str):
            return v

        if not os.path.isabs(v):
            raise ValueError

        return v


class TimestampsInputPlugin(
    LiveInputPluginMixin,
    SampleInputPluginMixin,
    InputPlugin,
    config_cls=TimestampsInputPluginConfig
):
    """Input plugin for generating events in specified timestamps."""

    def __init__(
        self,
        config: TimestampsInputPluginConfig,
        tz: BaseTzInfo
    ) -> None:
        if isinstance(config.source, str):
            try:
                self._timestamps: list[datetime] = [
                    convert_to_naive(datetime.fromisoformat(ts), tz)
                    for ts in self._read_timestamps_from_file(config.source)
                ]
            except ValueError as e:
                raise PluginConfigurationError(
                    f'Failed to parse timestamps: {e}'
                ) from None
        else:
            self._timestamps = [
                convert_to_naive(ts, tz) for ts in config.source
            ]

        self._tz = tz

    def _read_timestamps_from_file(self, filename: str) -> list[str]:
        """Read timestamp from specified file."""
        try:
            with open(filename) as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        except OSError as e:
            raise PluginConfigurationError(
                f'Failed to load timestamps file: {e}'
            ) from None

    def sample(self, on_events: Callable[[NDArray[datetime64]], Any]) -> None:
        timestamps = sort(array(self._timestamps, dtype='datetime64[us]'))
        on_events(timestamps)

    def live(self, on_events: Callable[[NDArray[datetime64]], Any]) -> None:
        timestamps = sort(array(self._timestamps, dtype='datetime64[us]'))

        now = get_now(tz=self._tz)
        future_timestamps = get_future_slice(
            timestamps=timestamps,
            after=now
        )
        if future_timestamps.size == 0:
            logger.warning('All timestamps are in past, nothing to generate')
            return

        for timestamp in future_timestamps:
            now = get_now(tz=self._tz)
            wait_seconds = timedelta_to_seconds(timestamp - now)

            if wait_seconds > 0:
                time.sleep(wait_seconds)    # type: ignore[arg-type]

            on_events(array([timestamp], dtype='datetime64[us]'))
