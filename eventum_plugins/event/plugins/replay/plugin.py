import logging
import os
import re
from typing import Iterator

from eventum_plugins.event.base.plugin import (EventPlugin, EventPluginParams,
                                               ProduceParams)
from eventum_plugins.event.exceptions import EventsExhausted
from eventum_plugins.event.plugins.replay.config import ReplayEventPluginConfig
from eventum_plugins.exceptions import (PluginConfigurationError,
                                        PluginRuntimeError)

logger = logging.getLogger(__name__)


class ReplayEventPlugin(
    EventPlugin[ReplayEventPluginConfig, EventPluginParams]
):
    """Event plugin for producing events using existing log
    file by replaying it line by line.
    """

    def __init__(
        self,
        config: ReplayEventPluginConfig,
        params: EventPluginParams
    ) -> None:
        super().__init__(config, params)

        self._lines = self._get_next_line()
        self._last_read_position = 0

        if self._config.timestamp_pattern is not None:
            try:
                self._pattern: re.Pattern | None = re.compile(
                    pattern=self._config.timestamp_pattern
                )
            except re.error as e:
                raise PluginConfigurationError(
                    'Failed to compile regular expression for timestamp '
                    f'pattern "{self._config.timestamp_pattern}": {e}'
                )
        else:
            self._pattern = None

    def _read_next_lines(self, count: int) -> list[str]:
        """Read next specified number of lines from the file.

        Parameters
        ----------
        count : int
            Number of lines

        Returns
        -------
        list[str]
            Specified number of lines read from the file

        Raises
        ------
        ValueError
            If parameter `count` is lower than 1

        PluginRuntimeError
            If error occurs during reading the file
        """
        if count < 1:
            raise ValueError(
                'The number of lines must be at least 1'
            )

        try:
            with open(self._config.path) as f:
                f.seek(self._last_read_position, os.SEEK_SET)
                lines = f.readlines(count)
                self._last_read_position = f.tell()
                return lines
        except OSError as e:
            raise PluginRuntimeError(
                f'Failed to read file "{self._config.path}": {e}'
            )

    def _get_next_line(self) -> Iterator[str]:
        """Get next line.

        Yields
        ------
        str
            Line

        Notes
        -----
        Repeating file reading are handled
        """
        while True:
            while lines := self._read_next_lines(self._config.read_batch_size):
                yield from lines

            if not self._config.repeat:
                break

            self._last_read_position = 0

    def produce(self, params: ProduceParams) -> list[str]:
        try:
            line = next(self._lines)
        except StopIteration:
            raise EventsExhausted

        if self._pattern is not None:
            timestamp = params['timestamp']

            if self._config.timestamp_format is None:
                fmt_timestamp = timestamp.isoformat()
            else:
                fmt_timestamp = timestamp.strftime(
                    self._config.timestamp_format
                )

            ts_match = self._pattern.search(line)

            if ts_match is not None:
                line = (
                    line[:ts_match.pos]
                    + fmt_timestamp
                    + line[ts_match.endpos:]
                )
            else:
                logger.warning(
                    'Failed to substitute timestamp into original message',
                )

        return [line]
