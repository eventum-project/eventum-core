import logging
import os
import signal
import sys
from multiprocessing import Event, Process, Queue, Value
from multiprocessing.sharedctypes import SynchronizedBase
from multiprocessing.synchronize import Event as EventClass
from time import sleep
from typing import NoReturn

from alive_progress import alive_bar    # type: ignore
from setproctitle import getproctitle, setproctitle

import eventum.logging_config
from eventum.core.models.application_config import ApplicationConfig
from eventum.core.models.time_mode import TimeMode
from eventum.core.subprocesses import (start_event_subprocess,
                                       start_input_subprocess,
                                       start_output_subprocess)

eventum.logging_config.apply()
logger = logging.getLogger(__name__)


class Application:
    """Main class of application."""

    _IDLE_SLEEP_SECONDS = 0.1

    def __init__(
        self,
        config: ApplicationConfig,
        time_mode: TimeMode
    ) -> None:
        self._config = config
        self._time_mode = time_mode

        # For all queues: The None element indicates that no more new
        # elements will be put in that queue
        self._input_queue: Queue[str] = Queue()
        self._event_queue: Queue[str] = Queue()

        # Regardless of whether the process ended with an error or not
        # this flag must be set at the end of its execution.
        # Used to control situations when process was killed from outside.
        self._is_input_done: EventClass = Event()
        self._is_event_done: EventClass = Event()
        self._is_output_done: EventClass = Event()

        self._processed_events: SynchronizedBase = Value('Q', 0)

        self._proc_input = Process(
            target=start_input_subprocess,
            args=(
                self._config.input,
                self._time_mode,
                self._input_queue,
                self._is_input_done
            )
        )
        self._proc_event = Process(
            target=start_event_subprocess,
            args=(
                self._config.event,
                self._input_queue,
                self._event_queue,
                self._is_event_done
            )
        )
        self._proc_output = Process(
            target=start_output_subprocess,
            args=(
                self._config.output,
                self._event_queue,
                self._processed_events,
                self._is_output_done
            )
        )

    def _terminate_application_on_crash(self) -> NoReturn:
        """Handle termination of application in emergency situation."""
        self._proc_input.terminate()
        self._proc_event.terminate()
        self._proc_output.terminate()
        exit(1)

    def _register_signal_handlers(self) -> None:
        """Register handlers for received signals. Call this method
        only after starting all subprocesses to avoid inheritance of
        behavior in subprocesses."""
        signal.signal(
            signal.SIGINT,
            lambda signal, frame: (
                logger.info('SIGINT is received'),      # type: ignore
                logger.info('Application is stopped'),  # type: ignore
                self._terminate_application_on_crash()
            )
        )
        signal.signal(
            signal.SIGTERM,
            lambda signal, frame: (
                logger.info('SIGTERM is received'),     # type: ignore
                logger.info('Application is stopped'),  # type: ignore
                self._terminate_application_on_crash()
            )
        )

    def _increment_progress(self, bar) -> None:
        """Increment progress by newly processed events value."""
        processed = self._processed_events.value - bar.current  # type: ignore

        for _ in range(processed):
            bar()

    def start(self, interactive: bool = True) -> None:
        logger.info('Application is started')

        self._proc_input.start()
        self._proc_event.start()
        self._proc_output.start()

        self._register_signal_handlers()

        setproctitle(f'{getproctitle()} [main]')

        bar_stream = sys.stderr if interactive else open(os.devnull, 'w')

        with alive_bar(0, enrich_print=False, file=bar_stream) as bar:
            bar.title('Awaiting events')

            while not self._is_output_done.is_set():
                if bar.current > 0:
                    bar.title('Processing events')
                self._increment_progress(bar)

                if (
                    not self._proc_input.is_alive()
                    and not self._is_input_done.is_set()
                ):
                    logger.critical(
                        'Input plugin subprocess terminated unexpectedly '
                        'or some error occurred'
                    )
                    logger.info('Application is stopped')
                    self._terminate_application_on_crash()

                if (
                    not self._proc_event.is_alive()
                    and not self._is_event_done.is_set()
                ):
                    logger.critical(
                        'Event plugin subprocess terminated unexpectedly '
                        'or some error occurred'
                    )
                    logger.info('Application is stopped')
                    self._terminate_application_on_crash()

                if (
                    not self._proc_output.is_alive()
                    and not self._is_output_done.is_set()
                ):
                    logger.critical(
                        'Output plugins subprocess terminated unexpectedly '
                        'or some error occurred'
                    )
                    logger.info('Application is stopped')
                    self._terminate_application_on_crash()

                sleep(Application._IDLE_SLEEP_SECONDS)

            self._proc_input.join()
            self._proc_event.join()
            self._proc_output.join()

            self._increment_progress(bar)

            logger.info('Application is stopped')
            exit(0)
