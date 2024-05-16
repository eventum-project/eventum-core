import time
from datetime import datetime
from typing import Any, Callable, Self

from croniter import croniter
from numpy import datetime64

from eventum.core import settings
from eventum.core.models.input_config import CronInputConfig
from eventum.core.plugins.input.base import (InputPluginConfigurationError,
                                             LiveInputPlugin)


class CronInputPlugin(LiveInputPlugin):
    """Input plugin for generating events at times defined by cron
    expression.
    """

    def __init__(self, expression: str, count: int) -> None:
        """Parameters:
        `expression` - cron expression;
        `count` - number of events to generate for each period.
        """
        if not croniter.is_valid(expression):
            raise InputPluginConfigurationError(
                'Failed to parse cron expression'
            )

        self._cron = croniter(
            expr_format=expression,
            start_time=datetime.now(tz=settings.TIMEZONE),
            ret_type=datetime
        )
        self._count = count

    def live(self, on_event: Callable[[datetime64], Any]) -> None:
        while True:
            timestamp: datetime = self._cron.get_next()
            now = datetime.now(tz=settings.TIMEZONE)
            wait_seconds = (timestamp - now).total_seconds()

            if wait_seconds > 0:
                time.sleep(wait_seconds)

            for _ in range(self._count):
                on_event(datetime64(timestamp.replace(tzinfo=None)))

    @classmethod
    def create_from_config(
        cls,
        config: CronInputConfig     # type: ignore[override]
    ) -> Self:
        return cls(
            expression=config.expression,
            count=config.count
        )


def load_plugin():
    """Return class of plugin from current module."""
    return CronInputPlugin
