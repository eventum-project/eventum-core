from abc import ABC

from eventum_plugins.base.config import PluginConfig


class InputPluginConfig(PluginConfig, ABC, frozen=True):
    """Base config model for input plugins.

    Attributes
    ----------
    tags : tuple[str, ...], optional
        Tags list attached to an input plugin (the default is no tags)
    """
    tags: tuple[str, ...] = tuple()
