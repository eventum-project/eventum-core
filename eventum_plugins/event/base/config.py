from abc import ABC

from pydantic import BaseModel


class EventPluginConfig(ABC, BaseModel, extra='forbid', frozen=True):
    """Base config model for event plugins."""
