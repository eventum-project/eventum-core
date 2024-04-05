from typing import Any, Callable

from eventum.core.models.application_config import SampleInputConfig
from eventum.core.plugins.input.base import \
    SampleInputPlugin as BaseSampleInputPlugin
from eventum.utils.numpy_time import get_now
from numpy import datetime64


class SampleInputPlugin(BaseSampleInputPlugin):
    """Input plugin for generating specified count of events. Use it
    when you only need to produce event facts and timestamps aren't
    important. For all events timestamps are the same and have a
    symbolic value of time when sample generating process was started.
    """

    def __init__(self, count: int) -> None:
        self._count = count

    def sample(self, on_event: Callable[[datetime64], Any]) -> None:
        timestamp = get_now()

        for _ in range(self._count):
            on_event(timestamp)

    @classmethod
    def create_from_config(
        cls,
        config: SampleInputConfig
    ) -> 'SampleInputPlugin':
        return SampleInputPlugin(count=config.count)


def load_plugin():
    """Return class of plugin from current module."""
    return SampleInputPlugin
