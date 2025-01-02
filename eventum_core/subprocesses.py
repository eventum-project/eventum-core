import asyncio
import logging
import signal
import time
import traceback
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime
from multiprocessing import Queue
from multiprocessing.sharedctypes import SynchronizedBase
from multiprocessing.synchronize import Event as EventClass
from typing import Callable, Iterable, NoReturn, Optional

import numpy as np
from eventum_plugins.event.base import (EventPluginConfigurationError,
                                        EventPluginRuntimeError)
from eventum_plugins.event.jinja import JinjaEventConfig, JinjaEventPlugin
from eventum_plugins.input.base import (BaseInputPlugin,
                                        InputPluginConfigurationError,
                                        InputPluginRuntimeError)
from eventum_plugins.output.base import (BaseOutputPlugin,
                                         OutputPluginConfigurationError,
                                         OutputPluginRuntimeError)
from numpy.typing import NDArray
from pytz import timezone
from setproctitle import getproctitle, setproctitle

from eventum_core.batcher import Batcher
from eventum_core.plugins_connector import (MutexFieldsModel,
                                            load_input_plugin_class,
                                            load_output_plugin_class)
from eventum_core.settings import Settings, TimeMode

logger = logging.getLogger(__name__)


def subprocess(name: str) -> Callable:
    """Parametrized decorator for all subprocesses."""

    def decorator(f: Callable):
        def wrapper(*args, **kwargs):
            setproctitle(f'{getproctitle()} [{name}]')

            signal.signal(signal.SIGINT, lambda signal, stack_frame: exit(1))

            result = f(*args, **kwargs)
            return result

        return wrapper
    return decorator


def _terminate_subprocess(
    is_done: EventClass,
    exit_code: int = 0,
    downstream_queue: Optional[Queue] = None
) -> NoReturn:
    """Handle termination of subprocess."""
    if downstream_queue is not None:
        time.sleep(0.1)
        downstream_queue.put(None)
    is_done.set()
    exit(exit_code)


@subprocess('input')
def start_input_subprocess(
    config: Iterable[MutexFieldsModel],
    settings: Settings,
    time_mode: TimeMode,
    queue: Queue,
    is_done: EventClass,
) -> None:
    plugins_list_fmt = ", ".join(
        [f'"{item.get_name()}"' for item in config]
    )

    logger.info(f'Initializing [{plugins_list_fmt}] input plugins')

    input_plugins: list[BaseInputPlugin] = []
    input_plugin_names: list[str] = []

    for item in config:
        plugin_name = item.get_name()
        input_conf = item.get_value()

        try:
            plugin_class = load_input_plugin_class(plugin_name=plugin_name)
            input_plugins.append(
                plugin_class(
                    config=input_conf,
                    tz=timezone(settings.timezone)
                )
            )
            input_plugin_names.append(plugin_name)
        except ValueError as e:
            logger.error(f'Failed to load "{plugin_name}" input plugin: {e}')
            _terminate_subprocess(is_done, 1, queue)
        except InputPluginConfigurationError as e:
            logger.error(
                f'Failed to initialize "{plugin_name}" input plugin: {e}'
            )
            _terminate_subprocess(is_done, 1, queue)
        except Exception:
            logger.error(
                'Unexpected error occurred during initializing '
                f'"{plugin_name}" input plugin:\n{traceback.format_exc()}'
            )
            _terminate_subprocess(is_done, 1, queue)

    logger.info('Input plugins are successfully initialized')

    plugin_tasks: list[Callable] = []
    for plugin_name, plugin in zip(input_plugin_names, input_plugins):
        if hasattr(plugin, time_mode.value):
            plugin_tasks.append(plugin.__getattribute__(time_mode.value))
        else:
            logger.error(
                f'"{plugin_name}" input plugin does not support '
                f'"{time_mode}" mode'
            )
            _terminate_subprocess(is_done, 1, queue)

    with ThreadPoolExecutor(max_workers=len(plugin_tasks)) as executor:
        with Batcher(
            size=settings.events_batch_size,
            timeout=settings.events_batch_timeout,
            callback=lambda batch: queue.put(
                np.array(
                    batch,
                    dtype=[('timestamp', 'datetime64[us]'), ('input_id', 'i8')]
                )
            )
        ) as batcher:
            submitted_tasks: list[Future] = []
            for plugin_id, plugin_task in enumerate(plugin_tasks):
                submitted_tasks.append(
                    executor.submit(
                        plugin_task,
                        on_event=(
                            lambda timestamp, plugin_id=plugin_id:
                            batcher.add((timestamp, plugin_id))
                        )
                    )
                )

            all_success = True
            for plugin_name, plugin_task in zip(    # type: ignore[assignment]
                input_plugin_names,
                submitted_tasks
            ):
                try:
                    plugin_task.result()   # type: ignore[attr-defined]
                except InputPluginRuntimeError as e:
                    logger.error(
                        f'Error occurred during "{plugin_name}" input plugin '
                        f'execution: {e}'
                    )
                    all_success = False
                except Exception:
                    logger.error(
                        f'Unexpected error occurred during "{plugin_name}" '
                        f'input plugin execution:\n{traceback.format_exc()}'
                    )
                    all_success = False

            if all_success:
                logger.info('Stopping input plugins')
                _terminate_subprocess(is_done, 0, queue)
            else:
                _terminate_subprocess(is_done, 1, queue)


@subprocess('event')
def start_event_subprocess(
    config: JinjaEventConfig,
    input_tags: dict[int, tuple[str, ...]],
    settings: Settings,
    input_queue: Queue,
    event_queue: Queue,
    is_done: EventClass
) -> None:
    logger.info('Initializing "jinja" event plugin')

    try:
        event_plugin = JinjaEventPlugin(config=config)
    except EventPluginConfigurationError as e:
        logger.error(f'Failed to initialize event plugin: {e}')
        _terminate_subprocess(is_done, 1, event_queue)
    except Exception:
        logger.error(
            f'Unexpected error occurred during initializing '
            f'event plugin:\n{traceback.format_exc()}'
        )
        _terminate_subprocess(is_done, 1, event_queue)

    logger.info('Event plugin is successfully initialized')

    timezone_as_string = datetime.now(
        tz=timezone(settings.timezone)
    ).strftime('%z')

    with Batcher(
        size=settings.output_batch_size,
        timeout=settings.output_batch_timeout,
        callback=lambda batch: event_queue.put(batch)
    ) as batcher:
        while True:
            batch = input_queue.get()
            if batch is None:
                break

            try:
                for timestamp, input_id in batch:
                    for event in event_plugin.render(
                        **{
                            settings.timestamp_field_name: str(timestamp),
                            settings.timezone_field_name: timezone_as_string,
                            settings.tags_field_name: input_tags[input_id]
                        }
                    ):
                        batcher.add(event)
            except EventPluginRuntimeError:
                logger.error(
                    f'Failed to produce event:\n'
                    f'{traceback.format_exc()}'
                )
                _terminate_subprocess(is_done, 1, event_queue)
            except Exception:
                logger.error(
                    f'Unexpected error occurred during producing event:\n'
                    f'{traceback.format_exc()}'
                )
                _terminate_subprocess(is_done, 1, event_queue)

    logger.info('Stopping event plugin')
    _terminate_subprocess(is_done, 0, event_queue)


@subprocess('output')
def start_output_subprocess(
    config: Iterable[MutexFieldsModel],
    settings: Settings,
    queue: Queue,
    processed_events: SynchronizedBase,
    is_done: EventClass
) -> None:
    plugins_list_fmt = ", ".join(
        [f'"{item.get_name()}"' for item in config]
    )

    logger.info(f'Initializing [{plugins_list_fmt}] output plugins')

    output_plugins: list[BaseOutputPlugin] = []

    for item in config:
        plugin_name = item.get_name()
        output_conf = item.get_value()

        try:
            plugin_class = load_output_plugin_class(plugin_name=plugin_name)
            output_plugins.append(plugin_class(config=output_conf))
        except ValueError as e:
            logger.error(f'Failed to load "{plugin_name}" output plugin: {e}')
            _terminate_subprocess(is_done, 1)
        except OutputPluginConfigurationError as e:
            logger.error(
                f'Failed to initialize "{plugin_name}" output plugin: {e}'
            )
            _terminate_subprocess(is_done, 1)
        except Exception:
            logger.error(
                'Unexpected error occurred during initializing '
                f'"{plugin_name}" output plugin:\n{traceback.format_exc()}'
            )
            _terminate_subprocess(is_done, 1)

    logger.info('Output plugins are successfully initialized')

    async def write_batch(
        plugin: BaseOutputPlugin,
        events_batch: NDArray[np.str_]
    ) -> None:
        batch_size = len(events_batch)
        try:
            if batch_size == 1:
                await plugin.write(events_batch[0])
            elif batch_size > 1:
                await plugin.write_many(events_batch)
        except OutputPluginRuntimeError as e:
            logger.error(f'Output plugin failed to write events: {e}')
            return
        except Exception:
            logger.error(
                f'Unexpected error occurred during '
                f'output plugin execution:\n{traceback.format_exc()}'
            )

    async def run_loop() -> None:
        await asyncio.gather(
            *[plugin.open() for plugin in output_plugins]
        )

        while True:
            events_batch = queue.get()

            if events_batch is None:
                break

            await asyncio.gather(
                *[
                    write_batch(plugin, events_batch)
                    for plugin in output_plugins
                ]
            )

            processed_events.value += len(      # type: ignore[attr-defined]
                events_batch
            )

        await asyncio.gather(
            *[plugin.close() for plugin in output_plugins]
        )

    asyncio.run(run_loop())

    logger.info('Stopping output plugins')
    _terminate_subprocess(is_done, 0)
