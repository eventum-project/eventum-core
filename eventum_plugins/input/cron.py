import time
from datetime import datetime
from typing import Any, Callable

from croniter import croniter
from numpy import datetime64, full
from numpy.typing import NDArray
from pydantic import Field, field_validator
from pytz.tzinfo import BaseTzInfo

from eventum_plugins.input._base import (InputPlugin, InputPluginConfig,
                                         LiveInputPluginMixin)


class CronInputPluginConfig(InputPluginConfig, frozen=True):
    """
    `expression` - cron expression (e.g. */5 * * * *)
    `count` - number of events to generate each interval
    """
    expression: str
    count: int = Field(..., gt=0)

    @field_validator('expression')
    def validate_expression(cls, v: str):
        if croniter.is_valid(v):
            return v
        raise ValueError('Invalid cron expression')


class CronInputPlugin(
    LiveInputPluginMixin,
    InputPlugin,
    config_cls=CronInputPluginConfig
):
    """Input plugin for generating events at moments defined by cron
    expression.
    """

    def __init__(self, config: CronInputPluginConfig, tz: BaseTzInfo) -> None:
        self._expression = config.expression
        self._count = config.count
        self._tz = tz

    def live(self, on_events: Callable[[NDArray[datetime64]], Any]) -> None:
        cron = croniter(
            expr_format=self._expression,
            start_time=datetime.now(tz=self._tz),
            ret_type=datetime
        )

        while True:
            timestamp: datetime = cron.get_next()
            now = datetime.now(tz=self._tz)
            wait_seconds = (timestamp - now).total_seconds()

            if wait_seconds > 0:
                time.sleep(wait_seconds)

            ts = datetime64(timestamp.replace(tzinfo=None))
            on_events(full(self._count, ts, dtype='datetime64[us]'))
