from typing import Literal

from pydantic import BaseModel, Field


class StartupParameters(BaseModel, extra='forbid', frozen=True):
    """Startup parameters.

    Attributes
    ----------
    source : Literal['db', 'file'], default='file'
        Type of source with generators definitions
    """
    source: Literal['db', 'file'] = Field(default='file')
