import time
from datetime import datetime
from typing import Any, Callable, Iterator, Unpack

import croniter
from numpy import array, datetime64, full, repeat
from numpy.typing import NDArray

from eventum_plugins.exceptions import PluginConfigurationError
from eventum_plugins.input.base.plugin import InputPlugin, InputPluginKwargs
from eventum_plugins.input.fields import TimeKeyword
from eventum_plugins.input.plugins.cron.config import CronInputPluginConfig
from eventum_plugins.input.tools import normalize_versatile_daterange


class CronInputPlugin(InputPlugin, config_cls=CronInputPluginConfig):
    """Input plugin for generating timestamps at moments defined by
    cron expression.
    """

    def __init__(
        self,
        *,
        config: CronInputPluginConfig,
        **kwargs: Unpack[InputPluginKwargs]
    ) -> None:
        super().__init__(config=config, **kwargs)

        self._config: CronInputPluginConfig

        if (
            not self._live_mode and (
                self._config.end is None
                or self._config.end == TimeKeyword.NEVER.value
            )
        ):
            raise PluginConfigurationError(
                'End time must be finite for sample mode'
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
            start=None,             # skip all past timestamps
            end=self._config.end,
            timezone=self._timezone,
            none_start='now'
        )
        range: Iterator[datetime] = croniter.croniter_range(
            start=start,
            stop=end,
            expr_format=self._config.expression,
            ret_type=datetime

        )

        for timestamp in range:
            now = datetime.now().astimezone(self._timezone)
            wait_seconds = (timestamp - now).total_seconds()

            if wait_seconds > 0:
                time.sleep(wait_seconds)

            on_events(
                full(
                    shape=self._config.count,
                    fill_value=datetime64(timestamp.replace(tzinfo=None)),
                    dtype='datetime64[us]'
                )
            )
