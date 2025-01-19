from datetime import datetime
from typing import Iterator

import croniter
from numpy import datetime64
from numpy.typing import NDArray

from eventum.plugins.input.base.plugin import InputPlugin, InputPluginParams
from eventum.plugins.input.normalizers import normalize_versatile_daterange
from eventum.plugins.input.plugins.cron.config import CronInputPluginConfig


class CronInputPlugin(InputPlugin[CronInputPluginConfig, InputPluginParams]):
    """Input plugin for generating timestamps at moments defined by
    cron expression.
    """

    def __init__(
        self,
        config: CronInputPluginConfig,
        params: InputPluginParams
    ) -> None:
        super().__init__(config, params)

    def generate(
        self,
        size: int,
        skip_past: bool = True
    ) -> Iterator[NDArray[datetime64]]:
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

        if skip_past:
            if end < now:
                self._logger.info(
                    'All timestamps are in past, nothing to generate'
                )
                return
            if start < now:
                start = now

        range: Iterator[datetime] = croniter.croniter_range(
            start=start,
            stop=end,
            expr_format=self._config.expression,
            ret_type=datetime
        )

        for timestamp in range:
            self._buffer.m_push(
                timestamp=datetime64(timestamp.replace(tzinfo=None)),
                multiply=self._config.count
            )

            if self._buffer.size >= size:
                yield from self._buffer.read(size, partial=False)

        if self._buffer.size > 0:
            yield from self._buffer.read(size, partial=True)
