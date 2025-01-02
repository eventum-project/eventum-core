import logging
import signal
from multiprocessing import Event, Process, Queue, Value
from multiprocessing.sharedctypes import SynchronizedBase
from multiprocessing.synchronize import Event as EventClass
from time import sleep
from typing import Any, NoReturn

import numpy as np
from eventum_plugins.event.jinja import JinjaEventConfig
from numpy.typing import NDArray
from pydantic import BaseModel
from setproctitle import getproctitle, setproctitle

from eventum_core.plugins_connector import (InputConfigMapping,
                                            OutputConfigMapping)
from eventum_core.settings import DEFAULT_SETTINGS, Settings, TimeMode
from eventum_core.subprocesses import (start_event_subprocess,
                                       start_input_subprocess,
                                       start_output_subprocess)

logger = logging.getLogger(__name__)


class ApplicationConfig(BaseModel, extra='forbid', frozen=True):
    input: tuple[InputConfigMapping, ...]       # type: ignore[valid-type]
    event: JinjaEventConfig
    output: tuple[OutputConfigMapping, ...]     # type: ignore[valid-type]


class Application:
    """Main class of application."""

    _REFRESH_STATUS_INTERVAL = 0.1

    def __init__(
        self,
        config: ApplicationConfig,
        time_mode: TimeMode,
        settings: Settings = DEFAULT_SETTINGS,
    ) -> None:
        self._config = config
        self._time_mode = time_mode
        self._settings = settings

        # For all queues: The None element indicates that no more new
        # elements will be put in that queue
        # For input queue dtype=[
        #   ('timestamp', 'datetime64[us]'), ('input_id', 'i8')
        # ]
        self._input_queue: Queue[NDArray[Any]] = Queue(
            maxsize=settings.input_queue_max_size
        )
        self._event_queue: Queue[NDArray[np.str_]] = Queue(
            maxsize=settings.event_queue_max_size
        )

        # Regardless of whether the process ended with an error or not
        # this flag must be set by subprocess at the end of its execution.
        # Used to control situations when process was killed from outside.
        self._is_input_done: EventClass = Event()
        self._is_event_done: EventClass = Event()
        self._is_output_done: EventClass = Event()

        self._processed_events: SynchronizedBase = Value('Q', 0)
        self._is_done = False

        self._proc_input = Process(
            target=start_input_subprocess,
            args=(
                self._config.input,
                self._settings,
                self._time_mode,
                self._input_queue,
                self._is_input_done
            )
        )
        self._proc_event = Process(
            target=start_event_subprocess,
            args=(
                self._config.event,
                self._get_input_tags(),
                self._settings,
                self._input_queue,
                self._event_queue,
                self._is_event_done
            )
        )
        self._proc_output = Process(
            target=start_output_subprocess,
            args=(
                self._config.output,
                self._settings,
                self._event_queue,
                self._processed_events,
                self._is_output_done
            )
        )

    @property
    def processed_events(self) -> int:
        """Get currently processed events."""
        return self._processed_events.value     # type: ignore[attr-defined]

    @property
    def is_done(self) -> bool:
        """Get current app state."""
        return self._is_done

    def _get_input_tags(self) -> dict[int, tuple[str]]:
        """Return dictionary where keys are input plugin indices and
        values are input plugin tags.
        """
        return {
            plugin_id: plugin_conf.get_value(   # type: ignore[attr-defined]
            ).tags
            for plugin_id, plugin_conf in enumerate(self._config.input)
        }

    def _terminate_application_on_crash(
        self,
        signal_number: int | None = None
    ) -> NoReturn:
        """Handle termination of application in emergency situation."""
        self._proc_input.terminate()
        self._proc_event.terminate()
        self._proc_output.terminate()

        if signal_number is not None:
            logger.info(
                f'Signal {signal.Signals(signal_number).name} is received'
            )

        self._is_done = True
        logger.info('Application shut down')
        exit(1)

    def _register_signal_handlers(self) -> None:
        """Register handlers for received signals. Call this method
        only after starting all subprocesses to avoid inheritance of
        behavior in subprocesses."""
        signal.signal(
            signal.SIGINT,
            lambda signal, frame: self._terminate_application_on_crash(signal)
        )
        signal.signal(
            signal.SIGTERM,
            lambda signal, frame: self._terminate_application_on_crash(signal)
        )

    def start(self) -> None:
        logger.info('Application is started')

        self._proc_input.start()
        self._proc_event.start()
        self._proc_output.start()

        self._register_signal_handlers()

        setproctitle(f'{getproctitle()} [main]')

        while not self._is_output_done.is_set():
            if (
                not self._proc_input.is_alive()
                and not self._is_input_done.is_set()
            ):
                logger.critical(
                    'Input plugin subprocess terminated unexpectedly '
                    'or some error occurred'
                )
                logger.info('Application shut down')
                self._terminate_application_on_crash()

            if (
                not self._proc_event.is_alive()
                and not self._is_event_done.is_set()
            ):
                logger.critical(
                    'Event plugin subprocess terminated unexpectedly '
                    'or some error occurred'
                )
                logger.info('Application shut down')
                self._terminate_application_on_crash()

            if (
                not self._proc_output.is_alive()
                and not self._is_output_done.is_set()
            ):
                logger.critical(
                    'Output plugins subprocess terminated unexpectedly '
                    'or some error occurred'
                )
                logger.info('Application shut down')
                self._terminate_application_on_crash()

            sleep(Application._REFRESH_STATUS_INTERVAL)

        if self._proc_input.is_alive() or self._proc_event.is_alive():
            self._terminate_application_on_crash()
        else:
            self._proc_input.join()
            self._proc_event.join()
            self._proc_output.join()
            self._is_done = True

        logger.info('Application shut down')
        exit(0)
