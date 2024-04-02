import asyncio
import logging
import signal
from concurrent.futures import ThreadPoolExecutor
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
from eventum.core.models.application_config import (InputConfigMapping,
                                                    InputType,
                                                    JinjaEventConfig,
                                                    OutputConfigMapping,
                                                    OutputType)
from eventum.core.models.time_mode import TimeMode
from eventum.core.plugins.event.base import (EventPluginConfigurationError,
                                             EventPluginRuntimeError)
from eventum.core.plugins.event.jinja import JinjaEventPlugin
from eventum.core.plugins.input.base import (InputPluginConfigurationError,
                                             InputPluginRuntimeError)
from eventum.core.plugins.input.cron import CronInputPlugin
from eventum.core.plugins.input.sample import SampleInputPlugin
from eventum.core.plugins.input.time_pattern import TimePatternPoolInputPlugin
from eventum.core.plugins.input.timestamps import TimestampsInputPlugin
from eventum.core.plugins.output.base import (BaseOutputPlugin,
                                              OutputPluginConfigurationError,
                                              OutputPluginRuntimeError)
from eventum.core.plugins.output.file import FileOutputPlugin
from eventum.core.plugins.output.stdout import StdoutOutputPlugin
from eventum.repository.manage import ContentReadError, load_time_pattern

eventum.logging_config.apply()
logger = logging.getLogger(__name__)


def subprocess(module_name: str) -> Callable:
    """Parametrized decorator for all subprocesses."""

    def decorator(f: Callable):
        def wrapper(*args, **kwargs):
            setproctitle(f'{getproctitle()} [{module_name}]')

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
    input_type, input_conf = config.popitem()

    logger.info(f'Initializing "{input_type}" input plugin')

    try:
        match input_type:
            case InputType.PATTERNS:
                input_plugin = TimePatternPoolInputPlugin(
                    [
                        load_time_pattern(path)         # type: ignore
                        for path in input_conf
                    ]
                )
            case InputType.TIMESTAMPS:
                input_plugin = TimestampsInputPlugin(
                    timestamps=input_conf               # type: ignore
                )
            case InputType.CRON:
                input_plugin = CronInputPlugin(
                    expression=input_conf.expression,   # type: ignore
                    count=input_conf.count              # type: ignore
                )
            case InputType.SAMPLE:
                input_plugin = SampleInputPlugin(
                    count=input_conf.count              # type: ignore
                )
            case value:
                assert_never(value)
    except ContentReadError as e:
        logger.error(f'Failed to load content for input plugin: {e}')
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
                    input_plugin.live(on_event=batcher.add)
                case TimeMode.SAMPLE:
                    input_plugin.sample(on_event=batcher.add)
                case _:
                    assert_never(time_mode)
    except AttributeError:
        logger.error(
            f'Specified input plugin does not support "{time_mode}" mode'
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
    input_queue: Queue,
    event_queue: Queue,
    is_done: EventClass
) -> None:
    logger.info('Initializing event plugin')

    try:
        event_plugin = JinjaEventPlugin(config)
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

    is_running = True
    while is_running:
        timestamps_batch = input_queue.get()
        if timestamps_batch is None:
            is_running = False
            break

        try:
            with Batcher(
                size=settings.OUTPUT_BATCH_SIZE,
                timeout=settings.OUTPUT_BATCH_TIMEOUT,
                callback=event_queue.put
            ) as batcher:
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
    config: OutputConfigMapping,
    queue: Queue,
    processed_events: SynchronizedBase,
    is_done: EventClass
) -> None:
    plugins_list_fmt = ", ".join([f'"{plugin}"' for plugin in config.keys()])

    logger.info(f'Initializing [{plugins_list_fmt}] output plugins')

    output_plugins: list[BaseOutputPlugin] = []

    for output, output_conf in config.items():
        try:
            match output:
                case OutputType.STDOUT:
                    output_plugins.append(
                        StdoutOutputPlugin(format=output_conf.format)
                    )
                case OutputType.FILE:
                    output_plugins.append(
                        FileOutputPlugin(
                            filepath=output_conf.path,  # type: ignore
                            format=output_conf.format,
                        )
                    )
                case val:
                    assert_never(val)
        except OutputPluginConfigurationError as e:
            logger.error(f'Failed to initialize "{output}" output plugin: {e}')
            _terminate_subprocess(is_done, 1)
        except Exception as e:
            logger.error(
                'Unexpected error occurred during initializing '
                f'"{output}" output plugin: {e}'
            )
            _terminate_subprocess(is_done, 1)

    logger.info('Output plugins are successfully initialized')

    async def write_batch(
        plugin: BaseOutputPlugin,
        events_batch: NDArray[np.str_]
    ) -> None:
        # TODO: make BaseOutputPlugin methods async
        try:
            if len(events_batch) == 1:
                plugin.write(events_batch[0])
            elif len(events_batch) > 1:
                plugin.write_many(events_batch)
        except OutputPluginRuntimeError as e:
            logger.error(f'Failed to write events to output: {e}')

    async def run_loop() -> None:
        with ThreadPoolExecutor(max_workers=1) as executor:
            loop = asyncio.get_running_loop()

            is_running = True
            while is_running:
                events_batch = await loop.run_in_executor(executor, queue.get)

                if events_batch is None:
                    is_running = False
                    break

                tasks = []
                for plugin in output_plugins:
                    tasks.append(write_batch(plugin, events_batch))

                await asyncio.gather(*tasks)

                processed_events.value += len(events_batch)  # type: ignore

    asyncio.run(run_loop())

    logger.info('Stopping output plugins')
    _terminate_subprocess(is_done, 0)
