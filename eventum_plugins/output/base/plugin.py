from abc import abstractmethod
from typing import Sequence
from eventum_plugins.base.plugin import Plugin
from eventum_plugins.output.base.config import OutputPluginConfig


class OutputPlugin(Plugin, config_cls=object, register=False):
    """Base class for all output plugins.

    Parameters
    ----------
    config : OutputPluginConfig
        Configuration for a plugin
    """

    @abstractmethod
    def __init__(self, *, config: OutputPluginConfig) -> None:
        ...

    @abstractmethod
    async def open(self) -> None:
        """Open plugin for writing."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close plugin for writing with releasing resources and
        flushing events.
        """
        ...

    @abstractmethod
    async def write(self, events: Sequence[str]) -> int:
        """Write events.

        Parameters
        ----------
        events : Sequence[str]
            Sequence of events to write

        Returns
        -------
        int
            Number of successfully written events
        """
        ...
