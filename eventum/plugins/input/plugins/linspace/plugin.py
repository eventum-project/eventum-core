from typing import Iterator

from numpy import datetime64, linspace, timedelta64
from numpy.typing import NDArray

from eventum.plugins.input.base.plugin import InputPlugin, InputPluginParams
from eventum.plugins.input.normalizers import normalize_versatile_daterange
from eventum.plugins.input.plugins.linspace.config import \
    LinspaceInputPluginConfig
from eventum.plugins.input.utils.array_utils import get_future_slice
from eventum.plugins.input.utils.time_utils import now64, to_naive


class LinspaceInputPlugin(
    InputPlugin[LinspaceInputPluginConfig, InputPluginParams]
):
    """Input plugin for generating specified count of events linearly
    spaced in specified date range.

    Notes
    -----
    Plugin allocates all the timestamp at generation start. If you have
    deal with large number of timestamps and need lazy evaluation, see
    timer input plugin
    """

    def __init__(
        self,
        config: LinspaceInputPluginConfig,
        params: InputPluginParams
    ) -> None:
        super().__init__(config, params)

    def _generate(
        self,
        size: int,
        skip_past: bool = True
    ) -> Iterator[NDArray[datetime64]]:
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

        space = linspace(
            start=0,
            stop=1,
            num=self._config.count,
            endpoint=self._config.endpoint,
        )

        first = datetime64(to_naive(start, self._timezone).isoformat(), 'us')
        timedelta = timedelta64((end - start), 'us')

        timestamps = first + (timedelta * space)

        if skip_past:
            timestamps = get_future_slice(
                timestamps=timestamps,
                after=now64(self._timezone)
            )
            if not timestamps:
                self._logger.info(
                    'All timestamps are in past, nothing to generate'
                )
                return

        self._buffer.mv_push(timestamps)

        yield from self._buffer.read(size, partial=True)
