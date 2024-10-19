from abc import abstractmethod

from eventum_plugins.base.plugin import Plugin


class BaseEventPlugin(Plugin, config_cls=object, register=False):
    """Base class for all event plugins."""

    @abstractmethod
    def produce(self, **kwargs) -> list[str]:
        """Produce events with provided parameters.

        Returns
        -------
        list[str]
            List of produced events

        Raises
        ------
        PluginRuntimeError
            If any error occurs during producing events
        """
        ...
