import time
from datetime import UTC
from typing import Any, Callable

from crontab import CronTab
from eventum.core import settings
from eventum.core.models.application_config import CronInputConfig
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
                ).replace(
                    tzinfo=UTC
                ).astimezone(settings.TIMEZONE).replace(tzinfo=None)
            )
            wait_seconds = self._entry.next(default_utc=False)  # type: ignore
            if wait_seconds > 0:
                time.sleep(wait_seconds)

            for _ in range(self._count):
                on_event(timestamp)

    @classmethod
    def create_from_config(cls, config: CronInputConfig) -> 'CronInputPlugin':
        return CronInputPlugin(
            expression=config.expression,
            count=config.count
        )


def load_plugin():
    """Return class of plugin from current module."""
    return CronInputPlugin
