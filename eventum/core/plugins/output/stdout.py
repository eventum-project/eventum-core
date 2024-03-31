import logging
import os
import sys
from typing import Collection

import eventum.logging_config
from eventum.core.models.application_config import OutputFormat
from eventum.core.plugins.output.base import BaseOutputPlugin, FormatError

eventum.logging_config.apply()
logger = logging.getLogger(__name__)


class StdoutOutputPlugin(BaseOutputPlugin):
    """Output plugin for writing events to stdout."""

    def __init__(self, format: OutputFormat) -> None:
        self._format = format

    def write(self, event: str) -> None:
        try:
            fmt_event = self._format_event(self._format, event)
            fmt_event += os.linesep
        except FormatError as e:
            logger.warning(
                f'Failed to format event to "{self._format}" format: {e}'
                f'{os.linesep}'
                'Original unformatted event: '
                f'{os.linesep}'
                f'{event}'
            )
            return

        sys.stdout.write(fmt_event)
        sys.stdout.flush()

    def write_many(self, events: Collection[str]) -> None:
        fmt_events = []

        for event in events:
            try:
                fmt_event = self._format_event(self._format, event)
                fmt_event += os.linesep
            except FormatError as e:
                logger.warning(
                    f'Failed to format event to "{self._format}" format: {e}'
                    f'{os.linesep}'
                    'Original unformatted event: '
                    f'{os.linesep}'
                    f'{event}'
                )
                continue

            fmt_events.append(fmt_event)

        sys.stdout.writelines(fmt_events)
        sys.stdout.flush()
