import os
from multiprocessing import Process, Queue
from typing import NoReturn

import psutil
from eventum.core.defaults import get_default_settings
from eventum.core.models.application_config import (ApplicationConfig,
                                                    InputConfigMapping,
                                                    EventConfig,
                                                    OutputConfigMapping,
                                                    InputType)
from eventum.core.models.runtime_settings import RuntimeSettings
from eventum.core.models.time_mode import TimeMode
from setproctitle import getproctitle, setproctitle
import eventum.core.time_distribution as td


class Application:
    def __init__(
        self,
        config: ApplicationConfig,
        time_mode: TimeMode,
        settings: RuntimeSettings | None
    ) -> None:
        self._config = config

        self._time_mode = time_mode
        self._settings = settings or get_default_settings()

        self._input_queue = Queue()
        self._output_queue = Queue()

    @staticmethod
    def _start_input_module(
        config: InputConfigMapping,
        queue: Queue,
        time_mode: TimeMode
    ) -> NoReturn:
        setproctitle(f'{getproctitle()} [input]')

        input_type, input_config = config.popitem()

        match input_type:
            case InputType.PATTERNS:
                distr = td.TimePatternPoolDistribution()
            case InputType.TIMESTAMPS:
                distr = td.ManualTimeDistribution()
            case InputType.CRON:
                distr = td.CronTimeDistribution()
            case InputType.SAMPLE:
                distr = td.SampleTimeDistribution()
            case _:
                raise NotImplementedError(
                    'No distribution class registered '
                    f'for input type "{input_type}"'
                )

        match time_mode:
            case TimeMode.LIVE:
                distr.live(on_event=lambda ts: queue.put(ts))
            case TimeMode.SAMPLE:
                distr.sample(on_event=lambda ts: queue.put(ts))
            case _:
                raise NotImplementedError(
                    f'No distribution method registred for '
                    f'time mode "{time_mode}"'
                )

    @staticmethod
    def _start_event_module(
        config: EventConfig,
        input_queue: Queue,
        output_queue: Queue
    ) -> NoReturn:
        setproctitle(f'{getproctitle()} [event]')

        while True:
            _ = input_queue.get()
            ...
            output_queue.put(...)

    @staticmethod
    def _start_output_module(
        config: OutputConfigMapping,
        queue: Queue
    ) -> NoReturn:
        setproctitle(f'{getproctitle()} [output]')

        while True:
            _ = queue.get(...)

    def start(self) -> NoReturn:

        _proc_input = Process(
            target=self._start_input_module,
            args=(self._config.input, self._input_queue, self._time_mode)
        )
        _proc_event = Process(
            target=self._start_event_module,
            args=(self._config.event, self._input_queue, self._output_queue)
        )
        _proc_output = Process(
            target=self._start_output_module,
            args=(self._config.output, self._output_queue)
        )

        _proc_input.start()
        _proc_event.start()
        _proc_output.start()

        _ = psutil.Process(os.getpid())
        setproctitle(f'{getproctitle()} [supervisor]')

        ...

        _proc_input.join()
        _proc_event.join()
        _proc_output.join()
