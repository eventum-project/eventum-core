import logging
import os
from multiprocessing import Event, Process, Queue
from time import perf_counter, sleep
from typing import NoReturn, assert_never

import eventum.logging_config
import psutil
from eventum.core import settings
from eventum.core.models.application_config import (ApplicationConfig,
                                                    CronInputConfig,
                                                    InputConfigMapping,
                                                    InputType,
                                                    JinjaEventConfig,
                                                    OutputConfigMapping,
                                                    OutputType,
                                                    PatternsInputConfig,
                                                    SampleInputConfig,
                                                    TimestampsInputConfig)
from eventum.core.models.time_mode import TimeMode
from eventum.core.plugins.event.jinja import JinjaEventPlugin
from eventum.core.plugins.input.cron import CronInputPlugin
from eventum.core.plugins.input.sample import SampleInputPlugin
from eventum.core.plugins.input.time_pattern import TimePatternPoolInputPlugin
from eventum.core.plugins.input.timestamps import TimestampsInputPlugin
from eventum.core.plugins.output.base import BaseOutputPlugin
from eventum.core.plugins.output.stdout import StdoutOutputPlugin
from eventum.repository.manage import load_time_pattern
from setproctitle import getproctitle, setproctitle

eventum.logging_config.apply()
logger = logging.getLogger(__name__)


class Application:
    def __init__(
        self,
        config: ApplicationConfig,
        time_mode: TimeMode
    ) -> None:
        self._config = config

        self._time_mode = time_mode

        self._input_queue = Queue()
        self._is_input_queue_awaited = Event()
        self._is_input_queue_awaited.set()

        self._output_queue = Queue()
        self._is_output_queue_awaited = Event()
        self._is_output_queue_awaited.set()

        self._is_input_done = Event()

    @staticmethod
    def _start_input_module(
        input_conf: InputConfigMapping,
        time_mode: TimeMode,
        queue: Queue,
        is_done: Event  # type: ignore
    ) -> NoReturn:
        setproctitle(f'{getproctitle()} [input]')

        input_type, input_conf = input_conf.popitem()

        match input_type:
            case InputType.PATTERNS:
                input_conf: PatternsInputConfig

                configs = []
                for path in input_conf:
                    configs.append(load_time_pattern(path))

                input_plugin = TimePatternPoolInputPlugin(configs)
            case InputType.TIMESTAMPS:
                input_conf: TimestampsInputConfig
                input_plugin = TimestampsInputPlugin(
                    timestamps=input_conf
                )
            case InputType.CRON:
                input_conf: CronInputConfig
                input_plugin = CronInputPlugin(
                    expression=input_conf.expression,
                    count=input_conf.count
                )
            case InputType.SAMPLE:
                input_conf: SampleInputConfig
                input_plugin = SampleInputPlugin(count=input_conf.count)
            case _:
                assert_never(input_type)

        try:
            match time_mode:
                case TimeMode.LIVE:
                    input_plugin.live(on_event=lambda ts: queue.put(ts))
                case TimeMode.SAMPLE:
                    input_plugin.sample(on_event=lambda ts: queue.put(ts))
                case _:
                    assert_never(time_mode)
        except AttributeError as e:
            raise AttributeError(
                f'Specified input plugin does not support "{time_mode}" mode'
            ) from e

        is_done.set()

    @staticmethod
    def _start_event_module(
        config: JinjaEventConfig,
        input_queue: Queue,
        output_queue: Queue,
        is_incoming_awaited: Event  # type: ignore
    ) -> NoReturn:
        setproctitle(f'{getproctitle()} [event]')

        event_plugin = JinjaEventPlugin(config)

        while is_incoming_awaited.is_set():
            timestamp = input_queue.get()
            event_plugin.produce(
                callback=lambda event: output_queue.put(event),
                timestamp=timestamp
            )

    @staticmethod
    def _start_output_module(
        config: OutputConfigMapping,
        queue: Queue,
        is_incoming_awaited: Event  # type: ignore
    ) -> NoReturn:
        setproctitle(f'{getproctitle()} [output]')

        output_plugins: list[BaseOutputPlugin] = []

        for output, output_conf in config.items():
            match output:
                case OutputType.STDOUT:
                    output_plugins.append(
                        StdoutOutputPlugin(
                            format=output_conf.format
                        )
                    )
                case OutputType.FILE:
                    ...
                case val:
                    assert_never(val)

        while is_incoming_awaited.is_set():
            start = perf_counter()
            while (
                queue.qsize() < settings.FLUSH_AFTER_SIZE
                and (perf_counter() - start) < settings.FLUSH_AFTER_SECONDS
            ):
                sleep(max(0.01, settings.FLUSH_AFTER_SECONDS * 0.1))

            events = [queue.get() for _ in range(queue.qsize())]

            if events:
                for plugin in output_plugins:
                    plugin.write_many(events)

    def start(self) -> NoReturn:

        _proc_input = Process(
            target=self._start_input_module,
            args=(
                self._config.input,
                self._time_mode,
                self._input_queue,
                self._is_input_done
            )
        )
        _proc_event = Process(
            target=self._start_event_module,
            args=(
                self._config.event,
                self._input_queue,
                self._output_queue,
                self._is_input_queue_awaited
            )
        )
        _proc_output = Process(
            target=self._start_output_module,
            args=(
                self._config.output,
                self._output_queue,
                self._is_output_queue_awaited
            )
        )

        _proc_input.start()
        _proc_event.start()
        _proc_output.start()

        setproctitle(f'{getproctitle()} [supervisor]')

        _ = psutil.Process(os.getpid())

        while True:
            if not _proc_output.is_alive():
                logger.critical('Output subprocess terminated unexpectedly')
                _proc_input.terminate()
                _proc_event.terminate()
                break

            if not _proc_event.is_alive():
                logger.critical('Event subprocess terminated unexpectedly')
                _proc_input.terminate()
                _proc_output.terminate()
                break

            if not _proc_input.is_alive():
                if self._is_input_done.is_set():
                    logger.info('Input module completed successfully')

                    logger.info('Waiting input queue to empty')
                    while not self._input_queue.empty():
                        sleep(0.1)
                    self._is_input_queue_awaited.clear()

                    logger.info('Waiting output queue to empty')
                    while not self._output_queue.empty():
                        sleep(0.1)
                    self._is_output_queue_awaited.clear()
                else:
                    logger.critical('Input subprocess terminated unexpectedly')
                    _proc_event.terminate()
                    _proc_output.terminate()

                break

            sleep(0.1)

        logger.info('Stopping application')
