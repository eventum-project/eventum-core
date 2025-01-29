import os
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class StartupParameters(BaseModel, extra='forbid', frozen=True):
    """Startup parameters.

    Attributes
    ----------
    source : Literal['db', 'file'], default='file'
        Type of source with configuration

    path : str
        Absolute path to configuration file or database file with
        defined generators to run on startup
    """
    source: Literal['db', 'file'] = Field(default='file')
    path: str = Field(min_length=1)

    @field_validator('path')
    def validate_path(cls, v: str):
        if os.path.isabs(v):
            return v
        raise ValueError('Path must be absolute')
