import os
import logging.config
from pathlib import Path

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

CORE_LOG_PATH = os.path.join(LOGS_DIR, 'core.log')
STUDIO_LOG_PATH = os.path.join(LOGS_DIR, 'studio.log')
CLI_LOG_PATH = os.path.join(LOGS_DIR, 'cli.log')
REPOSITORY_LOG_PATH = os.path.join(LOGS_DIR, 'repository.log')


LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'standard': {
            'format': (
                '%(asctime)s %(name)s [%(process)d] '
                '%(levelname)s: %(message)s'
            )
        },
    },
    'disable_existing_loggers': True,
    'handlers': {
        'core': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': CORE_LOG_PATH,
            'maxBytes': 1024,
            'backupCount': 3
        },
        'studio': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': STUDIO_LOG_PATH,
            'maxBytes': 1024,
            'backupCount': 3
        },
        'cli': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': CLI_LOG_PATH,
            'maxBytes': 1024,
            'backupCount': 3
        },
        'repository': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': REPOSITORY_LOG_PATH,
            'maxBytes': 1024,
            'backupCount': 3
        },
    },
    'loggers': {
        'eventum.core': {
            'handlers': ['core'],
            'level': 'INFO',
        },
        'eventum.studio': {
            'handlers': ['studio'],
            'level': 'INFO',
        },
        'eventum.cli': {
            'handlers': ['cli'],
            'level': 'INFO',
        },
        'eventum.repository': {
            'handlers': ['repository'],
            'level': 'INFO',
        },
    }
}


def apply():
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR, exist_ok=True)

    logging.config.dictConfig(config=LOGGING_CONFIG)
