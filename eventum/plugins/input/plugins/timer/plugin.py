from datetime import datetime, timedelta
from itertools import repeat
from typing import Iterator

from numpy import datetime64
from numpy.typing import NDArray

from eventum.plugins.exceptions import PluginRuntimeError
from eventum.plugins.input.base.plugin import InputPlugin, InputPluginParams
from eventum.plugins.input.normalizers import normalize_versatile_datetime
from eventum.plugins.input.plugins.timer.config import TimerInputPluginConfig
from eventum.plugins.input.utils.time_utils import skip_periods, to_naive


class TimerInputPlugin(InputPlugin[TimerInputPluginConfig]):
    """Input plugin for generating timestamps after specified number of
    seconds.
    """

    def __init__(
        self,
        config: TimerInputPluginConfig,
        params: InputPluginParams
    ) -> None:
        super().__init__(config, params)

    def generate(
        self,
        size: int,
        skip_past: bool = True
    ) -> Iterator[NDArray[datetime64]]:
        start = normalize_versatile_datetime(
            value=self._config.start,
            timezone=self._timezone,
            none_point='now'
        )

        timeout = timedelta(seconds=self._config.seconds)

        if self._config.repeat is None:
            end = normalize_versatile_datetime(
                value=None,
                timezone=self._timezone,
                none_point='max'
            )
        else:
            try:
                end = start + (timeout * self._config.repeat)
            except OverflowError:
                raise PluginRuntimeError(
                    'End time of generation is overflowed',
                    context=dict(self.instance_info)
                )

        self._logger.info(
            'Generating in range',
            start_timestamp=start.isoformat(),
            end_timestamp=end.isoformat()
        )

        if skip_past:
            timestamp = skip_periods(
                start=start,
                moment=datetime.now().astimezone(self._timezone),
                duration=timeout,
                ret_timestamp='first_future'
            )
            skipped_periods = (timestamp - start) // timeout
        else:
            timestamp = start
            skipped_periods = 0

        if (
            self._config.repeat is not None
            and self._config.repeat - skipped_periods <= 0
        ):
            self._logger.info(
                'All timestamps are in past, nothing to generate'
            )
            return

        for _ in (
            repeat(None)
            if self._config.repeat is None
            else range(max(self._config.repeat - skipped_periods, 0))
        ):
            try:
                timestamp += timeout
            except OverflowError:
                break

            self._buffer.m_push(
                timestamp=datetime64(
                    to_naive(timestamp, self._timezone).isoformat(), 'us'
                ),
                multiply=self._config.count
            )
            if self._buffer.size >= size:
                yield from self._buffer.read(size, partial=False)

        yield from self._buffer.read(size, partial=True)
