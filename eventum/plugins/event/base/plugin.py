from abc import abstractmethod
from datetime import datetime
from typing import TypedDict, TypeVar

from pydantic import RootModel

from eventum.plugins.base.plugin import Plugin, PluginParams
from eventum.plugins.event.base.config import EventPluginConfig


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


ConfigT = TypeVar(
    'ConfigT',
    bound=(EventPluginConfig | RootModel[EventPluginConfig])
)
ParamsT = TypeVar('ParamsT', bound=EventPluginParams)


class EventPlugin(Plugin[ConfigT, ParamsT], register=False):
    """Base class for all event plugins.

    Parameters
    ----------
    config : ConfigT
        Configuration for the plugin

    params : ParamsT
        Parameters for the plugin (see `EventPluginParams`)

    Raises
    ------
    PluginConfigurationError
        If any error occurs during initializing plugin
    """

    def __init__(self, config: ConfigT, params: ParamsT) -> None:
        super().__init__(config, params)

        self._produced = 0
        self._produce_failed = 0

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
        try:
            result = self._produce(params=params)
        except Exception as e:
            self._produce_failed += 1
            raise e

        self._produced += len(result)
        return result

    @abstractmethod
    def _produce(self, params: ProduceParams) -> list[str]:
        """Produce events with provided parameters.

        Notes
        -----
        See `produce` method for more info
        """
        ...

    @property
    def produced(self) -> int:
        """Number of produced events."""
        return self._produced

    @property
    def produce_failed(self) -> int:
        """Number of unsuccessfully produced events."""
        return self._produce_failed
