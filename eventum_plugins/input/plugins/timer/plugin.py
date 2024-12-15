import time
from datetime import datetime, timedelta
from itertools import repeat as i_repeat

from numpy import arange, datetime64, full, repeat, timedelta64
from numpy.typing import NDArray

from eventum_plugins.exceptions import PluginConfigurationError
from eventum_plugins.input.base.plugin import InputPlugin, InputPluginParams
from eventum_plugins.input.normalizers import normalize_versatile_datetime
from eventum_plugins.input.plugins.timer.config import TimerInputPluginConfig
from eventum_plugins.input.utils.time_utils import skip_periods, to_naive


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

        if not self._live_mode and self._config.repeat is None:
            raise PluginConfigurationError(
                'Repeats count must be finite for sample mode',
                context=dict(self.instance_info)
            )

    def _generate_sample(self) -> None:
        start = normalize_versatile_datetime(
            value=self._config.start,
            timezone=self._timezone,
            none_point='now'
        )

        timeout = timedelta(seconds=self._config.seconds)
        end_after = timeout * self._config.repeat  # type: ignore[operator]
        end = start + end_after

        self._logger.info(
            'Generating in range',
            start_timestamp=start.isoformat(),
            end_timestamp=end.isoformat()
        )

        delta = timedelta64(timeout, 'us')
        delta_end = timedelta64(end_after + timeout, 'us')

        deltas: NDArray[timedelta64] = arange(
            start=delta,
            stop=delta_end,
            step=delta
        )

        timestamps = deltas + datetime64(
            to_naive(start, self._timezone), 'us'
        )
        timestamps = repeat(timestamps, repeats=self._config.count)
        self._enqueue(timestamps)

    def _generate_live(self) -> None:
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
            end = start + (timeout * self._config.repeat)

        self._logger.info(
            'Generating in range',
            start_timestamp=start.isoformat(),
            end_timestamp=end.isoformat()
        )

        timestamp = skip_periods(
            start=start,
            moment=datetime.now().astimezone(self._timezone),
            duration=timeout,
            ret_timestamp='first_future'
        )
        skipped_periods = (timestamp - start) // timeout

        if skipped_periods > 1:
            self._logger.info(
                'Past timestamps are skipped',
                count=skipped_periods,
                start_timestamp=timestamp.isoformat()
            )

        if (
            self._config.repeat is not None
            and self._config.repeat - skipped_periods <= 0
        ):
            self._logger.info(
                'All timestamps are in past, nothing to generate'
            )

        for _ in (
            i_repeat(None)
            if self._config.repeat is None
            else range(max(self._config.repeat - skipped_periods, 0))
        ):
            timestamp += timeout
            sleep_seconds = (
                datetime.now().astimezone() - timestamp
            ).total_seconds()

            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

            self._enqueue(
                full(
                    shape=self._config.count,
                    fill_value=datetime64(
                        to_naive(timestamp, self._timezone), 'us'
                    ),
                    dtype='datetime64[us]'
                )
            )
