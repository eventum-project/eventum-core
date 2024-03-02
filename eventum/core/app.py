import os
from multiprocessing import Process, Queue
from typing import NoReturn

import psutil
from eventum.core.models.application_config import (ApplicationConfig,
                                                    CronInputConfig,
                                                    EventConfig,
                                                    InputConfigMapping,
                                                    InputType,
                                                    OutputConfigMapping,
                                                    PatternsInputConfig,
                                                    SampleInputConfig,
                                                    TimestampsInputConfig)
from eventum.core.models.time_mode import TimeMode
from eventum.core.plugins.input.cron import CronInputPlugin
from eventum.core.plugins.input.sample import SampleInputPlugin
from eventum.core.plugins.input.time_pattern import TimePatternPoolInputPlugin
from eventum.core.plugins.input.timestamps import TimestampsInputPlugin
from setproctitle import getproctitle, setproctitle


class Application:
    def __init__(
        self,
        config: ApplicationConfig,
        time_mode: TimeMode
    ) -> None:
        self._config = config

        self._time_mode = time_mode

        self._input_queue = Queue()
        self._output_queue = Queue()

    @staticmethod
    def _start_input_module(
        config: InputConfigMapping,
        queue: Queue,
        time_mode: TimeMode
    ) -> NoReturn:
        setproctitle(f'{getproctitle()} [input]')

        input_type, config = config.popitem()

        match input_type:
            case InputType.PATTERNS:
                config: PatternsInputConfig
                input = TimePatternPoolInputPlugin(...)
            case InputType.TIMESTAMPS:
                config: TimestampsInputConfig
                input = TimestampsInputPlugin(
                    timestamps=config
                )
            case InputType.CRON:
                config: CronInputConfig
                input = CronInputPlugin(
                    expression=config.expression,
                    count=config.count
                )
            case InputType.SAMPLE:
                config: SampleInputConfig
                input = SampleInputPlugin(count=config.count)
            case _:
                raise NotImplementedError(
                    'No input plugin class registered '
                    f'for input type "{input_type}"'
                )

        try:
            match time_mode:
                case TimeMode.LIVE:
                    input.live(on_event=lambda ts: queue.put(ts))
                case TimeMode.SAMPLE:
                    input.sample(on_event=lambda ts: queue.put(ts))
                case _:
                    raise NotImplementedError(
                        f'No input plugin method registered for '
                        f'time mode "{time_mode}"'
                    )
        except AttributeError as e:
            raise AttributeError(
                f'Specified input plugin does not support "{time_mode}" mode'
            ) from e

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

        # TODO while input is alive - to be alive. Otherwise, gracefully stop
        # event and output processes and stop itself.
        _ = psutil.Process(os.getpid())
        setproctitle(f'{getproctitle()} [supervisor]')

        ...

        _proc_input.join()
        _proc_event.join()
        _proc_output.join()
