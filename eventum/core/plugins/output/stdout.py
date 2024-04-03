import asyncio
import logging
import os
import sys
from typing import Iterable

import eventum.logging_config
from eventum.core.models.application_config import OutputFormat
from eventum.core.plugins.output.base import (BaseOutputPlugin, FormatError,
                                              OutputPluginRuntimeError)

eventum.logging_config.apply()
logger = logging.getLogger(__name__)


class StdoutOutputPlugin(BaseOutputPlugin):
    """Output plugin for writing events to stdout."""

    def __init__(self, format: OutputFormat) -> None:
        self._format = format
        self._writer = None

    async def open(self) -> None:
        loop = asyncio.get_event_loop()
        w_transport, w_protocol = await loop.connect_write_pipe(
            protocol_factory=asyncio.streams.FlowControlMixin,
            pipe=sys.stdout
        )
        self._writer = asyncio.StreamWriter(
            transport=w_transport,
            protocol=w_protocol,
            reader=None,
            loop=loop
        )

    async def write(self, event: str) -> None:
        if self._writer is None:
            raise OutputPluginRuntimeError(
                'Output plugin is not opened for writing to target'
            )

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

        self._writer.write(fmt_event.encode())
        await self._writer.drain()

    async def write_many(self, events: Iterable[str]) -> None:
        if self._writer is None:
            raise OutputPluginRuntimeError(
                'Output plugin is not opened for writing to target'
            )

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

            fmt_events.append(fmt_event.encode())

        self._writer.writelines(fmt_events)
        await self._writer.drain()
