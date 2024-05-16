import asyncio
import importlib
import logging
import signal
from multiprocessing import Queue
from multiprocessing.sharedctypes import SynchronizedBase
from multiprocessing.synchronize import Event as EventClass
from typing import Callable, NoReturn, Optional, assert_never

import numpy as np
from numpy.typing import NDArray
from setproctitle import getproctitle, setproctitle

import eventum.logging_config
from eventum.core import settings
from eventum.core.batcher import Batcher
from eventum.core.models.event_config import EventConfig
from eventum.core.models.input_config import InputConfigMapping
from eventum.core.models.output_config import OutputConfigMapping
from eventum.core.models.time_mode import TimeMode
from eventum.core.plugins.event.base import (BaseEventPlugin,
                                             EventPluginConfigurationError,
                                             EventPluginRuntimeError)
from eventum.core.plugins.input.base import (BaseInputPlugin,
                                             InputPluginConfigurationError,
                                             InputPluginRuntimeError)
from eventum.core.plugins.output.base import (BaseOutputPlugin,
                                              OutputPluginConfigurationError,
                                              OutputPluginRuntimeError)

eventum.logging_config.apply()
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
    config: InputConfigMapping,
    time_mode: TimeMode,
    queue: Queue,
    is_done: EventClass,
) -> None:
    plugin_name = config.get_name()
    input_conf = config.get_value()

    logger.info(f'Initializing "{plugin_name}" input plugin')

    try:
        plugin_module = importlib.import_module(
            f'eventum.core.plugins.input.{plugin_name}'
        )
        input_plugin_class = plugin_module.load_plugin()        # type: ignore
        input_plugin: BaseInputPlugin = (
            input_plugin_class.create_from_config(              # type: ignore
                config=input_conf
            )
        )
    except ModuleNotFoundError as e:
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
            size=settings.EVENTS_BATCH_SIZE,
            timeout=settings.EVENTS_BATCH_TIMEOUT,
            callback=queue.put
        ) as batcher:
            match time_mode:
                case TimeMode.LIVE:
                    input_plugin.live(on_event=batcher.add)     # type: ignore
                case TimeMode.SAMPLE:
                    input_plugin.sample(on_event=batcher.add)   # type: ignore
                case _:
                    assert_never(time_mode)
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
    config: EventConfig,
    input_queue: Queue,
    event_queue: Queue,
    is_done: EventClass
) -> None:
    plugin_name = 'jinja'

    logger.info(f'Initializing "{plugin_name}" event plugin')

    try:
        plugin_module = importlib.import_module(
            f'eventum.core.plugins.event.{plugin_name}'
        )
        event_plugin_class = plugin_module.load_plugin()    # type: ignore
        event_plugin: BaseEventPlugin = (
            event_plugin_class.create_from_config(          # type: ignore
                config=config
            )
        )
    except ModuleNotFoundError as e:
        logger.error(f'Failed to load event plugin: {e}')
        _terminate_subprocess(is_done, 1, event_queue)
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

    with Batcher(
        size=settings.OUTPUT_BATCH_SIZE,
        timeout=settings.OUTPUT_BATCH_TIMEOUT,
        callback=event_queue.put
    ) as batcher:
        while True:
            timestamps_batch = input_queue.get()
            if timestamps_batch is None:
                break

            try:
                for timestamp in timestamps_batch:
                    for event in event_plugin.render(timestamp=timestamp):
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
    config: list[OutputConfigMapping],
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
            plugin_module = importlib.import_module(
                f'eventum.core.plugins.output.{plugin_name}'
            )
            output_plugin_class = plugin_module.load_plugin()   # type: ignore
            output_plugin: BaseOutputPlugin = (
                output_plugin_class.create_from_config(         # type: ignore
                    config=output_conf
                )
            )
            output_plugins.append(output_plugin)
        except ModuleNotFoundError as e:
            logger.error(f'Failed to load input plugin: {e}')
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
                count = await plugin.write(events_batch[0])
            elif batch_size > 1:
                count = await plugin.write_many(events_batch)
        except OutputPluginRuntimeError as e:
            logger.error(f'Output plugin failed to write events: {e}')
            return

        if count < batch_size:
            logger.warning(
                f'Only {count} events were written by output plugin from '
                f' batch with size {batch_size}'
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

            processed_events.value += len(events_batch)  # type: ignore

        await asyncio.gather(
            *[plugin.close() for plugin in output_plugins]
        )

    asyncio.run(run_loop())

    logger.info('Stopping output plugins')
    _terminate_subprocess(is_done, 0)
