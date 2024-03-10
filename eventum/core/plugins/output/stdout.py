import json
import os
import sys
from typing import assert_never

from eventum.core.models.application_config import OutputFormat
from eventum.core.plugins.output.base import (BaseOutputPlugin, FormatError)


class StdoutOutputPlugin(BaseOutputPlugin):
    def __init__(self, format: OutputFormat) -> None:
        self._format = format

    def _format_event(self, event: str) -> str:
        match self._format:
            case OutputFormat.ORIGINAL:
                return event
            case OutputFormat.JSON_LINES:
                try:
                    return json.dumps(json.loads(event), ensure_ascii=False)
                except Exception:
                    raise FormatError('Failed to format event')
            case val:
                assert_never(val)

    def write(self, event: str) -> None:
        try:
            fmt_content = self._format_event(event)
        except FormatError:
            return

        sys.stdout.write(fmt_content)
        sys.stdout.write(os.linesep)
        sys.stdout.flush()

    def write_many(self, events: list[str]) -> None:
        fmt_events = []

        for event in events:
            try:
                fmt_events.append(self._format_event(event))
            except FormatError:
                pass

        sys.stdout.writelines(fmt_events)
        sys.stdout.write(os.linesep)
        sys.stdout.flush()
