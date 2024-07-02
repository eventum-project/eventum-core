import argparse
import json
import logging
import os
import signal
import time
from importlib.metadata import version
from multiprocessing import Process
from typing import Iterable, NoReturn, TypedDict

from eventum_content_manager.manage import (ContentManagementError,
                                            load_app_config,
                                            load_compose_config)
from eventum_core.app import Application
from eventum_core.settings import Settings, TimeMode
from pydantic import BaseModel, Field, ValidationError

import eventum_cli.logging_config as logging_config
from eventum_cli.cli_main import ApplicationConfig
from eventum_cli.config_finalizer import substitute_tokens
from eventum_cli.resolver import resolve_config_path
from eventum_cli.validation_prettier import prettify_errors

VERSION = version('eventum_cli')
logger = logging.getLogger(__name__)


class ComposeGeneratorConfig(BaseModel, frozen=True, extra='forbid'):
    config: str = Field(..., min_length=1)
    time_mode: TimeMode
    params: dict
    settings: dict


class ComposeConfig(BaseModel, frozen=True, extra='forbid'):
    generators: dict[str, ComposeGeneratorConfig] = Field(..., min_length=1)


class ApplicationKwargs(TypedDict):
    config: ApplicationConfig
    time_mode: TimeMode
    settings: Settings


def run_app(*args, **kwargs) -> None:
    """Run the application with specified arguments."""
    Application(*args, **kwargs).start()


def terminate_running_apps(
    processes: Iterable[Process],
    signal_number: int | None = None
) -> NoReturn:
    """Callback for signals handling that terminates started
    applications.
    """
    for proc in processes:
        proc.terminate()

    if signal_number is not None:
        logger.info(
            f'Signal {signal.Signals(signal_number).name} is received'
        )

    logger.info('Processes shut down')
    exit(1)


def _initialize_argparser(argparser: argparse.ArgumentParser) -> None:
    """Add arguments for initial argparser object."""

    parse_as_dict = json.loads
    parse_as_dict.__name__ = 'json parse'

    argparser.add_argument(
        '-c', '--config',
        required=True,
        help='Compose file'
    )
    argparser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable all informational messages in output'
    )
    argparser.add_argument(
        '-V', '--version',
        action='version',
        version=f'eventum-compose {VERSION}'
    )


def main() -> None:
    argparser = argparse.ArgumentParser(
        prog='eventum-compose',
        description='Compose util for Eventum',
        epilog='Documentation: https://eventum-generatives.github.io/Website/',
    )

    _initialize_argparser(argparser)

    args = argparser.parse_args()

    config_basename, _ = os.path.splitext(os.path.basename(args.config))
    log_filename = f'compose-{config_basename}.log'

    if args.verbose:
        logging_config.apply(
            stderr_level=logging.INFO,
            log_filename=log_filename
        )
    else:
        logging_config.apply(log_filename=log_filename)

    logger = logging.getLogger(__name__)

    logger.info('Eventum compose is started')

    logger.info(f'Resolving location of compose file "{args.config}"')
    config_path = resolve_config_path(args.config)

    try:
        raw_config_data = load_compose_config(config_path)
    except ContentManagementError as e:
        logger.error(f'Failed to load compose file: {e}')
        exit(1)

    try:
        config = ComposeConfig.model_validate(raw_config_data)
    except ValidationError as e:
        error_message = prettify_errors(e.errors())
        logger.error(f'Failed to read compose file: {error_message}')
        exit(1)

    apps_kwargs: list[ApplicationKwargs] = []

    for generator_name, generator_config in config.generators.items():
        logger.info(f'Initializing generator "{generator_name}"')
        logger.info(
            f'Resolving location of config file "{generator_config.config}"'
        )
        config_path = resolve_config_path(generator_config.config)

        try:
            config_data = load_app_config(
                path=config_path,
                preprocessor=(
                    lambda content: substitute_tokens(
                        content=content,
                        params=generator_config.params
                    )
                )
            )
        except ContentManagementError as e:
            logger.error(
                f'Failed to load config file '
                f'for generator "{generator_name}": {e}'
            )
            exit(1)
        except ValueError as e:
            logger.error(
                'Failed to substitute tokens to config'
                f'for generator "{generator_name}": {e}'
            )
            exit(1)

        try:
            app_config = ApplicationConfig.model_validate(config_data)
        except ValidationError as e:
            error_message = prettify_errors(e.errors())
            logger.error(
                'Failed to read config file '
                f'for generator "{generator_name}": {error_message}'
            )
            exit(1)

        try:
            settings = Settings(**generator_config.settings)
        except ValidationError as e:
            error_message = prettify_errors(e.errors())
            logger.error(
                'Incorrect settings '
                f'for generator "{generator_name}": {error_message}'
            )
            exit(1)

        apps_kwargs.append(
            {
                'config': app_config,
                'time_mode': TimeMode(generator_config.time_mode),
                'settings': settings
            }
        )

    logger.info(f'Starting {list(config.generators.keys())} generators')

    app_processes: list[Process] = []
    for kwargs in apps_kwargs:
        app_processes.append(Process(target=run_app, kwargs=kwargs))

    for proc in app_processes:
        proc.start()

    for reg_signal in [signal.SIGINT, signal.SIGTERM]:
        signal.signal(
            reg_signal,
            lambda signalnum, stack_frame: (
                terminate_running_apps(
                    processes=app_processes,
                    signal_number=signalnum
                )
            )
        )

    active_processes: dict[str, Process] = {
        name: proc
        for name, proc in zip(config.generators.keys(), app_processes)
    }

    while active_processes:
        done_processes: list[str] = []
        for name, proc in active_processes.items():
            if not proc.is_alive():
                if proc.exitcode == 0:
                    logger.info(
                        f'Generator "{name}" exited with code {proc.exitcode}'
                    )
                else:
                    logger.error(
                        f'Generator "{name}" exited with code {proc.exitcode}'
                    )
                proc.join()
                done_processes.append(name)

        for name in done_processes:
            active_processes.pop(name)

        time.sleep(0.1)

    logger.info('All process exited')
