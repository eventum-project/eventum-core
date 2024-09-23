

import os
from datetime import datetime

from pydantic import Field, field_validator

from eventum_plugins.input.base.config import InputPluginConfig


class TimestampsInputPluginConfig(InputPluginConfig, frozen=True):
    """Configuration for `timestamps` input plugin.

    Attributes
    ----------
    source : list[datetime] | str
        List of timestamps or absolute path to file with new line
        separated timestamps in ISO8601 format

    Notes
    -----
    It is expected that timestamps are already sorted in ascending
    order
    """
    source: list[datetime] | str = Field(..., min_length=1)

    @field_validator('source')
    def validate_source(cls, v: list[datetime] | str) -> list[datetime] | str:
        if isinstance(v, str) and not os.path.isabs(v):
            raise ValueError('Path must be absolute')

        return v
