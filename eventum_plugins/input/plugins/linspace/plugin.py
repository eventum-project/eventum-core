from typing import Any, Callable

from numpy import datetime64, linspace, timedelta64
from numpy.typing import NDArray

from eventum_plugins.input.base.plugin import InputPlugin, InputPluginParams
from eventum_plugins.input.normalizers import normalize_versatile_daterange
from eventum_plugins.input.plugins.linspace.config import \
    LinspaceInputPluginConfig
from eventum_plugins.input.utils.array_utils import get_future_slice
from eventum_plugins.input.utils.time_utils import now64, to_naive


class LinspaceInputPlugin(InputPlugin[LinspaceInputPluginConfig]):
    """Input plugin for generating specified count of events linearly
    spaced in specified date range.
    """

    def __init__(
        self,
        config: LinspaceInputPluginConfig,
        params: InputPluginParams
    ) -> None:
        super().__init__(config, params)

    def _generate(self) -> NDArray[datetime64]:
        start, end = normalize_versatile_daterange(
            start=self._config.start,
            end=self._config.end,
            timezone=self._timezone,
            none_start='now'
        )

        self._logger.info(
            'Starting generation',
            start_timestamp=start.isoformat(),
            end_timestamp=end.isoformat()
        )

        space = linspace(
            start=0,
            stop=1,
            num=self._config.count,
            endpoint=self._config.endpoint,
        )

        first = datetime64(to_naive(start, self._timezone), 'us')
        timedelta = timedelta64((end - start), 'us')

        timestamps = first + (timedelta * space)
        return timestamps

    def _generate_sample(
        self,
        on_events: Callable[[NDArray[datetime64]], Any]
    ) -> None:
        timestamps = self._generate()
        on_events(timestamps)

    def _generate_live(
        self,
        on_events: Callable[[NDArray[datetime64]], Any]
    ) -> None:
        timestamps = self._generate()

        future_timestamps = get_future_slice(
            timestamps=timestamps,
            after=now64(self._timezone)
        )

        skipped = len(timestamps) - len(future_timestamps)
        if skipped > 0:
            self._logger.info(
                'Past timestamps is skipped',
                count=skipped
            )

        on_events(future_timestamps)
