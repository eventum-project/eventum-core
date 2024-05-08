import time
from typing import Any, Callable

from numpy import datetime64

from eventum.core.models.application_config import TimerInputConfig
from eventum.core.plugins.input.base import (InputPluginConfigurationError,
                                             LiveInputPlugin)
from eventum.utils.numpy_time import get_now


class TimerInputPlugin(LiveInputPlugin):
    """Input plugin for generating events after specified number of
    seconds.
    """

    def __init__(self, seconds: int, count: int, repeat: bool) -> None:
        """Parameters:
        `seconds` - number of seconds to wait before generating events;
        `count` - number of events to generate;
        `repeat` - whether to loop the timer after generating events.
        """
        if seconds <= 0:
            raise InputPluginConfigurationError(
                'Parameter `seconds` must be greater than 0'
            )
        if count <= 0:
            raise InputPluginConfigurationError(
                'Parameter `count` must be greater than 0'
            )

        self._seconds = seconds
        self._count = count
        self._repeat = repeat

    def live(self, on_event: Callable[[datetime64], Any]) -> None:
        while True:
            if not self._repeat:
                break

            time.sleep(self._seconds)

            timestamp = get_now()
            for _ in range(self._count):
                on_event(timestamp)

    @classmethod
    def create_from_config(
        cls,
        config: TimerInputConfig
    ) -> 'TimerInputPlugin':
        return TimerInputPlugin(
            seconds=config.seconds,
            count=config.count,
            repeat=config.repeat
        )


def load_plugin():
    """Return class of plugin from current module."""
    return TimerInputPlugin
