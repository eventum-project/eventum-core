import logging
from datetime import datetime

from numpy import array, astype, datetime64
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
                raise PluginConfigurationError(
                    'No timestamps are in the file',
                    context=dict(self.instance_info, file_path=config.source)
                )
            self._logger.info(
                'Timestamps are read from the file',
                file_path=config.source,
                count=len(timestamps)
            )
        else:
            timestamps = [
                to_naive(ts, self._timezone) for ts in config.source
            ]
            self._logger.info(
                'Timestamps are read from the configuration',
                count=len(timestamps)
            )

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
        try:
            with open(filename) as f:
                return [
                    datetime.fromisoformat(line.strip())
                    for line in f.readlines() if line.strip()
                ]
        except (OSError, ValueError) as e:
            raise PluginConfigurationError(
                'Failed to read timestamps from file',
                context=dict(
                    self.instance_info,
                    file_path=filename,
                    reason=str(e)
                )
            ) from None

    def _log_generation_range(self) -> None:
        """Log generation range."""
        start = self._timezone.localize(
            astype(self._timestamps[0], datetime)   # type: ignore[arg-type]
        )
        end = self._timezone.localize(
            astype(self._timestamps[-1], datetime)  # type: ignore[arg-type]
        )
        self._logger.info(
            'Generating in range',
            start_timestamp=start.isoformat(),
            end_timestamp=end.isoformat(),
        )

    def _generate_sample(self) -> None:
        self._log_generation_range()
        self._enqueue(self._timestamps)

    def _generate_live(self) -> None:
        self._log_generation_range()

        future_timestamps = get_future_slice(
            timestamps=self._timestamps,
            after=now64(timezone=self._timezone)
        )

        if len(future_timestamps) < len(self._timestamps):
            self._logger.info('Past timestamp are skipped')

        self._enqueue(future_timestamps)
