import os

from pydantic import Field, field_validator

from eventum_plugins.event.base.config import EventPluginConfig


class ReplayEventPluginConfig(EventPluginConfig, frozen=True):
    """Configuration for `replay` event plugin.

    Attributes
    ----------
    path : str
        Absolute path to log file

    timestamp_pattern : str | None, default=None
        Regular expression pattern to identify the timestamp
        substitution position within the original message, if value is
        not set, then substitution is not performed, for more
        information about python regex syntax see:
        https://docs.python.org/3/library/re.html#regular-expression-syntax

    timestamp_format : str | None, default=None
        Format string that defines how the actual timestamp should be
        substituted in the log message, the format follows C89 standard,
        for more information see:
        https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
        If value is not set, then default (ISO8601) format is used

    repeat : bool, default=False
        Whether to repeat replaying after the end of file is reached

    read_batch_size : int
        Number of lines to read from the file at a time, this
        parameters controls how often to access file and how many lines
        from file to store in memory
    """
    path: str
    timestamp_pattern: str | None = None
    timestamp_format: str | None = None
    repeat: bool = False
    read_batch_size: int = Field(1000, ge=1, le=1_000_000)

    @field_validator('path')
    def validate_path(cls, v: str):
        if os.path.isabs(v):
            return v

        raise ValueError('Path must be absolute')
