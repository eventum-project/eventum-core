from typing import Any, Callable

from numpy import datetime64, full
from numpy.typing import NDArray
from pydantic import Field
from pytz.tzinfo import BaseTzInfo

from eventum_plugins.input._base import (InputPlugin, InputPluginConfig,
                                         SampleInputPluginMixin)
from eventum_plugins.utils.numpy_time import get_now


class SampleInputPluginConfig(InputPluginConfig, frozen=True):
    """
    `count` - number of events to generate
    """
    count: int = Field(..., gt=0)


class SampleInputPlugin(
    SampleInputPluginMixin,
    InputPlugin,
    config_cls=SampleInputPluginConfig
):
    """Input plugin for generating specified count of events. Use it
    when you only need to produce event facts and timestamps aren't
    important. For all events timestamps are the same and have a value
    of time when sample generating process was started.
    """

    def __init__(
        self,
        config: SampleInputPluginConfig,
        tz: BaseTzInfo
    ) -> None:
        self._count = config.count
        self._tz = tz

    def sample(self, on_events: Callable[[NDArray[datetime64]], Any]) -> None:
        timestamp = get_now(tz=self._tz)
        on_events(full(self._count, timestamp, dtype='datetime64[us]'))
