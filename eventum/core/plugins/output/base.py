import json
from abc import ABC, abstractmethod
from typing import Iterable, assert_never

from eventum.core.models.application_config import OutputFormat


class OutputPluginError(Exception):
    """Base exception for all output plugin errors."""


class OutputPluginConfigurationError(OutputPluginError):
    """Exception for output plugin configuration errors."""


class OutputPluginRuntimeError(OutputPluginError):
    """Exception for output plugin runtime errors."""


class FormatError(OutputPluginRuntimeError):
    """Exception for formatting errors."""


def format_event(format: OutputFormat, event: str) -> str:
    """Format `event` to specified `format`"""
    try:
        match format:
            case OutputFormat.ORIGINAL:
                return event
            case OutputFormat.JSON_LINES:
                return json.dumps(json.loads(event), ensure_ascii=False)
            case val:
                assert_never(val)
    except Exception as e:
        raise FormatError(str(e)) from e


class BaseOutputPlugin(ABC):
    """Base class for all output plugins."""
    def __init__(self) -> None:
        self._is_opened = False

    async def open(self) -> None:
        """Open target for async writing."""
        await self._open()
        self._is_opened = True

    async def close(self) -> None:
        """Close target and release acquired resources."""
        await self._close()
        self._is_opened = False

    async def write(self, event: str) -> None:
        """Write single event to output stream."""
        if not self._is_opened:
            raise OutputPluginRuntimeError(
                'Output plugin is not opened for writing to target'
            )
        await self._write(event)

    async def write_many(self, events: Iterable[str]) -> None:
        """Write many events to output stream."""
        if not self._is_opened:
            raise OutputPluginRuntimeError(
                'Output plugin is not opened for writing to target'
            )
        await self._write_many(events)

    async def _open(self) -> None:
        """Perform open operation. May be overridden in subclasses."""
        ...

    async def _close(self) -> None:
        """Perform close operation. May be overridden in subclasses."""
        ...

    @abstractmethod
    async def _write(self, event: str) -> None:
        """Perform write operation. Must be overridden in subclasses."""
        ...

    @abstractmethod
    async def _write_many(self, events: Iterable[str]) -> None:
        """Perform bulk write operation. Must be overridden in subclasses."""
        ...
