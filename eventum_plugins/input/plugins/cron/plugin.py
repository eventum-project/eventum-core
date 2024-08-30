import time
from datetime import datetime
from typing import Any, Callable, Literal

import croniter
from numpy import array, datetime64, full, repeat
from numpy.typing import NDArray
from pytz.tzinfo import BaseTzInfo

from eventum_plugins.input.base.plugin import InputPlugin
from eventum_plugins.input.enums import TimeMode
from eventum_plugins.input.plugins.cron.config import CronInputPluginConfig
from eventum_plugins.input.tools import normalize_daterange


class CronInputPlugin(InputPlugin, config_cls=CronInputPluginConfig):
    """Input plugin for generating timestamps at moments defined by
    cron expression.
    """

    def __init__(
        self,
        id: int,
        config: CronInputPluginConfig,
        mode: TimeMode,
        timezone: BaseTzInfo,
        batch_size: int | None = 100_000,
        batch_delay: float | None = 0.1,
        queue_max_size: int = 100_000_000,
        on_queue_overflow: Literal['block', 'skip'] = 'block'
    ) -> None:
        super().__init__(
            id, config, mode, timezone, batch_size, batch_delay,
            queue_max_size, on_queue_overflow
        )
        self._config: CronInputPluginConfig

        self._start, self._end = normalize_daterange(
            start=self._config.start,
            end=self._config.end,
            timezone=self._timezone,
            none_start='now'
        )

    def _generate_sample(
        self,
        on_events: Callable[[NDArray[datetime64]], Any]
    ) -> None:
        range = croniter.croniter_range(
            start=self._start.replace(tzinfo=None),
            stop=self._end.replace(tzinfo=None),
            expr_format=self._config.expression,
            ret_type=datetime

        )
        timestamps = repeat(
            a=array(list(range), dtype='datetime64[us]'),
            repeats=self._config.count
        )
        on_events(timestamps)

    def _generate_live(
        self,
        on_events: Callable[[NDArray[datetime64]], Any]
    ) -> None:
        cron = croniter.croniter(
            expr_format=self._config.expression,
            ret_type=datetime,
        )

        start_time = self._start

        while (timestamp := cron.get_next(start_time=start_time)) < self._end:
            timestamp: datetime

            now = datetime.now(tz=self._timezone)
            wait_seconds = (timestamp - now).total_seconds()

            if wait_seconds > 0:
                time.sleep(wait_seconds)
            else:
                continue

            on_events(
                full(
                    shape=self._config.count,
                    fill_value=datetime64(timestamp.replace(tzinfo=None)),
                    dtype='datetime64[us]'
                )
            )

            start_time = timestamp
