from multiprocessing import Process

from eventum.core.entrypoint import start
from eventum.core.models.parameters.generator import GeneratorParameters


class Generator:
    """Generator process wrapper."""

    def __init__(self, parameters: GeneratorParameters) -> None:
        self._parameters = parameters
        self._process = Process(target=start, args=(parameters, ))

    def start(self) -> None:
        """Start generator in subprocess."""
        if self.is_running:
            return

        self._process.start()

    def stop(self) -> None:
        """Stop generator"""
        if not self.is_running:
            return

        self._process.terminate()

    @property
    def is_running(self) -> bool:
        """Wether the generator is running."""
        return self._process.is_alive()
