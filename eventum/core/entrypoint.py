import os
import time

import structlog
from setproctitle import getproctitle, setproctitle

from eventum.core.config import ConfigurationLoadError, load
from eventum.core.executor import (ExecutionError, Executor,
                                   ImproperlyConfiguredError)
from eventum.core.initializer import InitializationError, init_plugins
from eventum.core.models.exit_codes import ExitCode
from eventum.core.models.parameters.generator import GeneratorParameters

logger = structlog.stdlib.get_logger()


def start(params: GeneratorParameters) -> None:
    """Start generator execution.

    Parameters
    ----------
    params : GeneratorParameters
        Parameters for generator
    """
    setproctitle(title=f'{getproctitle()} ({params.id})')

    logger.info('Loading configuration')
    init_start_time = time.time()

    try:
        config = load(params.path, params.params)
    except ConfigurationLoadError as e:
        logger.error(str(e), **e.context)
        exit(ExitCode.CONFIG_ERROR)
    except Exception as e:
        logger.exception(
            'Unexpected error occurred during loading config',
            reason=str(e),
            file_path=params.path
        )
        exit(ExitCode.UNEXPECTED_ERROR)

    working_dir = os.path.dirname(os.path.abspath(params.path))
    logger.info('Setting working directory', path=working_dir)
    os.chdir(working_dir)

    logger.info('Initializing plugins')
    try:
        plugins = init_plugins(
            input=config.input,
            event=config.event,
            output=config.output,
            params=params
        )
    except InitializationError as e:
        logger.error(str(e), **e.context)
        exit(ExitCode.INIT_ERROR)
    except Exception as e:
        logger.exception(
            'Unexpected error occurred during initializing plugins',
            reason=str(e)
        )
        exit(ExitCode.UNEXPECTED_ERROR)

    try:
        executor = Executor(
            input=plugins.input,
            event=plugins.event,
            output=plugins.output,
            params=params
        )
    except ImproperlyConfiguredError as e:
        logger.error(str(e), **e.context)
        exit(ExitCode.INIT_ERROR)
    except Exception as e:
        logger.exception(
            'Unexpected error occurred during initializing',
            reason=str(e)
        )
        exit(ExitCode.UNEXPECTED_ERROR)

    init_time = round(time.time() - init_start_time, 3)
    logger.info('Initialization completed', seconds=init_time)

    logger.info('Starting execution', parameters=params.model_dump())
    try:
        executor.execute()
    except ExecutionError as e:
        logger.error(str(e), **e.context)
        exit(ExitCode.EXECUTION_ERROR)
    except Exception as e:
        logger.exception(
            'Unexpected error occurred during execution',
            reason=str(e)
        )
        exit(ExitCode.UNEXPECTED_ERROR)
