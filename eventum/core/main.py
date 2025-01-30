import time
from typing import Any, Iterable, NoReturn

import structlog
import yaml
from pydantic import ValidationError, validate_call

from eventum.core.manager import GeneratorManager, ManagingError
from eventum.core.models.parameters.generator import GeneratorParameters
from eventum.core.models.settings import Settings
from eventum.utils.validation_prettier import prettify_validation_errors

logger = structlog.stdlib.get_logger()


class AppError(Exception):
    """Application error."""

    def __init__(self, *args: object, context: dict[str, Any]) -> None:
        super().__init__(*args)

        self.context = context


class App:
    """Main application.

    Parameters
    ----------
    settings : Settings
        Settings of the applications
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._manager = GeneratorManager()

    def start(self) -> NoReturn:
        """Start the app."""
        gen_list = self._load_generators_list()
        self._start_generators(generators_params=gen_list)

        if self._settings.api.enabled:
            self._start_api()

        while True:
            time.sleep(812)

    @validate_call
    def _validate_generators_list(
        self,
        object: list[dict]
    ) -> list[GeneratorParameters]:
        """Validate list of generators.

        Parameters
        ----------
        object : list[dict]
            Object loaded from content of file with list of generators

        Returns
        -------
        list[GeneratorParameters]
            Validated list of generators parameters applied above
            generation parameters from setting
        """
        generators_parameters: list[GeneratorParameters] = []

        base_params = self._settings.generation.model_dump()
        for params in object:
            params = base_params | params
            generators_parameters.append(
                GeneratorParameters.model_validate(params)
            )

        return generators_parameters

    def _load_generators_list(self) -> list[GeneratorParameters]:
        """Load generators list from specified file.

        Returns
        -------
        list[GeneratorParameters]
            List of defined generators parameters
        """
        logger.info(
            'Loading generators list',
            file_path=self._settings.path.generators
        )
        try:
            with open(self._settings.path.generators) as f:
                content = f.read()
        except OSError as e:
            raise AppError(
                'Failed to read generators list',
                context=dict(
                    file_path=self._settings.path.generators,
                    reason=str(e)
                )
            )

        try:
            obj = yaml.load(content, Loader=yaml.SafeLoader)
        except yaml.error.YAMLError as e:
            raise AppError(
                'Failed to parse generators list',
                context=dict(
                    file_path=self._settings.path.generators,
                    reason=str(e)
                )
            )

        try:
            return self._validate_generators_list(obj)
        except ValidationError as e:
            raise AppError(
                'Invalid structure of generators list',
                context=dict(reason=prettify_validation_errors(e.errors()))
            )

    def _start_generators(
        self,
        generators_params: Iterable[GeneratorParameters]
    ) -> None:
        """Start generators.

        Parameters
        ----------
        generators_params : Iterable[GeneratorParameters]
            List of generator parameters
        """
        running_generators: list[str] = []
        non_running_generators: list[str] = []

        for params in generators_params:
            logger.info('Starting generator', generator_id=params.id)
            try:
                self._manager.add(params)
                self._manager.start(params.id)
                running_generators.append(params.id)
            except ManagingError as e:
                non_running_generators.append(params.id)
                logger.error(
                    'Failed to start generator',
                    generator_id=params.id,
                    reason=str(e)
                )

        logger.info(
            'Generators are running',
            count=len(running_generators),
            running_generators=running_generators,
            non_running_generators=non_running_generators
        )

    def _start_api(self) -> None:
        """Start application API."""
        # TODO: implement
