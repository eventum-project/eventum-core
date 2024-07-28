from datetime import datetime
from typing import Any, Callable

from numpy import datetime64, linspace, timedelta64
from numpy.typing import NDArray
from pydantic import Field, model_validator
from pytz.tzinfo import BaseTzInfo

from eventum_plugins.input._base import (InputPlugin, InputPluginConfig,
                                         SampleInputPluginMixin)


class LinspaceInputPluginConfig(InputPluginConfig, frozen=True):
    """
    `start` - start time of interval
    `end` - end time of interval
    `count` - number of events within interval
    `endpoint` - whether to include end point of interval
    """
    start: datetime
    end: datetime
    count: int = Field(..., ge=1)
    endpoint: bool = True

    @model_validator(mode='after')
    def validate_interval(self):
        if self.start < self.end:
            return self
        raise ValueError('Start time must be earlier than end time')


class LinspaceInputPlugin(
    SampleInputPluginMixin,
    InputPlugin,
    config_cls=LinspaceInputPluginConfig
):
    """Input plugin for generating specified count of events linearly
    spaced in time.
    """

    def __init__(
        self,
        config: LinspaceInputPluginConfig,
        tz: BaseTzInfo
    ) -> None:
        self._start = config.start
        self._end = config.end
        self._count = config.count
        self._endpoint = config.endpoint
        self._tz = tz

    def sample(self, on_events: Callable[[NDArray[datetime64]], Any]) -> None:
        start = datetime64(
            value=self._start.astimezone(self._tz).replace(tzinfo=None),
            format='us'
        )
        end = datetime64(
            value=self._end.astimezone(self._tz).replace(tzinfo=None),
            format='us'
        )

        timedelta = timedelta64(value=(end - start), format='us')
        space = linspace(
            start=0,
            stop=1,
            num=self._count,
            endpoint=self._endpoint,
        )

        timestamps = start + (timedelta * space)
        on_events(timestamps)
