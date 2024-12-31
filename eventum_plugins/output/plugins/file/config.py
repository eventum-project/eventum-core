import os
from typing import Literal

from pydantic import Field, field_validator

from eventum_plugins.output.base.config import OutputPluginConfig
from eventum_plugins.output.encodings import Encoding
from eventum_plugins.output.formatters import Format


class FileOutputPluginConfig(OutputPluginConfig, frozen=True):
    """Configuration for `file` output plugin.

    Attributes
    ----------
    path : str
        Absolute path of the file to write

    format : Format, default = Format.PLAIN
        Format for formatting output events

    flush_interval : float, default = 1
        Flush interval (in seconds) for flushing events, if value is 0
        then flush is performed for every event

    cleanup_interval : float, default = 10
        Interval (in seconds) to wait new events before closing file,
        file is reopened once new events are received

    file_mode : int, default = -1
        File access mode to use (e.g. 640), if value is -1 then default
        OS mode is used

    write_mode : Literal['append', 'overwrite'], default = 'append'
        Mode that is used to write if the file already exists

    encoding : Encoding, default='utf-8'
        Encoding

    separator : str, default=os.linesep
        Separator between events
    """
    path: str
    format: Format = Format.PLAIN
    flush_interval: float = Field(default=1, ge=0)
    cleanup_interval: float = Field(default=10, ge=1.0)
    file_mode: int = Field(default=-1, ge=-1, le=7777)
    write_mode: Literal['append', 'overwrite'] = 'append'
    encoding: Encoding = Field(default='utf_8')
    separator: str = Field(default=os.linesep)

    @field_validator('path')
    def validate_path(cls, v: str):
        if os.path.isabs(v):
            return v
        raise ValueError('Path must be absolute')
