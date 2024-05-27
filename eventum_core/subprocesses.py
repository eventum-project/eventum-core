import asyncio
import logging
import signal
from datetime import datetime
from multiprocessing import Queue
from multiprocessing.sharedctypes import SynchronizedBase
from multiprocessing.synchronize import Event as EventClass
from typing import Callable, NoReturn, Optional

import numpy as np
from eventum_plugins.event.base import (EventPluginConfigurationError,
                                        EventPluginRuntimeError)
from eventum_plugins.event.jinja import JinjaEventConfig, JinjaEventPlugin
from eventum_plugins.input.base import (InputPluginConfigurationError,
                                        InputPluginRuntimeError)
from eventum_plugins.output.base import (BaseOutputPlugin,
                                         OutputPluginConfigurationError,
                                         OutputPluginRuntimeError)
from jinja2 import BaseLoader
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

            signal.signal(signal.SIGINT, lambda signal, stack_frame: exit(0))

            result = f(*args, **kwargs)
            return result

        return wrapper
    return decorator


def _terminate_subprocess(
    is_done: EventClass,
    exit_code: int = 0,
    signal_queue: Optional[Queue] = None
) -> NoReturn:
    """Handle termination of subprocess."""
    if signal_queue is not None:
        signal_queue.put(None)
    is_done.set()
    exit(exit_code)


@subprocess('input')
def start_input_subprocess(
    config: MutexFieldsModel,
    settings: Settings,
    time_mode: TimeMode,
    queue: Queue,
    is_done: EventClass,
) -> None:
    plugin_name = config.get_name()
    input_conf = config.get_value()

    logger.info(f'Initializing "{plugin_name}" input plugin')

    try:
        plugin_class = load_input_plugin_class(plugin_name=plugin_name)
        input_plugin = plugin_class(
            config=input_conf,
            tz=timezone(settings.timezone)
        )
    except ValueError as e:
        logger.error(f'Failed to load input plugin: {e}')
        _terminate_subprocess(is_done, 1, queue)
    except InputPluginConfigurationError as e:
        logger.error(f'Failed to initialize input plugin: {e}')
        _terminate_subprocess(is_done, 1, queue)
    except Exception as e:
        logger.error(
            'Unexpected error occurred during initializing '
            f'input plugin: {e}'
        )
        _terminate_subprocess(is_done, 1, queue)

    logger.info('Input plugin is successfully initialized')

    try:
        with Batcher(
            size=settings.events_batch_size,
            timeout=settings.events_batch_timeout,
            callback=queue.put
        ) as batcher:
            plugin_mode = input_plugin.__getattribute__(time_mode.value)
            plugin_mode.__call__(on_event=batcher.add)
    except AttributeError:
        logger.error(
            f'"{plugin_name}" input plugin does not support "{time_mode}" mode'
        )
        _terminate_subprocess(is_done, 1, queue)
    except InputPluginRuntimeError as e:
        logger.error(f'Error occurred during input plugin execution: {e}')
        _terminate_subprocess(is_done, 1, queue)
    except Exception as e:
        logger.error(
            f'Unexpected error occurred during input plugin execution: {e}'
        )
        _terminate_subprocess(is_done, 1, queue)

    logger.info('Stopping input plugin')
    _terminate_subprocess(is_done, 0, queue)


@subprocess('event')
def start_event_subprocess(
    config: JinjaEventConfig,
    loader: BaseLoader | None,
    settings: Settings,
    input_queue: Queue,
    event_queue: Queue,
    is_done: EventClass
) -> None:
    logger.info('Initializing "jinja" event plugin')

    try:
        event_plugin = JinjaEventPlugin(config=config, loader=loader)
    except EventPluginConfigurationError as e:
        logger.error(f'Failed to initialize event plugin: {e}')
        _terminate_subprocess(is_done, 1, event_queue)
    except Exception as e:
        logger.error(
            f'Unexpected error occurred during initializing '
            f'event plugin: {e}'
        )
        _terminate_subprocess(is_done, 1, event_queue)

    logger.info('Event plugin is successfully initialized')

    timezone_as_string = datetime.now(
        tz=timezone(settings.timezone)
    ).strftime('%z')

    with Batcher(
        size=settings.output_batch_size,
        timeout=settings.output_batch_timeout,
        callback=event_queue.put
    ) as batcher:
        while True:
            timestamps_batch = input_queue.get()
            if timestamps_batch is None:
                break

            try:
                for timestamp in timestamps_batch:
                    for event in event_plugin.render(
                        **{
                            settings.timestamp_field_name: timestamp,
                            settings.timezone_field_name: timezone_as_string
                        }
                    ):
                        batcher.add(event)
            except EventPluginRuntimeError as e:
                logger.error(f'Failed to produce event: {e}')
                _terminate_subprocess(is_done, 1, event_queue)
            except Exception as e:
                logger.error(
                    f'Unexpected error occurred during producing event: {e}'
                )
                _terminate_subprocess(is_done, 1, event_queue)

    logger.info('Stopping event plugin')
    _terminate_subprocess(is_done, 0, event_queue)


@subprocess('output')
def start_output_subprocess(
    config: list[MutexFieldsModel],
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
            logger.error(f'Failed to load output plugin: {e}')
            _terminate_subprocess(is_done, 1)
        except OutputPluginConfigurationError as e:
            logger.error(
                f'Failed to initialize "{plugin_name}" output plugin: {e}'
            )
            _terminate_subprocess(is_done, 1)
        except Exception as e:
            logger.error(
                'Unexpected error occurred during initializing '
                f'"{plugin_name}" output plugin: {e}'
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
