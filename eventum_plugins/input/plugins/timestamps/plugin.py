import logging
from datetime import datetime
from typing import Any, Callable

from numpy import array, datetime64
from numpy.typing import NDArray

from eventum_plugins.exceptions import PluginConfigurationError
from eventum_plugins.input.base.plugin import InputPlugin, InputPluginParams
from eventum_plugins.input.plugins.timestamps.config import \
    TimestampsInputPluginConfig
from eventum_plugins.input.utils.array_utils import get_future_slice
from eventum_plugins.input.utils.time_utils import now64, to_naive

logger = logging.getLogger(__name__)


class TimestampsInputPlugin(InputPlugin[TimestampsInputPluginConfig]):
    """Input plugin for generating events at specified timestamps."""

    def __init__(
        self,
        config: TimestampsInputPluginConfig,
        params: InputPluginParams
    ) -> None:
        super().__init__(config, params)

        if isinstance(config.source, str):
            timestamps: list[datetime] = [
                to_naive(ts, self._timezone)
                for ts in self._read_timestamps_from_file(config.source)
            ]
            if not timestamps:
                raise PluginConfigurationError('No timestamps in the file')
        else:
            timestamps = [
                to_naive(ts, self._timezone) for ts in config.source
            ]

        self._timestamps: NDArray[datetime64] = array(
            timestamps,
            dtype='datetime64[us]'
        )

    def _read_timestamps_from_file(self, filename: str) -> list[datetime]:
        """Read timestamps from specified file.

        Parameters
        ----------
        filename : str
            Path to file with timestamps that are delimited with new
            line

        Returns
        -------
        list[datetime]
            List of datetime objects

        Raises
        ------
        PluginConfigurationError
            If cannot read content of the specified file or parse
            timestamps
        """
        self._logger.info('Reading timestamps from file', file_path=filename)
        try:
            with open(filename) as f:
                return [
                    datetime.fromisoformat(line.strip())
                    for line in f.readlines() if line.strip()
                ]
        except (OSError, ValueError) as e:
            raise PluginConfigurationError(
                f'Failed to read timestamps from file: {e}'
            ) from None

    def _generate_sample(
        self,
        on_events: Callable[[NDArray[datetime64]], Any]
    ) -> None:
        self._logger.info('Generating in provided range')
        on_events(self._timestamps)

    def _generate_live(
        self,
        on_events: Callable[[NDArray[datetime64]], Any]
    ) -> None:
        self._logger.info('Generating in provided range')

        future_timestamps = get_future_slice(
            timestamps=self._timestamps,
            after=now64(timezone=self._timezone)
        )

        if len(future_timestamps) < len(self._timestamps):
            self._logger.info('Past timestamp are skipped')

        on_events(future_timestamps)
