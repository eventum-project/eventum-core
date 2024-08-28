import time
from datetime import datetime
from typing import Any, Callable, Literal, assert_never

from croniter import croniter
from numpy import datetime64, full
from numpy.typing import NDArray
from pytz.tzinfo import BaseTzInfo

from eventum_plugins.exceptions import PluginConfigurationError
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

        try:
            self._start, self._end = normalize_daterange(
                start=self._config.start,
                end=self._config.end,
                timezone=self._timezone,
                none_start='now'
            )
        except ValueError as e:
            raise PluginConfigurationError(
                f'Date range normalization failure: {e}'
            )

    def _generate(
        self,
        mode: TimeMode,
        on_events: Callable[[NDArray[datetime64]], Any]
    ) -> None:
        cron = croniter(
            expr_format=self._config.expression,
            ret_type=datetime
        )

        start_time = self._start

        while (timestamp := cron.get_next(start_time=start_time)) < self._end:
            timestamp: datetime

            match mode:
                case TimeMode.LIVE:
                    now = datetime.now(tz=self._timezone)
                    wait_seconds = (timestamp - now).total_seconds()

                    if wait_seconds > 0:
                        time.sleep(wait_seconds)
                    else:
                        continue
                case TimeMode.SAMPLE:
                    pass
                case v:
                    assert_never(v)

            on_events(
                full(
                    shape=self._config.count,
                    fill_value=datetime64(timestamp.replace(tzinfo=None)),
                    dtype='datetime64[us]'
                )
            )

            start_time = timestamp
