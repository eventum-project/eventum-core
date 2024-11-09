from abc import abstractmethod
from typing import Sequence, Unpack

from eventum_plugins.base.plugin import Plugin, PluginKwargs
from eventum_plugins.output.base.config import OutputPluginConfig


class OutputPluginKwargs(PluginKwargs):
    """Arguments for output plugin configuration."""


class OutputPlugin(Plugin, config_cls=object, register=False):
    """Base class for all output plugins.

    Parameters
    ----------
    **kwargs : Unpack[OutputPluginKwargs]
        Arguments for plugin configuration (see `OutputPluginKwargs`)

    Raises
    ------
    PluginConfigurationError
        If any error occurs during initializing plugin
    """

    def __init__(self, **kwargs: Unpack[OutputPluginKwargs]) -> None:
        super().__init__(**kwargs)
        self._config = OutputPluginConfig

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
