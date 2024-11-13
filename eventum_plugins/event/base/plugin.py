from abc import abstractmethod
from typing import Any, TypeVar

from pydantic import RootModel

from eventum_plugins.base.plugin import Plugin, PluginParams
from eventum_plugins.event.base.config import EventPluginConfig


class EventPluginParams(PluginParams):
    """Parameters for event plugin."""


config_T = TypeVar('config_T', bound=(EventPluginConfig | RootModel))
params_T = TypeVar('params_T', bound=EventPluginParams)


class EventPlugin(Plugin[config_T, params_T], register=False):
    """Base class for all event plugins.

    Parameters
    ----------
    config : config_T
        Configuration for the plugin

    params : params_T
        Parameters for the plugin (see `EventPluginParams`)

    Raises
    ------
    PluginConfigurationError
        If any error occurs during initializing plugin
    """

    def __init__(self, config: config_T, params: params_T) -> None:
        super().__init__(config, params)

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
