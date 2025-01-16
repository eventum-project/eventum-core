from typing import Iterable

from eventum.core.generator import Generator
from eventum.core.models.parameters.generator import GeneratorParameters


class ManagingError(Exception):
    """Error in managing generators."""


class GeneratorManager:
    """Manager of generators."""

    def __init__(self) -> None:
        self._generators: dict[str, Generator] = dict()

    def add(self, parameters: GeneratorParameters) -> None:
        """Add new generator with provided parameters to list of managed
        generators.

        Parameters
        ----------
        parameters : GeneratorParameters
            Parameters for generator

        Raises
        ------
        ManagingError
            If generator with this id is already added
        """
        if parameters.id in self._generators:
            raise ManagingError('Generator with this id is already added')

        self._generators[parameters.id] = Generator(parameters)

    def remove(self, generator_id: str) -> None:
        """Remove generator from list of managed generators. Stop it in
        case it is running.

        Parameters
        ----------
        generator_id : str
            ID of generator to remove

        Raises
        ------
        ManagingError
            If generator is not found in list of managed generators
        """
        generator = self.get_generator(generator_id)

        if generator.is_running:
            generator.stop()

        del self._generators[generator_id]

    def bulk_remove(self, generator_ids: Iterable[str]) -> None:
        """Remove generators from list of managed generators. Stop
        generators that are running. If no generator of specified id
        found in list of managed generators it is just skipped.

        Parameters
        ----------
        generator_ids : Iterable[str]
            ID of generators to remove
        """
        for id in generator_ids:
            if id in self._generators:
                generator = self._generators[id]

                if generator.is_running:
                    generator.stop()

                del self._generators[id]

    def start(self, generator_id: str) -> None:
        """Start generator. Ignore call if generator is already
        running.

        Parameters
        ----------
        generator_id : str
            ID of generator to run

        Raises
        ------
        ManagingError
            If generator is not found in list of managed generators
        """
        generator = self.get_generator(generator_id)

        if generator.is_running:
            return

        generator.start()

    def bulk_start(self, generator_ids: Iterable[str]) -> None:
        """Start generators. Ignore call for those that are already
        running. If no generator of specified id found in list of
        managed generators it is just skipped.

        Parameters
        ----------
        generator_ids : Iterable[str]
            ID of generators to start
        """
        for id in generator_ids:
            if id in self._generators:
                generator = self._generators[id]

                if not generator.is_running:
                    generator.start()

    def stop(self, generator_id: str) -> None:
        """Stop generator. Ignore call if generator is not running.

        Parameters
        ----------
        generator_id : str
            ID of generator to stop

        Raises
        ------
        ManagingError
            If generator is not found in list of managed generators
        """
        generator = self.get_generator(generator_id)

        if not generator.is_running:
            return

        generator.stop()

    def bulk_stop(self, generator_ids: Iterable[str]) -> None:
        """Stop generators. Ignore call for those that are not running.
        If no generator of specified id found in list of managed
        generators it is just skipped.

        Parameters
        ----------
        generator_ids : Iterable[str]
            ID of generators to stop
        """
        for id in generator_ids:
            if id in self._generators:
                generator = self._generators[id]

                if generator.is_running:
                    generator.stop()

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
        ManagingError
            If no generator with provided ID found in managed
            generators
        """
        try:
            return self._generators[generator_id]
        except KeyError:
            raise ManagingError('No such generator')

    @property
    def generator_ids(self) -> list[str]:
        """List of generator ids."""
        return list(self._generators.keys())
