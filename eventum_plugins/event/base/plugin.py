from abc import abstractmethod
from typing import Any, Unpack

from eventum_plugins.base.plugin import Plugin, PluginKwargs
from eventum_plugins.event.base.config import EventPluginConfig


class EventPluginKwargs(PluginKwargs):
    """Arguments for event plugin configuration."""


class EventPlugin(Plugin, config_cls=object, register=False):
    """Base class for all event plugins.

    Parameters
    ----------
    **kwargs : Unpack[EventPluginKwargs]
        Arguments for plugin configuration (see `EventPluginKwargs`)

    Raises
    ------
    PluginConfigurationError
        If any error occurs during initializing plugin
    """

    def __init__(self, **kwargs: Unpack[EventPluginKwargs]) -> None:
        super().__init__(**kwargs)
        self._config: EventPluginConfig

    @abstractmethod
    def produce(self, params: Any) -> Any:
        """Produce events with provided parameters.

        Parameters
        ----------
        params : Any
            Parameters for events producing

        Returns
        -------
        Any
           Produced events

        Raises
        ------
        PluginRuntimeError
            If any error occurs during producing events
        """
        ...
