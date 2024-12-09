import asyncio
import logging
import os
import sys
from typing import Sequence, assert_never

from eventum_plugins.output.base.plugin import OutputPlugin, OutputPluginParams
from eventum_plugins.output.formatters import format_events
from eventum_plugins.output.plugins.stdout.config import \
    StdoutOutputPluginConfig

logger = logging.getLogger(__name__)


class StdoutOutputPlugin(
    OutputPlugin[StdoutOutputPluginConfig, OutputPluginParams]
):
    """Output plugin for writing events to stdout."""

    def __init__(
        self,
        config: StdoutOutputPluginConfig,
        params: OutputPluginParams
    ) -> None:
        super().__init__(config, params)

        self._writer: asyncio.StreamWriter
        self._flushing_task: asyncio.Task

    async def _start_flushing(self) -> None:
        """Start flushing cycle based on specified flush interval."""
        if self._config.flush_interval == 0:
            return

        while True:
            await asyncio.sleep(self._config.flush_interval)
            await self._writer.drain()

    async def _open(self) -> None:
        match self._config.stream:
            case 'stdout':
                pipe = sys.stdout
            case 'stderr':
                pipe = sys.stderr
            case val:
                assert_never(val)

        loop = asyncio.get_event_loop()
        w_transport, w_protocol = await loop.connect_write_pipe(
            protocol_factory=asyncio.streams.FlowControlMixin,
            pipe=pipe
        )
        self._writer = asyncio.StreamWriter(
            transport=w_transport,
            protocol=w_protocol,
            reader=None,
            loop=loop
        )
        self._flushing_task = self._loop.create_task(self._start_flushing())

    async def _close(self) -> None:
        self._flushing_task.cancel()
        await self._writer.drain()
        self._writer.close()

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

        self._writer.writelines(
            [f'{event}{os.linesep}'.encode() for event in formatted_events]
        )

        if self._config.flush_interval == 0:
            await self._writer.drain()

        return len(formatted_events)
