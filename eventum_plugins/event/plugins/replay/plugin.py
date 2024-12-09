import logging
import os
import re
from datetime import datetime
from typing import Any, Iterator

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
                self._pattern: re.Pattern[Any] | None = re.compile(
                    pattern=self._config.timestamp_pattern
                )
            except re.error as e:
                raise PluginConfigurationError(
                    'Failed to compile regular expression for timestamp '
                    f'pattern "{self._config.timestamp_pattern}": {e}'
                ) from None
        else:
            self._pattern = None

        if not os.path.exists(self._config.path):
            raise PluginConfigurationError(
                f'File "{self._config.path}" does not exist'
            )

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
                lines: list[str] = []
                for _ in range(count):
                    line = f.readline().rstrip('\n\r')

                    if not line:
                        break

                    lines.append(line)

                self._last_read_position = f.tell()

                return lines
        except OSError as e:
            raise PluginRuntimeError(
                f'Failed to read file "{self._config.path}": {e}'
            ) from None

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

    def _format_timestamp(self, timestamp: datetime) -> str:
        """Format timestamp to specified format.

        Parameters
        ----------
        timestamp : datetime
            Timestamp to format

        Returns
        -------
        str
            Formatted timestamp
        """
        if self._config.timestamp_format is None:
            return timestamp.isoformat()
        else:
            return timestamp.strftime(
                self._config.timestamp_format
            )

    def _substitute_string(
        self,
        message: str,
        string: str,
        pattern: re.Pattern[Any],
        group_name: str
    ) -> str:
        """Substitute string into original message in position defined
        by pattern named group.

        Parameters
        ----------
        message : str
            Original message

        string : str
            String to substitute

        pattern : re.Pattern
            Pattern that defines position of substitution

        group_name : str
            Named group in pattern that defines position of substitution

        Returns
        -------
        str
            New message with substituted string

        Raises
        ------
        ValueError
            If substitution is failed
        """
        msg_match = pattern.search(message)  # type: ignore

        if msg_match is None:
            raise ValueError('No match found')

        try:
            match_start = msg_match.start(group_name)
            match_end = msg_match.end(group_name)
        except IndexError:
            raise ValueError(
                f'No group "{group_name}" found in match'
            ) from None

        if match_start == -1 or match_end == -1:
            raise ValueError(
                f'Group "{group_name}" did not contribute to the match'
            )

        return message[:match_start] + string + message[match_end:]

    def produce(self, params: ProduceParams) -> list[str]:
        try:
            line = next(self._lines)
        except StopIteration:
            raise EventsExhausted() from None

        if self._pattern is None:
            return [line]

        fmt_timestamp = self._format_timestamp(
            timestamp=params['timestamp']
        )

        try:
            line = self._substitute_string(
                message=line,
                string=fmt_timestamp,
                pattern=self._pattern,
                group_name='timestamp'
            )
        except ValueError as e:
            logger.warning(
                f'Failed to substitute timestamp into original message: {e}'
            )

        return [line]
