import time
from datetime import datetime, timedelta
from itertools import repeat as i_repeat
from typing import Any, Callable, Unpack

from numpy import arange, datetime64, full, repeat, timedelta64
from numpy.typing import NDArray

from eventum_plugins.exceptions import PluginConfigurationError
from eventum_plugins.input.base.plugin import InputPlugin, InputPluginKwargs
from eventum_plugins.input.normalizers import normalize_versatile_datetime
from eventum_plugins.input.plugins.timer.config import TimerInputPluginConfig
from eventum_plugins.input.utils.time_utils import skip_periods, to_naive


class TimerInputPlugin(InputPlugin, config_cls=TimerInputPluginConfig):
    """Input plugin for generating timestamps after specified number of
    seconds.
    """

    def __init__(
        self,
        *,
        config: TimerInputPluginConfig,
        **kwargs: Unpack[InputPluginKwargs]
    ) -> None:
        super().__init__(config=config, **kwargs)

        self._config: TimerInputPluginConfig

        if not self._live_mode and self._config.repeat is None:
            raise PluginConfigurationError(
                'Repeats count must be set for sample mode'
            )

    def _generate_sample(
        self,
        on_events: Callable[[NDArray[datetime64]], Any]
    ) -> None:
        start = normalize_versatile_datetime(
            value=self._config.start,
            timezone=self._timezone,
            none_point='now'
        )

        timeout = timedelta64(timedelta(seconds=self._config.seconds), 'us')
        end = timeout * (self._config.repeat + 1)  # type: ignore[operator]

        deltas: NDArray[timedelta64] = arange(
            start=timeout,
            stop=end,
            step=timeout
        )

        timestamps = deltas + datetime64(
            to_naive(start, self._timezone), 'us'
        )
        timestamps = repeat(timestamps, repeats=self._config.count)
        on_events(timestamps)

    def _generate_live(
        self,
        on_events: Callable[[NDArray[datetime64]], Any]
    ) -> None:
        start = normalize_versatile_datetime(
            value=self._config.start,
            timezone=self._timezone,
            none_point='now'
        )
        timeout = timedelta(seconds=self._config.seconds)

        timestamp = skip_periods(
            start=start,
            moment=datetime.now().astimezone(self._timezone),
            duration=timeout,
            ret_timestamp='first_future'
        )
        skipped_periods = (timestamp - start) // timeout

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

            on_events(
                full(
                    shape=self._config.count,
                    fill_value=datetime64(
                        to_naive(timestamp, self._timezone), 'us'
                    ),
                    dtype='datetime64[us]'
                )
            )
