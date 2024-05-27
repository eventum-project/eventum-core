from typing import Any, Callable

from numpy import datetime64
from pydantic import Field
from pytz.tzinfo import BaseTzInfo

from eventum_plugins.input.base import InputPluginBaseConfig
from eventum_plugins.input.base import \
    SampleInputPlugin as BaseSampleInputPlugin
from eventum_plugins.utils.numpy_time import get_now


class SampleInputConfig(InputPluginBaseConfig, frozen=True):
    count: int = Field(..., gt=0)


class SampleInputPlugin(BaseSampleInputPlugin):
    """Input plugin for generating specified count of events. Use it
    when you only need to produce event facts and timestamps aren't
    important. For all events timestamps are the same and have a value
    of time when sample generating process was started.
    """

    def __init__(self, config: SampleInputConfig, tz: BaseTzInfo) -> None:
        self._count = config.count
        self._tz = tz

    def sample(self, on_event: Callable[[datetime64], Any]) -> None:
        timestamp = get_now(tz=self._tz)

        for _ in range(self._count):
            on_event(timestamp)


PLUGIN_CLASS = SampleInputPlugin
CONFIG_CLASS = SampleInputConfig
