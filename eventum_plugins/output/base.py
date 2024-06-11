import json
import logging
import os
from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any, Iterable, Self, assert_never

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class OutputPluginError(Exception):
    """Base exception for all output plugin errors."""


class OutputPluginConfigurationError(OutputPluginError):
    """Exception for output plugin configuration errors."""


class OutputPluginRuntimeError(OutputPluginError):
    """Exception for output plugin runtime errors."""


class FormatError(OutputPluginRuntimeError):
    """Exception for formatting errors."""


class OutputPluginBaseConfig(BaseModel, extra='forbid', frozen=True):
    """Base config model for output plugins"""


class OutputFormat(StrEnum):
    ORIGINAL = 'original'
    JSON_LINES = 'json-lines'


class BaseOutputPlugin(ABC):
    """Base class for all output plugins."""
    def __init__(self, config: Any) -> None:
        self._is_opened = False
        self._format: OutputFormat | None = None

    def _set_formatter(self, format: OutputFormat | None) -> None:
        """Set the format to which events will be converted before
        they are passed to `_write` and `_write_many` methods.
        """
        self._format = format

    async def __aenter__(self) -> Self:
        await self.open()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: Any
    ) -> None:
        await self.close()

    async def open(self) -> None:
        """Open target for async writing."""
        if not self._is_opened:
            await self._open()
            self._is_opened = True

    async def close(self) -> None:
        """Close target and release acquired resources."""
        if self._is_opened:
            await self._close()
            self._is_opened = False

    async def write(self, event: str) -> None:
        """Write single event to output stream."""
        if not self._is_opened:
            raise OutputPluginRuntimeError(
                'Output plugin is not opened for writing to target'
            )

        await self._write(self._format_event(event=event))

    async def write_many(self, events: Iterable[str]) -> None:
        """Write many events to output stream."""
        if not self._is_opened:
            raise OutputPluginRuntimeError(
                'Output plugin is not opened for writing to target'
            )

        fmt_events = []
        for event in events:
            fmt_events.append(self._format_event(event=event))

        await self._write_many(fmt_events)

    async def _open(self) -> None:
        """Perform open operation."""
        ...

    async def _close(self) -> None:
        """Perform close operation."""
        ...

    @abstractmethod
    async def _write(self, event: str) -> None:
        """Perform write operation."""
        ...

    @abstractmethod
    async def _write_many(self, events: Iterable[str]) -> None:
        """Perform bulk write operation."""
        ...

    def _format_event(self, event: str) -> str:
        """Format `event` to configured `format`"""
        if self._format is None:
            return event

        try:
            match self._format:
                case OutputFormat.ORIGINAL:
                    return event
                case OutputFormat.JSON_LINES:
                    return json.dumps(json.loads(event), ensure_ascii=False)
                case val:
                    assert_never(val)
        except Exception as e:
            logger.error(
                f'Failed to format event to "{self._format}" format: {e}'
                f'{os.linesep}'
                'Original unformatted event: '
                f'{os.linesep}'
                f'{event}'
            )
            raise FormatError(f'Failed to format event: {e}') from e
