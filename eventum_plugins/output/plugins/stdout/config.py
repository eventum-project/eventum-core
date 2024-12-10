from typing import Literal

from pydantic import Field

from eventum_plugins.output.base.config import OutputPluginConfig
from eventum_plugins.output.formatters import Format


class StdoutOutputPluginConfig(OutputPluginConfig, frozen=True):
    """Configuration for `stdout` output plugin.

    Attributes
    ----------
    format : Format, default = Format.PLAIN
        Format for formatting output events

    flush_interval : float, default = 1
        Flush interval (in seconds) for flushing events, if value is 0
        then flush is performed for every event

    stream : Literal['stdout', 'stderr'], default='stdout'
        Stream to write events in
    """
    format: Format = Format.PLAIN
    flush_interval: float = Field(default=1, ge=0)
    stream: Literal['stdout', 'stderr'] = 'stdout'
