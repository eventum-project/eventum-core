from datetime import datetime
import time
from typing import Any, Callable, NoReturn

from crontab import CronTab

from eventum.core.plugins.input.base import LiveInputPlugin


class CronInputPlugin(LiveInputPlugin):
    """Input plugin for generating events at times defined by cron
    expression.
    """

    def __init__(self, expression: str, count: int) -> None:
        """Parameters:
        `expression` - cron expression;
        `count` - number of events to generate for each period.
        """
        self._entry = CronTab(expression)
        self._count = count

    def live(self, on_event: Callable[[datetime], Any]) -> NoReturn:
        while True:
            timestamp = self._entry.next(
                default_utc=False,
                return_datetime=True
            )
            time.sleep(self._entry.next(default_utc=False))

            for _ in range(self._count):
                on_event(timestamp)
