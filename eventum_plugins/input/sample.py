from datetime import datetime
from typing import Any, Callable

from numpy import datetime64
from pydantic import Field
from pytz.tzinfo import DstTzInfo

from eventum_plugins.input.base import (InputPluginBaseConfig,
                                        SampleInputPluginMixin)


class SampleInputConfig(InputPluginBaseConfig):
    count: int = Field(..., gt=0)


class SampleInputPlugin(SampleInputPluginMixin):
    """Input plugin for generating specified count of events. Use it
    when you only need to produce event facts and timestamps aren't
    important. For all events timestamps are the same and have a value
    of time when sample generating process was started.
    """

    def __init__(self, config: SampleInputConfig, tz: DstTzInfo) -> None:
        self._count = config.count
        self._tz = tz

    def sample(self, on_event: Callable[[datetime64], Any]) -> None:
        timestamp = datetime64(
            datetime.now(tz=self._tz).replace(tzinfo=None)
        )

        for _ in range(self._count):
            on_event(timestamp)


PLUGIN_CLASS = SampleInputPlugin
CONFIG_CLASS = SampleInputConfig
