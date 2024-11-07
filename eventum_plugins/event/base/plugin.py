from abc import abstractmethod
from typing import Any

from eventum_plugins.base.plugin import Plugin
from eventum_plugins.event.base.config import EventPluginConfig


class EventPlugin(Plugin, config_cls=object, register=False):
    """Base class for all event plugins."""

    @abstractmethod
    def __init__(
        self,
        *,
        config: EventPluginConfig,
        **kwargs: Any
    ) -> None:
        ...

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
