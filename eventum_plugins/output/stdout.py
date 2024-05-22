import asyncio
import sys
from typing import Iterable

from eventum_plugins.output.base import (BaseOutputPlugin,
                                         OutputFormat, OutputPluginBaseConfig)


class StdOutOutputConfig(OutputPluginBaseConfig):
    format: OutputFormat = OutputFormat.ORIGINAL


class StdoutOutputPlugin(BaseOutputPlugin):
    """Output plugin for writing events to stdout."""

    def __init__(self, config: StdOutOutputConfig) -> None:
        super().__init__(format=config.format)

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
        self._writer.write(event.encode())          # type: ignore
        await self._writer.drain()                  # type: ignore

        return 1

    async def _write_many(self, encoded_events: Iterable[str]) -> int:
        encoded_events = [event.encode() for event in encoded_events]

        self._writer.writelines(encoded_events)     # type: ignore
        await self._writer.drain()                  # type: ignore

        return len(encoded_events)


PLUGIN_CLASS = StdoutOutputPlugin
CONFIG_CLASS = StdOutOutputConfig
