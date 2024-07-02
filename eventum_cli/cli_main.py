import argparse
import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from importlib.metadata import version
from typing import Callable

from alive_progress import alive_bar  # type: ignore[import-untyped]
from eventum_content_manager.manage import (ContentManagementError,
                                            load_app_config)
from eventum_core.app import Application, ApplicationConfig
from eventum_core.settings import Settings, TimeMode
from pydantic import ValidationError

import eventum_cli.logging_config as logging_config
from eventum_cli.config_finalizer import substitute_tokens
from eventum_cli.resolver import resolve_config_path
from eventum_cli.validation_prettier import prettify_errors

VERSION = version('eventum_cli')
logger: logging.Logger | None = None


def _initialize_argparser(argparser: argparse.ArgumentParser) -> None:
    """Add arguments for initial argparser object."""

    parse_as_dict = json.loads
    parse_as_dict.__name__ = 'json parse'

    argparser.add_argument(
        '-c', '--config',
        required=True,
        help='Configuration file'
    )
    argparser.add_argument(
        '-t', '--time-mode',
        required=True,
        choices=[str(elem) for elem in TimeMode],
        help='Time mode'
    )
    argparser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='Enable interactive mode'
    )
    argparser.add_argument(
        '-s', '--settings',
        type=parse_as_dict,
        default='{ }',
        help='Core settings, json string'
    )
    argparser.add_argument(
        '-p', '--params',
        type=parse_as_dict,
        default='{ }',
        help='Parameters to use in config, json string'
    )
    argparser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable all informational messages in output'
    )
    argparser.add_argument(
        '-V', '--version',
        action='version',
        version=f'eventum-cli {VERSION}'
    )


def display_progress_bar(
    get_value_callback: Callable[[], int],
    check_done_callback: Callable[[], bool],
    update_interval: float
) -> None:
    """Display progress bar. This function should be submitted to
    background thread. The provided callbacks are used to retrieve
    current progress value and stop thread condition.
    """
    with alive_bar(
        0,
        enrich_print=False,
        file=sys.stderr,
        refresh_secs=update_interval,
        title='Processing events'
    ) as bar:
        while not check_done_callback():
            processed = get_value_callback() - bar.current

            for _ in range(processed):
                bar()

            time.sleep(update_interval)


def main() -> None:
    argparser = argparse.ArgumentParser(
        prog='eventum',
        description='Flexible event generator',
        epilog='Documentation: https://eventum-generatives.github.io/Website/',
    )

    _initialize_argparser(argparser)

    args = argparser.parse_args()

    config_basename, _ = os.path.splitext(os.path.basename(args.config))
    log_filename = f'generator-{config_basename}.log'

    if args.verbose:
        logging_config.apply(
            stderr_level=logging.INFO,
            log_filename=log_filename
        )
    else:
        logging_config.apply(log_filename=log_filename)

    logger = logging.getLogger(__name__)

    logger.info('Eventum CLI is started')

    logger.info(f'Resolving location of config file "{args.config}"')
    config_path = resolve_config_path(args.config)

    try:
        config_data = load_app_config(
            path=config_path,
            preprocessor=(
                lambda content: substitute_tokens(
                    content=content,
                    params=args.params
                )
            )
        )
    except ContentManagementError as e:
        logger.error(f'Failed to load config file: {e}')
        exit(1)
    except ValueError as e:
        logger.error(f'Failed to substitute tokens to config: {e}')
        exit(1)

    try:
        config = ApplicationConfig.model_validate(config_data)
    except ValidationError as e:
        error_message = prettify_errors(e.errors())
        logger.error(f'Failed to read config file: {error_message}')
        exit(1)

    logger.info(
        f'Starting application with loaded config in {args.time_mode} mode'
    )

    try:
        settings = Settings(**args.settings)
    except ValidationError as e:
        error_message = prettify_errors(e.errors())
        logger.error(f'Incorrect settings: {error_message}')
        exit(1)

    app = Application(
        config=config,
        time_mode=TimeMode(args.time_mode),
        settings=settings
    )

    if args.interactive:
        with ThreadPoolExecutor(max_workers=3) as executor:
            task = executor.submit(
                display_progress_bar,
                get_value_callback=lambda: app.processed_events,
                check_done_callback=lambda: app.is_done,
                update_interval=0.05
            )
            app.start()
            task.result()
    else:
        app.start()
