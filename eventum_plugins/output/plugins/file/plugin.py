import asyncio
import logging
import os
from typing import Sequence

import aiofiles
from aiofiles.threadpool.text import AsyncTextIOWrapper

from eventum_plugins.exceptions import PluginRuntimeError
from eventum_plugins.output.base.plugin import OutputPlugin, OutputPluginParams
from eventum_plugins.output.formatters import format_events
from eventum_plugins.output.plugins.file.config import FileOutputPluginConfig

logger = logging.getLogger(__name__)


class FileOutputPlugin(
    OutputPlugin[FileOutputPluginConfig, OutputPluginParams]
):
    """Output plugin for writing events to file."""

    def __init__(
        self,
        config: FileOutputPluginConfig,
        params: OutputPluginParams
    ) -> None:
        super().__init__(config, params)

        self._file: AsyncTextIOWrapper

        self._flushing_task: asyncio.Task

        self._cleanup_task: asyncio.Task
        self._cleaned_up = False
        self._cleanup_lock = asyncio.Lock()

    async def _is_operable(self) -> bool:
        """Check if file is operable (not closed and not deleted).

        Returns
        -------
        bool
            Check result

        Notes
        -----
        Cleanup lock must be acquired before running this method to
        avoid unexpected file closing when trying to get fileno
        """
        if self._file.closed:
            return False

        fileno = self._file.fileno()

        stat = await self._loop.run_in_executor(
            executor=None,
            func=lambda: os.stat(fileno)
        )

        return True if stat.st_nlink > 0 else False

    async def _start_flushing(self) -> None:
        """Start flushing cycle based on specified flush interval."""
        if self._config.flush_interval == 0:
            return

        while True:
            await asyncio.sleep(self._config.flush_interval)

            async with self._cleanup_lock:
                if await self._is_operable():
                    await self._file.flush()

    async def _schedule_cleanup(self) -> None:
        """Schedule file closing after specified number of seconds."""
        await asyncio.sleep(self._config.cleanup_interval)

        async with self._cleanup_lock:
            if await self._is_operable():
                await self._file.flush()
                await self._file.close()

            self._cleaned_up = True

    def _create_descriptor(self, path: str, flags: int) -> int:
        """Create file descriptor opened for writing with specified
        file mode.

        Parameters
        ----------
        path : str
            Path to file

        flags : int
            Flags for file descriptor

        Returns
        -------
        int
            File descriptor number
        """
        return os.open(
            path=path,
            flags=flags,
            mode=int(str(self._config.file_mode), base=8)
        )

    async def _open_file(self) -> AsyncTextIOWrapper:
        """Open file for the first time.

        Returns
        -------
        AsyncTextIOWrapper
            Opened file
        """
        return await aiofiles.open(
            file=self._config.path,
            mode='a' if self._config.write_mode == 'append' else 'w',
            encoding='utf-8',
            opener=self._create_descriptor
        )

    async def _reopen_file(self) -> AsyncTextIOWrapper:
        """Reopen file after deleting or cleanup.

        Returns
        -------
        AsyncTextIOWrapper
            Opened file
        """
        return await aiofiles.open(
            file=self._config.path,
            mode='a',
            encoding='utf-8',
            opener=self._create_descriptor
        )

    async def _open(self) -> None:
        try:
            self._file = await self._open_file()
        except OSError as e:
            raise PluginRuntimeError(str(e))

        if not await self._file.writable():
            raise PluginRuntimeError('File is not writable')

        self._flushing_task = self._loop.create_task(self._start_flushing())
        self._cleanup_task = self._loop.create_task(self._schedule_cleanup())

    async def _close(self) -> None:
        self._flushing_task.cancel()
        self._cleanup_task.cancel()

        async with self._cleanup_lock:
            if await self._is_operable():
                await self._file.flush()
                await self._file.close()

    async def _write(self, events: Sequence[str]) -> int:
        formatted_events = await self._loop.run_in_executor(
            executor=None,
            func=lambda: format_events(
                events=events,
                format=self._config.format,
                ignore_errors=True,
                error_callback=lambda e: logger.warning(
                    f'Failed to format event to "{self._config.format}" '
                    f'format in "{self}" output plugin: {e}',
                )
            )
        )

        if not formatted_events:
            return 0

        async with self._cleanup_lock:
            if not await self._is_operable():
                try:
                    self._file = await self._reopen_file()
                except OSError as e:
                    raise PluginRuntimeError(f'Failed to reopen file: {e}')

            if not self._cleaned_up:
                self._cleanup_task.cancel()

            self._cleaned_up = False
            self._cleanup_task = self._loop.create_task(
                self._schedule_cleanup()
            )

            try:
                await self._file.writelines(e + os.linesep for e in events)
            except OSError as e:
                raise PluginRuntimeError(
                    f'Failed to write events to file: {e}'
                ) from e

            if self._config.flush_interval == 0:
                await self._file.flush()

        return len(formatted_events)
