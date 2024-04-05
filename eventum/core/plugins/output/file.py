import logging
import os
from typing import Iterable

import aiofiles
import aiofiles.base
import eventum.logging_config
from eventum.core.models.application_config import (FileOutputConfig,
                                                    OutputFormat)
from eventum.core.plugins.output.base import (BaseOutputPlugin, FormatError,
                                              OutputPluginConfigurationError,
                                              OutputPluginRuntimeError,
                                              format_event)

eventum.logging_config.apply()
logger = logging.getLogger(__name__)


class FileOutputPlugin(BaseOutputPlugin):
    """Output plugin for writing events to file."""
    def __init__(self, filepath: str, format: OutputFormat) -> None:
        super().__init__()

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

    async def _open(self) -> None:
        self._file = await aiofiles.open(       # type: ignore
            file=self._filepath,
            mode='a',
            encoding='utf-8'
        )

    async def _close(self) -> None:
        if self._file is None:
            return

        await self._file.close()
        self._file = None

    async def _write(self, event: str) -> int:
        try:
            fmt_event = format_event(self._format, event)
            fmt_event += os.linesep
        except FormatError as e:
            logger.warning(
                f'Failed to format event to "{self._format}" format: {e}'
                f'{os.linesep}'
                'Original unformatted event: '
                f'{os.linesep}'
                f'{event}'
            )
            return 0
        try:
            await self._file.write(fmt_event)           # type: ignore
        except OSError as e:
            raise OutputPluginRuntimeError(
                f'Failed to write event to file: {e}'
            ) from e

        return 1

    async def _write_many(self, events: Iterable[str]) -> int:
        fmt_events = []

        for event in events:
            try:
                fmt_event = format_event(self._format, event)
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
        try:
            await self._file.writelines(fmt_events)     # type: ignore
        except OSError as e:
            raise OutputPluginRuntimeError(
                f'Failed to write {len(fmt_events)} events to file: {e}'
            ) from e

        return len(fmt_events)

    @classmethod
    def create_from_config(
        cls,
        config: FileOutputConfig
    ) -> 'FileOutputPlugin':
        return FileOutputPlugin(filepath=config.path, format=config.format)


def load_plugin():
    """Return class of plugin from current module."""
    return FileOutputPlugin
