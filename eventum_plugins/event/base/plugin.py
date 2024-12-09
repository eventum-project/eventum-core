from abc import abstractmethod
from datetime import datetime
from typing import Any, TypedDict, TypeVar

from pydantic import RootModel

from eventum_plugins.base.plugin import Plugin, PluginParams
from eventum_plugins.event.base.config import EventPluginConfig


class ProduceParams(TypedDict):
    """Params for `produce` method of `EventPlugin`.

    Attributes
    ----------
    timestamp : str
        Timestamp of event

    tags : tuple[str, ...]
        Tags from input plugin that generated timestamp

    """
    timestamp: datetime
    tags: tuple[str, ...]


class EventPluginParams(PluginParams):
    """Parameters for event plugin."""


config_T = TypeVar('config_T', bound=(EventPluginConfig | RootModel[Any]))
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
    def produce(self, params: ProduceParams) -> list[str]:
        """Produce events with provided parameters.

        Parameters
        ----------
        params : ProduceParams
            Parameters for events producing

        Returns
        -------
        list[str]
           Produced events

        Raises
        ------
        PluginRuntimeError
            If any error occurs during producing events

        EventsExhausted
            If no more events can be produced by event plugin
        """
        ...
