import asyncio
from abc import abstractmethod
from typing import Sequence, TypeVar

from pydantic import RootModel

from eventum_plugins.base.plugin import Plugin, PluginParams
from eventum_plugins.exceptions import PluginRuntimeError
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

        self._loop: asyncio.AbstractEventLoop

        self._is_opened = False
        self._lock = asyncio.Lock()

    async def open(self) -> None:
        """Open plugin for writing.

        Raises
        ------
        PluginRuntimeError
            If error occurs during opening
        """
        async with self._lock:
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError as e:
                raise PluginRuntimeError(str(e))

            if not self._is_opened:
                await self._open()
                self._is_opened = True

        await self._logger.ainfo('Plugin is opened for writing')

    async def close(self) -> None:
        """Close plugin for writing with releasing resources and
        flushing events.
        """
        async with self._lock:
            if self._is_opened:
                await self._close()
                self._is_opened = False

        await self._logger.ainfo('Plugin is closed')

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

        Raises
        ------
        PluginRuntimeError
            If error occurs during writing events
        """
        if not events:
            return 0

        async with self._lock:
            if not self._is_opened:
                raise PluginRuntimeError(
                    'Output plugin is not opened for writing'
                )
            return await self._write(events)

    @abstractmethod
    async def _open(self) -> None:
        """Perform actions for plugin opening.

        Raises
        ------
        PluginRuntimeError
            If error occurs during opening
        """
        ...

    @abstractmethod
    async def _close(self) -> None:
        """Perform actions for plugin closing..
        """
        ...

    @abstractmethod
    async def _write(self, events: Sequence[str]) -> int:
        """Perform writing events.

        Parameters
        ----------
        events : Sequence[str]
            Sequence of events to write

        Returns
        -------
        int
            Number of successfully written events

        Raises
        ------
        PluginRuntimeError
            If error occurs during writing events
        """
        ...
