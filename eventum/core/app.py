import logging
import signal
from multiprocessing import Event, Process, Queue, Value
from multiprocessing.sharedctypes import SynchronizedBase
from multiprocessing.synchronize import Event as EventClass
import sys
from time import perf_counter, sleep
from typing import Callable, assert_never

from alive_progress import alive_bar
from setproctitle import getproctitle, setproctitle

import eventum.logging_config
from eventum.core import settings
from eventum.core.models.application_config import (ApplicationConfig,
                                                    InputConfigMapping,
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
    def decorator(f: Callable):
        def wrapper(*args, **kwargs):
            setproctitle(f'{getproctitle()} [{module_name}]')

            signal.signal(
                signal.SIGINT,
                lambda signal, stack_frame: exit(0)
            )

            result = f(*args, **kwargs)
            return result

        return wrapper
    return decorator


class Application:
    """Main class to execute application."""

    _IDLE_SLEEP_SECONDS = 0.01

    def __init__(
        self,
        config: ApplicationConfig,
        time_mode: TimeMode
    ) -> None:
        self._config = config

        self._time_mode = time_mode

        self._input_queue: Queue[str] = Queue()
        self._is_input_queue_awaited = Event()
        self._is_input_queue_awaited.set()

        self._event_queue: Queue[str] = Queue()
        self._is_event_queue_awaited = Event()
        self._is_event_queue_awaited.set()

        # `_total_events` should keep 0 if it's hard to predict actual value
        self._total_events: SynchronizedBase = Value('Q', 0)
        self._processed_events: SynchronizedBase = Value('Q', 0)

        # `_total_events` is adjusted as long as input is initialized
        self._is_input_initialized = Event()
        self._is_input_done = Event()

        self._proc_input = Process(
            target=self._start_input_subprocess,
            args=(
                self._config.input,
                self._time_mode,
                self._input_queue,
                self._is_input_initialized,
                self._is_input_done,
                self._total_events,
            )
        )
        self._proc_event = Process(
            target=self._start_event_subprocess,
            args=(
                self._config.event,
                self._input_queue,
                self._event_queue,
                self._is_input_queue_awaited
            )
        )
        self._proc_output = Process(
            target=self._start_output_subprocess,
            args=(
                self._config.output,
                self._event_queue,
                self._is_event_queue_awaited,
                self._processed_events
            )
        )

    @staticmethod
    @subprocess('input')
    def _start_input_subprocess(
        config: InputConfigMapping,
        time_mode: TimeMode,
        queue: Queue,
        is_initialized: EventClass,
        is_done: EventClass,
        total_events: SynchronizedBase,
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
                    total_events.value = len(input_conf)
                case InputType.CRON:
                    input_plugin = CronInputPlugin(
                        expression=input_conf.expression,   # type: ignore
                        count=input_conf.count              # type: ignore
                    )
                case InputType.SAMPLE:
                    input_plugin = SampleInputPlugin(
                        count=input_conf.count              # type: ignore
                    )
                    total_events.value = input_conf.count
                case value:
                    assert_never(value)
        except ContentReadError as e:
            logger.error(f'Failed to load content for input plugin: {e}')
            exit(1)
        except InputPluginConfigurationError as e:
            logger.error(f'Failed to initialize input plugin: {e}')
            exit(1)
        except Exception as e:
            logger.error(
                'Unexpected error occurred during initializing '
                f'input plugin: {e}'
            )
            exit(1)

        is_initialized.set()
        logger.info('Input plugin is successfully initialized')

        try:
            match time_mode:
                case TimeMode.LIVE:
                    input_plugin.live(
                        on_event=lambda ts: queue.put(
                            ts.isoformat()                  # type: ignore
                        )
                    )
                case TimeMode.SAMPLE:
                    input_plugin.sample(
                        on_event=lambda ts: queue.put(
                            ts.isoformat()                  # type: ignore
                        )
                    )
                case _:
                    assert_never(time_mode)
        except AttributeError:
            logger.error(
                f'Specified input plugin does not support "{time_mode}" mode'
            )
            exit(1)
        except InputPluginRuntimeError as e:
            logger.error(
                f'Error occurred during input plugin execution: {e}'
            )
            exit(1)
        except Exception as e:
            logger.error(
                f'Unexpected error occurred during input plugin execution: {e}'
            )
            exit(1)

        is_done.set()

        logger.info('Stopping input plugin')

    @staticmethod
    @subprocess('event')
    def _start_event_subprocess(
        config: JinjaEventConfig,
        input_queue: Queue,
        event_queue: Queue,
        is_incoming_awaited: EventClass
    ) -> None:
        logger.info('Initializing event plugin')

        try:
            event_plugin = JinjaEventPlugin(config)
        except EventPluginConfigurationError as e:
            logger.error(f'Failed to initialize event plugin: {e}')
            exit(1)
        except Exception as e:
            logger.error(
                f'Unexpected error occurred during initializing '
                f'event plugin: {e}'
            )
            exit(1)

        logger.info('Event plugin is successfully initialized')

        while is_incoming_awaited.is_set():
            start = perf_counter()
            while (
                input_queue.qsize() < settings.RENDER_AFTER_SIZE
                and (perf_counter() - start) < settings.RENDER_AFTER_TIMEOUT
            ):
                sleep(Application._IDLE_SLEEP_SECONDS)

            batch_size = min(input_queue.qsize(), settings.RENDER_AFTER_SIZE)

            if not batch_size:
                continue

            timestamps = [
                input_queue.get() for _ in range(batch_size)
            ]

            try:
                events = []
                for timestamp in timestamps:
                    events.extend(
                        event_plugin.render(timestamp=timestamp)
                    )
            except EventPluginRuntimeError as e:
                logger.error(f'Failed to produce event: {e}')
                exit(1)
            except Exception as e:
                logger.error(
                    f'Unexpected error occurred during producing event: {e}'
                )
                exit(1)

            for event in events:
                event_queue.put(event)

        logger.info('Stopping event plugin')

    @staticmethod
    @subprocess('output')
    def _start_output_subprocess(
        config: OutputConfigMapping,
        queue: Queue,
        is_incoming_awaited: EventClass,
        processed_events_feedback: SynchronizedBase
    ) -> None:
        plugins_list_fmt = ", ".join(
            [f'"{plugin}"' for plugin in config.keys()]
        )

        logger.info(f'Initializing [{plugins_list_fmt}] output plugins')

        output_plugins: list[BaseOutputPlugin] = []

        for output, output_conf in config.items():
            try:
                match output:
                    case OutputType.STDOUT:
                        output_plugins.append(
                            StdoutOutputPlugin(
                                format=output_conf.format
                            )
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
                logger.error(
                    f'Failed to initialize "{output}" output plugin: {e}'
                )
                exit(1)
            except Exception as e:
                logger.error(
                    'Unexpected error occurred during initializing '
                    f'"{output}" output plugin: {e}'
                )
                exit(1)

        logger.info('Output plugins are successfully initialized')

        while is_incoming_awaited.is_set():
            start = perf_counter()
            while (
                queue.qsize() < settings.OUTPUT_AFTER_SIZE
                and (perf_counter() - start) < settings.OUTPUT_AFTER_TIMEOUT
            ):
                sleep(Application._IDLE_SLEEP_SECONDS)

            batch_size = min(queue.qsize(), settings.OUTPUT_AFTER_SIZE)

            if not batch_size:
                continue

            events = [queue.get() for _ in range(batch_size)]

            if events:
                for plugin in output_plugins:
                    try:
                        if len(events) == 1:
                            plugin.write(events[0])
                        elif len(events) > 1:
                            plugin.write_many(events)
                    except OutputPluginRuntimeError as e:
                        logger.error(
                            f'Failed to write events to output: {e}'
                        )

                processed_events_feedback.value += len(events)

        logger.info('Stopping output plugins')

    def start(self) -> None:
        logger.info('Application is started')

        self._proc_input.start()
        self._proc_event.start()
        self._proc_output.start()

        setproctitle(f'{getproctitle()} [main]')

        signal.signal(signal.SIGINT, self._handle_termination)
        signal.signal(signal.SIGTERM, self._handle_termination)

        self._is_input_initialized.wait()

        with alive_bar(
            self._total_events.value,
            enrich_print=False,
            file=sys.stderr
        ) as bar:
            bar.title('Generating input timestamps')

            is_running = True
            exit_code = 0

            last_processed_count = 0

            while is_running:
                if last_processed_count > 0:
                    bar.title('Rendering and outputting events')

                processed = self._processed_events.value - last_processed_count
                for _ in range(processed):
                    bar()
                    last_processed_count = self._processed_events.value

                if not self._proc_output.is_alive():
                    logger.critical(
                        'Output plugins subprocess terminated unexpectedly '
                        'or some error occurred'
                    )
                    self._proc_input.terminate()
                    self._proc_event.terminate()
                    exit_code = 1
                    break

                if not self._proc_event.is_alive():
                    logger.critical(
                        'Event plugin subprocess terminated unexpectedly '
                        'or some error occurred'
                    )
                    self._proc_input.terminate()
                    self._proc_output.terminate()
                    exit_code = 1
                    break

                if not self._proc_input.is_alive():
                    if self._is_input_done.is_set():
                        if (
                            self._input_queue.empty()
                            and self._event_queue.empty()
                        ):
                            logger.info('Queues are empty')
                            self._is_input_queue_awaited.clear()
                            self._proc_event.join()

                            self._is_event_queue_awaited.clear()
                            self._proc_output.join()
                            break
                        else:
                            continue
                    else:
                        logger.critical(
                            'Input subprocess terminated unexpectedly '
                            'or some error occurred'
                        )
                        self._proc_event.terminate()
                        self._proc_output.terminate()
                        exit_code = 1
                        break

                sleep(Application._IDLE_SLEEP_SECONDS)

        logger.info('Application is stopped')
        exit(exit_code)

    def _handle_termination(self, signal, stack_frame):
        logger.info('Termination signal received')
        self._proc_input.terminate()
        self._proc_event.terminate()
        self._proc_output.terminate()
        logger.info('Application is stopped')
        exit(0)
