import asyncio
from abc import abstractmethod
from typing import Any, Sequence, TypeVar

from pydantic import RootModel

from eventum.plugins.base.plugin import Plugin, PluginParams
from eventum.plugins.exceptions import (PluginConfigurationError,
                                        PluginRuntimeError)
from eventum.plugins.output.base.config import OutputPluginConfig
from eventum.plugins.output.fields import FormatterConfigT
from eventum.plugins.output.formatters import (Formatter, FormattingResult,
                                               get_formatter_class)


class OutputPluginParams(PluginParams):
    """Parameters for output plugin."""


ConfigT = TypeVar(
    'ConfigT',
    bound=(OutputPluginConfig | RootModel[OutputPluginConfig])
)
ParamsT = TypeVar('ParamsT', bound=OutputPluginParams)


class OutputPlugin(Plugin[ConfigT, ParamsT], register=False):
    """Base class for all output plugins.

    Parameters
    ----------
    config : ConfigT
        Configuration for the plugin

    params : ParamsT
        Parameters for the plugin (see `OutputPluginParams`)

    Raises
    ------
    PluginConfigurationError
        If any error occurs during initializing plugin
    """

    def __init__(self, config: ConfigT, params: ParamsT) -> None:
        super().__init__(config, params)

        self._loop: asyncio.AbstractEventLoop

        self._is_opened = False

        self._formatter_config = self._get_formatter_config()
        self._formatter = self._get_formatter(self._formatter_config)

        self._written = 0
        self._format_failed = 0
        self._write_failed = 0

    def _get_formatter_config(self) -> FormatterConfigT:
        """Get formatter config.

        Returns
        -------
        FormatterConfigT
            Formatter config

        Raises
        ------
        PluginConfigurationError
            If config is of invalid type
        """
        if isinstance(self._config, OutputPluginConfig):
            return self._config.formatter
        elif isinstance(self._config, RootModel):
            return self._config.root.formatter
        else:
            raise PluginConfigurationError(
                'Invalid config type',
                context=dict(
                    self.instance_info,
                    plugin_config_class=type(self._config)
                )
            )

    def _get_formatter(self, config: FormatterConfigT) -> Formatter[Any]:
        """Get formatter corresponding to config.

        Parameters
        ----------
        config : FormatterConfigT
            Configuration of formatter

        Returns
        -------
        Formatter[Any]
            Formatter

        Raises
        ------
        PluginConfigurationError
            If formatter configuration fails
        """
        try:
            FormatterCls = get_formatter_class(config.format)
            return FormatterCls(config)
        except ValueError as e:
            raise PluginConfigurationError(
                'Failed to configure formatter',
                context=dict(self.instance_info, reason=str(e))
            )

    async def open(self) -> None:
        """Open plugin for writing.

        Raises
        ------
        PluginRuntimeError
            If error occurs during opening

        Notes
        -----
        Metrics are reset on successful opening
        """
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError as e:
            raise PluginRuntimeError(
                str(e).capitalize(),
                context=dict(self.instance_info)
            )

        if not self._is_opened:
            await self._open()
            self._is_opened = True
            self._written = 0
            self._format_failed = 0
            self._write_failed = 0

        await self._logger.ainfo('Plugin is opened for writing')

    async def close(self) -> None:
        """Close plugin for writing with releasing resources and
        flushing events.
        """
        if self._is_opened:
            await self._close()
            self._is_opened = False

        await self._logger.ainfo('Plugin is closed')

    async def _format_events(self, events: Sequence[str]) -> FormattingResult:
        """Format events.

        Parameters
        ----------
        events : Sequence[str]
            Events to format

        Returns
        -------
        FormattingResult
            Formatting result

        Notes
        -----
        All errors from formatting result are logged
        """

        formatting_result = await self._loop.run_in_executor(
            executor=None,
            func=lambda: self._formatter.format_events(events)
        )

        if formatting_result.errors:
            contexts: list[dict] = []

            for error in formatting_result.errors:
                context = {
                    'format': self._formatter_config.format,
                    'reason': str(error)
                }

                if error.original_event is not None:
                    context['original_event'] = error.original_event

                contexts.append(context)

            await asyncio.gather(
                *[
                    self._logger.aerror('Failed to format event', **context)
                    for context in contexts
                ]
            )

        return formatting_result

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

        Notes
        -----
        Number of successfully written events based on formatted events
        """
        if not events:
            return 0

        if not self._is_opened:
            raise PluginRuntimeError(
                'Output plugin is not opened for writing',
                context=dict(self.instance_info)
            )

        try:
            formatting_result = await self._format_events(events)
        except Exception as e:
            self._format_failed += len(events)
            raise e

        if not formatting_result.events:
            return 0

        try:
            written = await self._write(formatting_result.events)
        except Exception as e:
            self._write_failed += formatting_result.formatted_count
            raise e

        # handle possible events aggregation
        if (
            len(formatting_result.events) == 1
            and formatting_result.formatted_count > 1
            and written == 1
        ):
            written = formatting_result.formatted_count

        self._written += written
        return written

    @abstractmethod
    async def _open(self) -> None:
        """Open plugin for writing.

        Notes
        -----
        See `open` method for more info
        """
        ...

    @abstractmethod
    async def _close(self) -> None:
        """Close plugin for writing with releasing resources and
        flushing events.

        Notes
        -----
        See `close` method for more info
        """
        ...

    @abstractmethod
    async def _write(self, events: Sequence[str]) -> int:
        """Write events.

        Notes
        -----
        See `write` method for more info
        """
        ...

    @property
    def written(self) -> int:
        """Number of written events."""
        return self._written

    @property
    def write_failed(self) -> int:
        """Number of unsuccessfully written events."""
        return self._write_failed

    @property
    def format_failed(self) -> int:
        """Number of unsuccessfully formatted events."""
        return self._format_failed
