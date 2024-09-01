import time
from datetime import datetime, timedelta
from itertools import repeat as i_repeat
from typing import Any, Callable

from numpy import arange, datetime64, full, repeat, timedelta64
from numpy.typing import NDArray

from eventum_plugins.exceptions import PluginConfigurationError
from eventum_plugins.input.base.plugin import InputPlugin
from eventum_plugins.input.enums import TimeMode
from eventum_plugins.input.plugins.timer.config import TimerInputPluginConfig
from eventum_plugins.input.tools import normalize_versatile_datetime
from eventum_plugins.input.utils.time_utils import to_naive


class TimerInputPlugin(InputPlugin, config_cls=TimerInputPluginConfig):
    """Input plugin for generating timestamps after specified number of
    seconds.
    """

    def __init__(self, *, config: TimerInputPluginConfig, **kwargs) -> None:
        super().__init__(config=config, **kwargs)

        self._config: TimerInputPluginConfig

        mode = kwargs['mode']
        if mode == TimeMode.SAMPLE and self._config.repeat is None:
            raise PluginConfigurationError(
                f'Repeats count must be set for "{mode}" mode'
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
        deltas = arange(
            start=timeout,
            stop=timeout * (self._config.repeat + 1),
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
        timeout = timedelta(microseconds=self._config.seconds)

        # skip past timestamps
        skip_cycles = (datetime.now().astimezone() - start) // timeout
        if skip_cycles > 0:
            timestamp = start + (timeout * skip_cycles)
        else:
            timestamp = start

        if self._config.repeat is not None and skip_cycles > 0:
            repeat_count = max(self._config.repeat - skip_cycles, 0)
        else:
            repeat_count = self._config.repeat

        for _ in (
            i_repeat(None)
            if self._config.repeat is None
            else range(repeat_count)
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
