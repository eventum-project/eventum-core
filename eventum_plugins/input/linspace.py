from datetime import datetime
from typing import Any, Callable

from numpy import datetime64, linspace, timedelta64
from pydantic import Field, model_validator
from pytz.tzinfo import BaseTzInfo

from eventum_plugins.input.base import InputPluginBaseConfig, SampleInputPlugin


class LinspaceInputConfig(InputPluginBaseConfig, frozen=True):
    start: datetime
    end: datetime
    count: int = Field(..., ge=1)
    endpoint: bool = True

    @model_validator(mode='after')
    def validate_interval(self):
        if self.start < self.end:
            return self
        raise ValueError('Start time must be earlier than end time')


class LinspaceInputPlugin(SampleInputPlugin):
    """Input plugin for generating specified count of events linearly
    spaced in time.
    """

    def __init__(self, config: LinspaceInputConfig, tz: BaseTzInfo) -> None:
        self._start = config.start
        self._end = config.end
        self._count = config.count
        self._endpoint = config.endpoint
        self._tz = tz

    def sample(self, on_event: Callable[[datetime64], Any]) -> None:
        start = datetime64(
            self._start.astimezone(self._tz).replace(tzinfo=None)
        )
        end = datetime64(
            self._end.astimezone(self._tz).replace(tzinfo=None)
        )

        timedelta = timedelta64(end - start)
        space = linspace(
            start=0,
            stop=1,
            num=self._count,
            endpoint=self._endpoint,
        )
        timestamps = [start + delta for delta in space * timedelta]

        for ts in timestamps:
            on_event(ts)


PLUGIN_CLASS = LinspaceInputPlugin
CONFIG_CLASS = LinspaceInputConfig
