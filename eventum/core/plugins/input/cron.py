import time
from typing import Any, Callable

from crontab import CronTab
from eventum.core.plugins.input.base import (InputPluginConfigurationError,
                                             LiveInputPlugin)
from numpy import datetime64


class CronInputPlugin(LiveInputPlugin):
    """Input plugin for generating events at times defined by cron
    expression.
    """

    def __init__(self, expression: str, count: int) -> None:
        """Parameters:
        `expression` - cron expression;
        `count` - number of events to generate for each period.
        """
        try:
            self._entry = CronTab(expression)
        except ValueError as e:
            raise InputPluginConfigurationError(
                f'Failed to parse cron expression: {e}'
            )
        self._count = count

    def live(self, on_event: Callable[[datetime64], Any]) -> None:
        while True:
            timestamp = datetime64(
                self._entry.next(                               # type: ignore
                    default_utc=True,
                    return_datetime=True
                )
            )
            wait_seconds = self._entry.next(default_utc=False)  # type: ignore
            if wait_seconds > 0:
                time.sleep(wait_seconds)

            for _ in range(self._count):
                on_event(timestamp)
