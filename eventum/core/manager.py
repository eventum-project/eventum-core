from concurrent.futures import Future, ThreadPoolExecutor
from eventum.core.parameters.generator import GeneratorParameters
from eventum.core.generator import Generator


class ManagingError(Exception):
    """Error in managing generators."""


class GeneratorManager:
    """Manager of generators."""

    def __init__(self) -> None:
        self._generators: dict[str, Generator] = dict()
        self._running_tasks: dict[str, Future] = dict()
        self._executor = ThreadPoolExecutor()

    def shutdown(
        self,
        wait: bool = True,
        cancel_pending: bool = False
    ) -> None:
        """Shutdown generators manager.

        wait : bool, default=True
            Wait until all running generators have finished execution

        cancel_pending : bool, default=False
            Wether to cancel all pending generators that was added but
            not yet being started by executor
        """
        self._executor.shutdown(wait, cancel_futures=cancel_pending)

    def add(self, parameters: GeneratorParameters) -> None:
        """Add new generator with provided parameters to list of managed
        generators.

        Parameters
        ----------
        parameters : GeneratorParameters
            Parameters for generator
        """
        ...

    def remove(self, generator_id: str) -> None:
        """Remove generator from list of managed generators.

        Parameters
        ----------
        generator_id : str
            ID of generator to remove

        Raises
        ------
        ValueError
            If generator is not found in list of managed generators

        ManagingError
            If generator is currently running
        """
        generator = self.get_generator(generator_id)

        if generator.is_running:
            raise ManagingError('Generator is running')
        else:
            del self._generators[generator_id]

    def run(self, generator_id: str) -> None:
        """Run generator.

        Parameters
        ----------
        generator_id : str
            ID of generator to run

        Raises
        ------
        ValueError
            If generator is not found in list of managed generators
        """
        generator = self.get_generator(generator_id)

        task = self._executor.submit(generator.run)
        self._running_tasks[generator_id] = task

    def stop(self, generator_id: str) -> None:
        """Stop generator.

        Parameters
        ----------
        generator_id : str
            ID of generator to stop

        Raises
        ------
        ValueError
            If generator is not found in list of managed generators

        ManagingError
            If error occurs during generator stopping
        """
        generator = self.get_generator(generator_id)

        try:
            generator.stop()
        except Exception as e:  # TODO narrow exception type
            raise ManagingError(str(e))

    def get_metrics(self, generator_id: str) -> GeneratorMetrics:
        """Get metrics of generator.

        Parameters
        ----------
        generator_id : str
            ID of generator to get metrics of

        Returns
        -------
        GeneratorMetrics
            Metrics

        Raises
        ------
        ValueError
            If generator is not found in list of managed generators

        ManagingError
            If error occurs during getting metrics
        """
        generator = self.get_generator(generator_id)

        try:
            return generator.get_metrics()
        except Exception as e:  # TODO narrow exception type
            raise ManagingError(str(e))

    def wait(self, generator_id: str, timeout: float | None = None) -> None:
        """Wait for generator to complete.

        Parameters
        ----------
        generator_id : str
            ID of generator to wait for

        timeout : float | None, default=None
            The number of seconds to wait for the generator if it is
            not done, if `None` is passed, then there is no limit on
            the wait time

        Raises
        ------
        ManagingError
            If generator is not running

        TimeoutError
            If timeout expired

        ManagingError
            If error occurs during waiting for generator
        """
        try:
            future = self._running_tasks[generator_id]
        except KeyError:
            raise ManagingError('Generator is not running')

        try:
            future.result(timeout=timeout)
            del self._running_tasks[generator_id]
        except TimeoutError as e:
            raise e
        except Exception as e:  # TODO narrow exception type
            del self._running_tasks[generator_id]
            raise ManagingError(str(e))

    @property
    def generator_ids(self) -> list[str]:
        """List of generator ids."""
        return list(self._generators.keys())

    def get_generator(self, generator_id: str) -> Generator:
        """Get generator from list of managed generators.

        Parameters
        ----------
        generator_id : str
            ID of generator to get

        Returns
        -------
        Generator
            Generator with provided ID

        Raises
        ------
        ValueError
            If no generator with provided ID found in managed
            generators
        """
        try:
            return self._generators[generator_id]
        except KeyError:
            raise ValueError('No such generator')
