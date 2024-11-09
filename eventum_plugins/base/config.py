from abc import ABC

from pydantic import BaseModel, ConfigDict


class PluginConfig(BaseModel, ABC):
    """Base config model for plugins."""
    model_config = ConfigDict(extra='forbid', frozen=True)
