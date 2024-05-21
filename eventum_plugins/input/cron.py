import time
from datetime import datetime
from typing import Any, Callable

from croniter import croniter
from numpy import datetime64
from pydantic import Field, field_validator
from pytz.tzinfo import DstTzInfo

from eventum_plugins.input.base import (InputPluginBaseConfig,
                                        LiveInputPluginMixin)


class CronInputConfig(InputPluginBaseConfig):
    expression: str
    count: int = Field(..., gt=0)

    @field_validator('expression')
    def validate_expression(cls, v: Any):
        if croniter.is_valid(v):
            return v
        raise ValueError('Invalid cron expression')


class CronInputPlugin(LiveInputPluginMixin):
    """Input plugin for generating events at moments defined by cron
    expression.
    """

    def __init__(self, config: CronInputConfig, tz: DstTzInfo) -> None:
        self._expression = config.expression
        self._count = config.count
        self._tz = tz

    def live(self, on_event: Callable[[datetime64], Any]) -> None:
        self._cron = croniter(
            expr_format=self._expression,
            start_time=datetime.now(tz=self._tz),
            ret_type=datetime
        )

        while True:
            timestamp: datetime = self._cron.get_next()
            now = datetime.now(tz=self._tz)
            wait_seconds = (timestamp - now).total_seconds()

            if wait_seconds > 0:
                time.sleep(wait_seconds)

            for _ in range(self._count):
                on_event(datetime64(timestamp.replace(tzinfo=None)))


EXPORT_PLUGIN = CronInputPlugin
