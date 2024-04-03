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


class BaseOutputPlugin(ABC):
    """Base class for all output plugins."""

    async def open(self) -> None:
        """Open target for async writing."""
        ...

    async def close(self) -> None:
        """Close target and release acquired resources."""
        ...

    @abstractmethod
    async def write(self, event: str) -> None:
        """Write single event to output stream."""
        ...

    @abstractmethod
    async def write_many(self, events: Iterable[str]) -> None:
        """Write events to output stream."""
        ...

    @staticmethod
    def _format_event(format: OutputFormat, event: str) -> str:
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
