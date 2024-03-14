from abc import ABC, abstractmethod
import json
from typing import assert_never

from eventum.core.models.application_config import OutputFormat


class OutputPluginError(Exception):
    """Base exception for all output plugin errors."""


class FormatError(OutputPluginError):
    """Exception for formatting errors."""


class BaseOutputPlugin(ABC):
    """Base class for all output plugins."""

    @staticmethod
    def _format_event(format: OutputFormat, event: str) -> str:
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

    @abstractmethod
    def write(self, event: str) -> None:
        """Write single event to output stream."""
        ...

    @abstractmethod
    def write_many(self, events: list[str]) -> None:
        """Write many events to output stream in optimized way."""
        ...
