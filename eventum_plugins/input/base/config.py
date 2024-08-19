from abc import ABC

from pydantic import BaseModel


class InputPluginConfig(ABC, BaseModel, extra='forbid', frozen=True):
    """Base config model for input plugins.

    Attributes
    ----------
    tags : tuple[str, ...], optional
        Tags list attached to an input plugin (the default is no tags)
    """
    tags: tuple[str, ...] = tuple()
