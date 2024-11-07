from abc import ABC

from pydantic import BaseModel


class OutputPluginConfig(ABC, BaseModel, extra='forbid', frozen=True):
    """Base config model for output plugins."""
