import time
from typing import Any, Callable, NoReturn

from crontab import CronTab

from eventum.core.plugins.input.base import LiveInputPlugin


class CronInputPlugin(LiveInputPlugin):
    """Input plugin for generating events at times defined
    by cron expression.
    """

    def __init__(self, expression: str, count: int) -> None:
        """Parameters:
        `expression` - cron expression;
        `count` - number of events to generate for each interval.
        """
        self._expression = expression
        self._count = count

    def live(self, on_event: Callable[[str], Any]) -> NoReturn:
        entry = CronTab(self._expression)

        while True:
            timestamp = entry.next(default_utc=False, return_datetime=True)
            time.sleep(entry.next(default_utc=False))

            for _ in range(self._count):
                on_event(timestamp.isoformat())
