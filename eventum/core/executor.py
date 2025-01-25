import asyncio
from datetime import datetime
from queue import Queue
from typing import Any, Sequence

import structlog
import uvloop
from pytz import timezone

from eventum.core.models.parameters.generator import GeneratorParameters
from eventum.plugins.event.base.plugin import EventPlugin, ProduceParams
from eventum.plugins.exceptions import PluginRuntimeError
from eventum.plugins.input.adapters import IdentifiedTimestampsPluginAdapter
from eventum.plugins.input.base.plugin import InputPlugin
from eventum.plugins.input.batcher import TimestampsBatcher
from eventum.plugins.input.merger import InputPluginsMerger
from eventum.plugins.input.protocols import (
    IdentifiedTimestamps, SupportsIdentifiedTimestampsIterate,
    SupportsIdentifiedTimestampsSizedIterate)
from eventum.plugins.input.scheduler import BatchScheduler
from eventum.plugins.output.base.plugin import OutputPlugin

logger = structlog.stdlib.get_logger()


class ImproperlyConfiguredError(Exception):
    """Plugins cannot be executed with provided parameters."""

    def __init__(self, *args: object, context: dict[str, Any]) -> None:
        super().__init__(*args)

        self.context = context


class ExecutionError(Exception):
    """Execution error."""

    def __init__(self, *args: object, context: dict[str, Any]) -> None:
        super().__init__(*args)

        self.context = context


class Executor:
    """Executor of plugins.

    Parameters
    ----------
    input : Sequence[InputPlugin]
        List of input plugins

    event: EventPlugin
        Event plugin

    output: Sequence[OutputPlugin]
        List of output plugins

    params: GeneratorParameters
        Generator parameters

    Raises
    ------
    ImproperlyConfiguredError
        If initialization failed with provided plugins and parameters

    Notes
    -----
    It is expected that all of the parameters are already validated
    """

    def __init__(
        self,
        input: Sequence[InputPlugin],
        event: EventPlugin,
        output: Sequence[OutputPlugin],
        params: GeneratorParameters
    ) -> None:
        self._input = list(input)
        self._event = event
        self._output = list(output)
        self._params = params

        self._input_queue: Queue[IdentifiedTimestamps | None] = Queue(
            maxsize=params.queue.max_batches
        )
        self._event_queue: Queue[list[str] | None] = Queue(
            maxsize=params.queue.max_batches
        )

        self._configured_input = self._configure_input()
        self._input_tags = self._build_input_tags_map()
        self._timezone = timezone(self._params.timezone)

    def _build_input_tags_map(self) -> dict[int, tuple[str, ...]]:
        """Build map of input plugin tags.

        Returns
        -------
        dict[int, tuple[str, ...]]
            Tags map with input plugin id in keys and tags tuple in values
        """
        tags_map: dict[int, tuple[str, ...]] = dict()
        for plugin in self._input:
            tags_map[plugin.id] = plugin.config.tags

        return tags_map

    def _configure_input(self) -> SupportsIdentifiedTimestampsIterate:
        """Configure input plugins according to generating parameters
        by wrapping it to merger, batcher and scheduler.

        Returns
        -------
        SupportsIdentifiedTimestampsIterate
            Configured input

        Raises
        ------
        ImproperlyConfiguredError
            If input plugins cannot be configured
        """
        if len(self._input) > 1:
            try:
                input_plugin: SupportsIdentifiedTimestampsSizedIterate \
                    = InputPluginsMerger(plugins=self._input)
            except ValueError as e:
                raise ImproperlyConfiguredError(
                    'Failed to merge input plugins',
                    context=dict(reason=str(e))
                )
        else:
            input_plugin = IdentifiedTimestampsPluginAdapter(
                plugin=self._input[0]
            )

        try:
            batcher = TimestampsBatcher(
                source=input_plugin,
                batch_size=self._params.batch.size,
                batch_delay=self._params.batch.delay
            )
        except ValueError as e:
            raise ImproperlyConfiguredError(
                'Failed to initialize batcher',
                context=dict(reason=str(e))
            )

        if self._params.time_mode == 'live':
            return BatchScheduler(
                batcher=batcher,
                timezone=self._timezone
            )
        else:
            return batcher

    async def _open_output_plugins(self) -> None:
        """Open output plugins.

        Raises
        ------
        ExecutionError
            If opening for at least one output plugin fails
        """
        try:
            async with asyncio.TaskGroup() as group:
                for plugin in self._output:
                    group.create_task(plugin.open())
        except* PluginRuntimeError as e:
            exc: PluginRuntimeError = e.exceptions[0]   # type: ignore
            raise ExecutionError(str(exc), **exc.context)

    async def _execute(self) -> None:
        """Start execution of plugins in different threads.

        Raises
        ------
        ExecutionError
            If any error occurs during execution
        """
        loop = asyncio.get_running_loop()

        await self._open_output_plugins()

        input_task = loop.run_in_executor(None, self._execute_input)
        event_task = loop.run_in_executor(None, self._execute_event)
        output_task = loop.create_task(self._execute_output())

        await input_task
        await event_task
        await output_task

    def execute(self) -> None:
        """Start execution of plugins.

        Raises
        ------
        ExecutionError
            If any error occurs during execution
        """
        with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
            runner.run(self._execute())

    def _execute_input(self) -> None:
        """Execute input plugins."""
        skip_past = self._params.time_mode == 'live' and self._params.skip_past

        try:
            for timestamps in self._configured_input.iterate(
                skip_past=skip_past
            ):
                self._input_queue.put(timestamps)

            self._input_queue.put(None)
        except PluginRuntimeError as e:
            logger.error(str(e), **e.context)
            self._input_queue.put(None)
        except Exception as e:
            logger.exception(
                'Unexpected error during input plugins execution',
                reason=str(e)
            )
            self._input_queue.put(None)

    def _execute_event(self) -> None:
        """Execute event plugin."""
        while True:
            timestamps = self._input_queue.get()

            if timestamps is None:
                break

            dt_timestamps = timestamps['timestamp'].astype(dtype=datetime)
            params: ProduceParams = ProduceParams(
                tags=tuple(),
                timestamp=datetime.now()
            )
            events: list[str] = []
            for id, timestamp in zip(timestamps['id'], dt_timestamps):
                params['tags'] = self._input_tags[id]
                params['timestamp'] = self._timezone.localize(timestamp)

                try:
                    events.extend(self._event.produce(params=params))
                except PluginRuntimeError as e:
                    logger.error(str(e), **e.context)
                except Exception as e:
                    logger.exception(
                        'Unexpected error during event plugin execution',
                        reason=str(e)
                    )

            if events:
                self._event_queue.put(events)

        self._event_queue.put(None)

    def _handle_write_result(self, future: asyncio.Future[int]) -> None:
        """Handle result of output plugin write task.

        Parameters
        ----------
        future : asyncio.Future
            Done future
        """
        try:
            future.result()
        except PluginRuntimeError as e:
            logger.error(str(e), **e.context)
        except Exception as e:
            logger.exception(
                'Unexpected error occurred during output plugins execution',
                reason=str(e)
            )

    async def _execute_output(self) -> None:
        """Execute output plugins."""
        loop = asyncio.get_running_loop()

        while True:
            events = await loop.run_in_executor(
                executor=None,
                func=self._event_queue.get
            )

            if events is None:
                break

            tasks: list[asyncio.Task] = []
            for plugin in self._output:
                task = loop.create_task(plugin.write(events))
                task.add_done_callback(self._handle_write_result)
                tasks.append(task)

            if self._params.keep_order:
                await asyncio.gather(*tasks)
