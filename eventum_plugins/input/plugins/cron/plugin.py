import time
from datetime import datetime
from typing import Iterator

import croniter
from numpy import array, datetime64, full, repeat

from eventum_plugins.exceptions import PluginConfigurationError
from eventum_plugins.input.base.plugin import InputPlugin, InputPluginParams
from eventum_plugins.input.fields import TimeKeyword
from eventum_plugins.input.normalizers import normalize_versatile_daterange
from eventum_plugins.input.plugins.cron.config import CronInputPluginConfig


class CronInputPlugin(InputPlugin[CronInputPluginConfig]):
    """Input plugin for generating timestamps at moments defined by
    cron expression.
    """

    def __init__(
        self,
        config: CronInputPluginConfig,
        params: InputPluginParams
    ) -> None:
        super().__init__(config, params)

        if (
            not self._live_mode and (
                self._config.end is None
                or self._config.end == TimeKeyword.NEVER.value
            )
        ):
            raise PluginConfigurationError(
                'End time must be finite for sample mode',
                context=dict(self.instance_info)
            )

    def _generate_sample(self) -> None:
        start, end = normalize_versatile_daterange(
            start=self._config.start,
            end=self._config.end,
            timezone=self._timezone,
            none_start='now',
            none_end='max'
        )

        self._logger.info(
            'Generating in range',
            start_timestamp=start.isoformat(),
            end_timestamp=end.isoformat()
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

        self._enqueue(timestamps)

    def _generate_live(self) -> None:
        now = datetime.now().astimezone(self._timezone)
        start, end = normalize_versatile_daterange(
            start=self._config.start,
            end=self._config.end,
            timezone=self._timezone,
            none_start='now',
            none_end='max'
        )

        self._logger.info(
            'Generating in range',
            start_timestamp=start.isoformat(),
            end_timestamp=end.isoformat()
        )

        if end < now:
            self._logger.info(
                'All timestamps are in past, nothing to generate'
            )
            return
        elif start < now:
            start = now
            self._logger.info('Past timestamps are skipped')

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

            self._enqueue(
                full(
                    shape=self._config.count,
                    fill_value=datetime64(timestamp.replace(tzinfo=None)),
                    dtype='datetime64[us]'
                )
            )
