import logging
from typing import Any, Callable

import numpy as np
from eventum.plugins.input.base import BaseInputPlugin

from eventum_core.settings import TimeMode

logger = logging.getLogger(__name__)


class UnsupportedTimeModeError(Exception):
    """Exception for for indicating that plugins does not support
    specific time mode.
    """


class InputPluginRunner:
    """Runner for executing input plugin in specified time mode."""

    def __init__(
        self,
        plugin: BaseInputPlugin,
        time_mode: TimeMode,
        name: str = 'unnamed'
    ) -> None:
        self._plugin = plugin
        self._time_mode = time_mode
        self._name = name

        self._task = self._select_mode()

    def _select_mode(self) -> Callable:
        """Get input plugin method that corresponds to specified time
        mode.
        """
        if hasattr(self._plugin, self._time_mode.value):
            return self._plugin.__getattribute__(self._time_mode.value)
        else:
            raise UnsupportedTimeModeError(
                f'"{self._name}" input plugin does not support '
                f'"{self._time_mode}" mode'
            )

    def run(self, on_event: Callable[[np.datetime64], Any],) -> None:
        """Run configured input plugin with specified `on_event`
        callback with blocking execution.
        """
        self._task(on_event=on_event)

    @property
    def name(self) -> str:
        return self._name
