import os

from pydantic import field_validator

from eventum_plugins.event.base.config import EventPluginConfig


class ScriptEventPluginConfig(EventPluginConfig, frozen=True):
    """Configuration for `script` event plugin.

    Attributes
    ----------
    path : str
        Absolute path to script
    """
    path: str

    @field_validator('path')
    def validate_path(cls, v: str):
        if os.path.isabs(v):
            return v

        raise ValueError('Path must be absolute')
