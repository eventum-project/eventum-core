from typing import Literal
from pydantic import BaseModel


class LogParameters(BaseModel, extra='forbid', frozen=True):
    """Log parameters.

    Attributes
    ----------
    level : Literal['info', 'warning', 'error', 'critical'], default='info'
        Log level

    format : Literal['plain', 'json'], default='plain'
        Format format
    """
    level: Literal['info', 'warning', 'error', 'critical'] = 'info'
    format: Literal['plain', 'json'] = 'plain'
