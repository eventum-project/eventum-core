import os
from multiprocessing import Process, Queue
from typing import NoReturn

import psutil
from eventum.core.models.application_config import (ApplicationConfig,
                                                    EventConfig, InputConfig,
                                                    OutputConfig)
from setproctitle import getproctitle, setproctitle


class Application:
    def __init__(self, config: ApplicationConfig) -> None:
        self._config = config

        self._input_queue = Queue()
        self._output_queue = Queue()

    @staticmethod
    def _start_input_module(config: InputConfig, queue: Queue) -> NoReturn:
        setproctitle(f'{getproctitle()} [input]')

        while True:
            queue.put(...)

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
    def _start_output_module(config: OutputConfig, queue: Queue) -> NoReturn:
        setproctitle(f'{getproctitle()} [output]')

        while True:
            _ = queue.get(...)

    def start(self) -> NoReturn:

        _proc_input = Process(
            target=self._start_input_module,
            args=(self._config.input, self._input_queue)
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
