import logging
import os
from typing import Iterable

import aiofiles
from aiofiles.threadpool.text import AsyncTextIOWrapper
from pydantic import field_validator

from eventum_plugins.output.base import (BaseOutputPlugin, OutputFormat,
                                         OutputPluginBaseConfig,
                                         OutputPluginConfigurationError,
                                         OutputPluginRuntimeError)

logger = logging.getLogger(__name__)


class FileOutputConfig(OutputPluginBaseConfig, frozen=True):
    path: str
    format: OutputFormat = OutputFormat.ORIGINAL
    flush: bool = False

    @field_validator('path')
    def validate_path(cls, v: str):
        if os.path.isabs(v):
            return v
        raise ValueError('Path must be absolute')


class FileOutputPlugin(BaseOutputPlugin):
    """Output plugin for writing events to file."""
    def __init__(self, config: FileOutputConfig) -> None:
        super().__init__(config)
        self._set_formatter(format=config.format)

        self._filepath = config.path
        self._flush = config.flush

        self._check_file_access()

        self._file: AsyncTextIOWrapper

    def _check_file_access(self) -> None:
        try:
            with open(self._filepath, 'a') as f:
                if not f.writable():
                    raise OutputPluginConfigurationError(
                        f'File "{self._filepath}" is not writable'
                    )
        except OSError as e:
            raise OutputPluginConfigurationError(
                f'Failed to open file "{self._filepath}": {e}'
            )

    async def _open(self) -> None:
        self._file = await aiofiles.open(
            file=self._filepath,
            mode='a',
            encoding='utf-8'
        )

    async def _close(self) -> None:
        await self._file.flush()
        await self._file.close()

    async def _write(self, event: str) -> None:
        try:
            await self._file.write(event + os.linesep)
        except OSError as e:
            raise OutputPluginRuntimeError(
                f'Failed to write event to file: {e}'
            ) from e

        if self._flush:
            await self._file.flush()

    async def _write_many(self, events: Iterable[str]) -> None:
        try:
            await self._file.writelines(map(lambda e: e + os.linesep, events))
        except OSError as e:
            raise OutputPluginRuntimeError(
                f'Failed to write events to file: {e}'
            ) from e

        if self._flush:
            await self._file.flush()


PLUGIN_CLASS = FileOutputPlugin
CONFIG_CLASS = FileOutputConfig
