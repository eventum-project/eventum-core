import time
from datetime import datetime
from typing import Any, Callable

import croniter
from numpy import array, datetime64, full, repeat
from numpy.typing import NDArray

from eventum_plugins.exceptions import PluginConfigurationError
from eventum_plugins.input.base.plugin import InputPlugin
from eventum_plugins.input.enums import TimeMode
from eventum_plugins.input.fields import TimeKeyword
from eventum_plugins.input.plugins.cron.config import CronInputPluginConfig
from eventum_plugins.input.tools import normalize_versatile_daterange


class CronInputPlugin(InputPlugin, config_cls=CronInputPluginConfig):
    """Input plugin for generating timestamps at moments defined by
    cron expression.
    """

    def __init__(self, *, config: CronInputPluginConfig, **kwargs) -> None:
        super().__init__(config=config, **kwargs)

        self._config: CronInputPluginConfig

        mode = kwargs['mode']
        if (
            mode == TimeMode.SAMPLE
            and (
                self._config.end is None
                or self._config.end == TimeKeyword.NEVER.value
            )
        ):
            raise PluginConfigurationError(
                f'End time must be finite for "{mode}" mode'
            )

    def _generate_sample(
        self,
        on_events: Callable[[NDArray[datetime64]], Any]
    ) -> None:
        start, end = normalize_versatile_daterange(
            start=self._config.start,
            end=self._config.end,
            timezone=self._timezone,
            none_start='now'
        )
        range = croniter.croniter_range(
            start=start.replace(tzinfo=None),
            stop=end.replace(tzinfo=None),
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
        start, end = normalize_versatile_daterange(
            start=self._config.start,
            end=self._config.end,
            timezone=self._timezone,
            none_start='now'
        )
        range = croniter.croniter_range(
            start=start.replace(tzinfo=None),
            stop=end.replace(tzinfo=None),
            expr_format=self._config.expression,
            ret_type=datetime

        )

        for timestamp in range:
            timestamp: datetime

            now = datetime.now().astimezone(self._timezone)
            wait_seconds = (timestamp - now).total_seconds()

            # skip past timestamps
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
