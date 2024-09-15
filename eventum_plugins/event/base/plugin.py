from abc import abstractmethod
from typing import Any, Literal, TypeAlias

from nptyping import NDArray

from eventum_plugins.base.plugin import Plugin

TimestampsBatch: TypeAlias = NDArray[
    Any,
    Literal['timestamp: Datetime64, plugin_id: Int']
]


class BaseEventPlugin(Plugin, config_cls=object, base=True):
    """Base class for all event plugins."""

    @abstractmethod
    def produce(self, timestamps: TimestampsBatch) -> list[str]:
        """Produce events for provided timestamps.

        Parameters
        ----------
        timestamps : TimestampsBatch
            Batch of timestamps

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
