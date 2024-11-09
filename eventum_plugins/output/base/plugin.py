from abc import abstractmethod
from typing import Required, Sequence, TypedDict, Unpack

from eventum_plugins.base.plugin import Plugin
from eventum_plugins.output.base.config import OutputPluginConfig


class OutputPluginKwargs(TypedDict):
    id: Required[int]


class OutputPlugin(Plugin, config_cls=object, register=False):
    """Base class for all output plugins.

    Parameters
    ----------
    id : int
        Numeric plugin identifier

    config : OutputPluginConfig
        Configuration for a plugin

    Raises
    ------
    PluginConfigurationError
        If any error occurs during initializing plugin
    """

    def __init__(
        self,
        *,
        config: OutputPluginConfig,
        **kwargs: Unpack[OutputPluginKwargs]
    ) -> None:
        self._id = kwargs['id']
        self._config = config

    def __str__(self) -> str:
        return f'{self.__class__.__name__}-{self.id}'

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

    @property
    def id(self) -> int:
        """ID of the plugin."""
        return self._id
