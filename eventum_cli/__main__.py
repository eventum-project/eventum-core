import argparse
import json
import logging
import os

from eventum_content_manager.manage import (ContentManagementError,
                                            load_app_config)
from eventum_core.app import Application, ApplicationConfig
from eventum_core.settings import Settings, TimeMode
from pydantic import ValidationError

from eventum_cli.config_finalizer import substitute_tokens
from eventum_cli.validation_prettier import prettify_errors

logger = logging.getLogger(__name__)


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


def main() -> None:
    argparser = argparse.ArgumentParser(
        prog="eventum",
        description="Flexible event generation tool",
        epilog="Repository: https://github.com/rnv812/Eventum",
    )

    _initialize_argparser(argparser)

    args = argparser.parse_args()

    logger.info('Eventum CLI is started')
    logger.info(f'Resolving location of config file "{args.config}"')

    if os.path.isabs(args.config):
        config_path = args.config
    else:
        config_path = os.path.join(
            os.path.abspath(os.getcwd()), args.config
        )

        if not os.path.exists(config_path):
            logger.info(
                'Config file not found from current location and '
                'will be read from repository'
            )
            config_path = args.config

    try:
        raw_config_data = load_app_config(config_path)
    except ContentManagementError as e:
        logger.error(f'Failed to load config file: {e}')
        exit(1)

    try:
        final_config_data = substitute_tokens(
            config=raw_config_data,
            params=args.params
        )
    except ValueError as e:
        logger.error(f'Failed to substitute tokens to config: {e}')
        exit(1)

    try:
        config = ApplicationConfig.model_validate(final_config_data)
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

    app.start()


if __name__ == '__main__':
    main()
