from multiprocessing import Process
from threading import RLock

from eventum.core.parameters.generator import GeneratorParameters
from eventum.core.runtime.executor import execute


class GeneratorError(Exception):
    """Error during managing generator."""


class Generator:
    def __init__(self, parameters: GeneratorParameters) -> None:
        self._is_running = False
        self._lock = RLock()
        self._parameters = parameters
        self._process = Process(target=execute, args=(parameters, ))

    def run(self) -> None:
        """Run generator with blocking execution until it completes."""
        with self._lock:
            if self._is_running:
                raise GeneratorError('Generator is already running')

            self._process.start()
            self._is_running = True

        self._process.join()
        self._is_running = False

    def stop(self, timeout: float | None = None) -> None:
        """Stop generator.

        Parameters
        ----------
        timeout : float | None, default=None
            The number of seconds to wait for the generator if it is
            not done, if `None` is passed, then there is no limit on
            the wait time

        Raises
        ------
        TimeoutError
            If timeout expired
        """
        with self._lock:
            if not self._is_running:
                return

            # TODO: somehow send stop signal
            self._process.join(timeout)
            self._is_running = False

    def get_metrics(self) -> GeneratorMetrics:
        ...

    @property
    def is_running(self) -> bool:
        """Wether the generator is running."""
        return self._is_running
