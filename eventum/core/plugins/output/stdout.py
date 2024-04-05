import asyncio
import logging
import os
import sys
from typing import Iterable

import eventum.logging_config
from eventum.core.models.application_config import (OutputFormat,
                                                    StdOutOutputConfig)
from eventum.core.plugins.output.base import (BaseOutputPlugin, FormatError,
                                              format_event)

eventum.logging_config.apply()
logger = logging.getLogger(__name__)


class StdoutOutputPlugin(BaseOutputPlugin):
    """Output plugin for writing events to stdout."""

    def __init__(self, format: OutputFormat) -> None:
        super().__init__()

        self._format = format
        self._writer = None

    async def _open(self) -> None:
        loop = asyncio.get_event_loop()
        w_transport, w_protocol = await loop.connect_write_pipe(
            protocol_factory=asyncio.streams.FlowControlMixin,
            pipe=sys.stdout
        )
        self._writer = asyncio.StreamWriter(        # type: ignore
            transport=w_transport,
            protocol=w_protocol,
            reader=None,
            loop=loop
        )

    async def _close(self) -> None:
        if self._writer is None:
            return

        self._writer.close()
        self._writer = None

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

        self._writer.write(fmt_event.encode())      # type: ignore
        await self._writer.drain()                  # type: ignore

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

            fmt_events.append(fmt_event.encode())

        self._writer.writelines(fmt_events)         # type: ignore
        await self._writer.drain()                  # type: ignore

        return len(fmt_events)

    @classmethod
    def create_from_config(
        cls,
        config: StdOutOutputConfig
    ) -> 'StdoutOutputPlugin':
        return StdoutOutputPlugin(format=config.format)
