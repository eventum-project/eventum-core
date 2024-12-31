from abc import ABC

from pydantic import BaseModel


class PluginConfig(BaseModel, ABC, frozen=True, extra='forbid'):
    """Base config model for plugins."""
