from abc import abstractmethod
from typing import Sequence, TypeVar

from pydantic import RootModel

from eventum_plugins.base.plugin import Plugin, PluginParams
from eventum_plugins.output.base.config import OutputPluginConfig


class OutputPluginParams(PluginParams):
    """Parameters for output plugin."""


config_T = TypeVar('config_T', bound=(OutputPluginConfig | RootModel))
params_T = TypeVar('params_T', bound=OutputPluginParams)


class OutputPlugin(Plugin[config_T, params_T], register=False):
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

    def __init__(self, config: config_T, params: params_T) -> None:
        super().__init__(config, params)

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
