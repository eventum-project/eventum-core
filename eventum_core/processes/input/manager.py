import logging
import traceback
from concurrent.futures import Future
from enum import IntEnum
from multiprocessing import Process, Queue
from typing import Iterable

import numpy as np
from eventum_core.batcher import Batcher
from eventum_core.plugins_connector import (InputConfigMapping,
                                            PluginNotFoundError,
                                            load_input_plugin_class)
from eventum_core.processes.input.pool_runner import InputPluginPoolRunner
from eventum_core.processes.input.runner import (InputPluginRunner,
                                                 UnsupportedTimeModeError)
from eventum_core.settings import Settings, TimeMode
from eventum_plugins.input.base import (BaseInputPlugin,
                                        InputPluginConfigurationError,
                                        InputPluginRuntimeError)
from numpy.typing import NDArray
from pytz import timezone

logger = logging.getLogger(__name__)


class PluginLoadingError(Exception):
    """Exception for plugin load errors."""


class ExitCode(IntEnum):
    SUCCESS = 0
    FAILED = 1


class InputProcessManager():
    """Manager of input plugins process."""

    def __init__(
        self,
        config: Iterable[InputConfigMapping],   # type: ignore[valid-type]
        settings: Settings,
        time_mode: TimeMode,
        downstream_queue: Queue[NDArray]
    ) -> None:
        self._config = list(config)
        self._settings = settings
        self._time_mode = time_mode
        self._queue = downstream_queue

        self._process = Process(target=self._start_process)

    def start(self) -> None:
        """Start input process"""
        self._process.start()

    def get_plugin_names(self) -> list[str]:
        """Get plugin names in order specified in config."""
        return [
            item.get_name()             # type: ignore[attr-defined]
            for item in self._config
        ]

    def get_plugin_name_by_id(self, id: int) -> str:
        """Get plugin name by specified id."""
        return self.get_plugin_names()[id]

    def _load_plugins(self) -> list[BaseInputPlugin]:
        """Load configured input plugins specified in config. If any
        error is occurred, then `PluginLoadingError` is raised.
        """
        plugins: list[BaseInputPlugin] = []

        for item in self._config:
            plugin_name = item.get_name()       # type: ignore[attr-defined]
            plugin_config = item.get_value()    # type: ignore[attr-defined]

            try:
                Plugin = load_input_plugin_class(plugin_name)
                plugins.append(
                    Plugin(
                        config=plugin_config,
                        tz=timezone(self._settings.timezone)
                    )
                )
            except PluginNotFoundError as e:
                raise PluginLoadingError(
                    f'Failed to load "{plugin_name}" input plugin: {e}'
                ) from None
            except InputPluginConfigurationError as e:
                raise PluginLoadingError(
                    f'Failed to initialize "{plugin_name}" input plugin: {e}'
                ) from None
            except Exception:
                raise PluginLoadingError(
                    'Unexpected error occurred during initializing '
                    f'"{plugin_name}" input plugin:\n{traceback.format_exc()}'
                ) from None

        return plugins

    def _handle_plugin_result(self, plugin_id: int, future: Future) -> None:
        """Handle result of input plugin execution."""
        plugin_name = self.get_plugin_name_by_id(plugin_id)
        try:
            future.result()
            logger.info(f'Input plugin "{plugin_name}" has ended successfully')
        except InputPluginRuntimeError as e:
            logger.error(
                f'Error occurred during "{plugin_name}" input plugin '
                f'execution: {e}'
            )
        except Exception:
            logger.error(
                f'Unexpected error occurred during "{plugin_name}" '
                f'input plugin execution:\n{traceback.format_exc()}'
            )

    def _start_process(self) -> int:
        """Start process with input plugins execution."""
        plugin_names_fmt = ", ".join(self.get_plugin_names())

        logger.info(f'Loading [{plugin_names_fmt}] input plugins')
        try:
            plugins = self._load_plugins()
        except PluginLoadingError as e:
            logger.error(f'Failed to load input plugins: {e}')
            return ExitCode.FAILED.value

        logger.info('Input plugins are successfully loaded')

        logger.info(f'Creating execution pool of {len(plugins)} input plugins')
        plugin_runners: list[InputPluginRunner] = []
        try:
            for plugin_name, plugin in zip(self.get_plugin_names(), plugins):
                plugin_runners.append(
                    InputPluginRunner(
                        plugin=plugin,
                        time_mode=self._time_mode,
                        name=plugin_name
                    )
                )
        except UnsupportedTimeModeError as e:
            logger.error(f'Failed to create input plugins execution pool: {e}')
            return ExitCode.FAILED.value

        plugins_pool_runner = InputPluginPoolRunner(plugin_runners)

        logger.info('Running input plugins pool')
        with Batcher(
            size=self._settings.events_batch_size,
            timeout=self._settings.events_batch_timeout,
            callback=lambda batch: self._queue.put(
                np.array(
                    batch,
                    dtype=[('timestamp', 'datetime64[us]'), ('input_id', 'i8')]
                )
            )
        ) as batcher:
            plugins_pool_runner.run(
                on_event=(
                    lambda timestamp, plugin_id:
                    batcher.add((timestamp, plugin_id))
                ),
                on_done=self._handle_plugin_result
            )

        logger.info('Input plugins pool has finished')
        return ExitCode.SUCCESS.value
