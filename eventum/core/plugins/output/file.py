import logging
import os
from typing import Iterable

import aiofiles

import eventum.logging_config
from eventum.core.models.application_config import OutputFormat
from eventum.core.plugins.output.base import (BaseOutputPlugin, FormatError,
                                              OutputPluginConfigurationError,
                                              OutputPluginRuntimeError)

eventum.logging_config.apply()
logger = logging.getLogger(__name__)


class FileOutputPlugin(BaseOutputPlugin):
    """Output plugin for writing events to file."""

    def __init__(self, filepath: str, format: OutputFormat) -> None:
        if not os.path.isabs(filepath):
            raise OutputPluginConfigurationError(
                f'Filepath must be absolute, but got "{filepath}"'
            )

        try:
            with open(filepath, 'a') as f:
                if not f.writable():
                    raise OutputPluginConfigurationError(
                        f'File "{filepath}" is not writable'
                    )
        except OSError as e:
            raise OutputPluginConfigurationError(
                f'Failed to open file "{filepath}": {e}'
            )

        self._filepath = filepath
        self._format = format
        self._file = None

    async def open(self) -> None:
        self._file = await aiofiles.open(
            file=self._filepath,
            mode='a',
            encoding='utf-8'
        )

    async def close(self) -> None:
        if self._file is None:
            return

        await self._file.close()
        self._file = None

    async def write(self, event: str) -> None:
        if self._file is None:
            raise OutputPluginRuntimeError(
                'Output plugin is not opened for writing to target'
            )

        try:
            fmt_event = self._format_event(self._format, event)
            fmt_event += os.linesep
        except FormatError as e:
            logger.error(
                f'Failed to format event to "{self._format}" format: {e}'
                f'{os.linesep}'
                'Original unformatted event: '
                f'{os.linesep}'
                f'{event}'
            )
            return
        try:
            await self._file.write(fmt_event)
        except OSError as e:
            logger.error(f'Failed to write event to file: {e}')

    async def write_many(self, events: Iterable[str]) -> None:
        if self._file is None:
            raise OutputPluginRuntimeError(
                'Output plugin is not opened for writing to target'
            )

        fmt_events = []

        for event in events:
            try:
                fmt_event = self._format_event(self._format, event)
                fmt_event += os.linesep
            except FormatError as e:
                logger.error(
                    f'Failed to format event to "{self._format}" format: {e}'
                    f'{os.linesep}'
                    'Original unformatted event: '
                    f'{os.linesep}'
                    f'{event}'
                )
                continue

            fmt_events.append(fmt_event)
        try:
            await self._file.writelines(fmt_events)
        except OSError as e:
            logger.error(
                f'Failed to write {len(fmt_events)} events to file: {e}'
            )
