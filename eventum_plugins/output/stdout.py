import asyncio
import sys
from typing import Iterable

from eventum_plugins.output.base import (BaseOutputPlugin,
                                         OutputFormat, OutputPluginBaseConfig)


class StdOutOutputConfig(OutputPluginBaseConfig, frozen=True):
    format: OutputFormat = OutputFormat.ORIGINAL


class StdoutOutputPlugin(BaseOutputPlugin):
    """Output plugin for writing events to stdout."""

    def __init__(self, config: StdOutOutputConfig) -> None:
        super().__init__(format=config.format)

        self._writer: asyncio.StreamWriter

    async def _open(self) -> None:
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

    async def _close(self) -> None:
        self._writer.close()

    async def _write(self, event: str) -> int:
        self._writer.write(event.encode())
        await self._writer.drain()

        return 1

    async def _write_many(self, events: Iterable[str]) -> int:
        encoded_events = [event.encode() for event in events]

        self._writer.writelines(encoded_events)
        await self._writer.drain()

        return len(encoded_events)


PLUGIN_CLASS = StdoutOutputPlugin
CONFIG_CLASS = StdOutOutputConfig
