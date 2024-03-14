import os
import logging.config

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

CORE_LOG_PATH = os.path.join(LOGS_DIR, 'core.log')
STUDIO_LOG_PATH = os.path.join(LOGS_DIR, 'studio.log')
CLI_LOG_PATH = os.path.join(LOGS_DIR, 'cli.log')
REPOSITORY_LOG_PATH = os.path.join(LOGS_DIR, 'repository.log')

MiB = 1048576

LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'file-formatter': {
            'format': (
                '%(asctime)s %(name)s [%(process)d] '
                '%(levelname)s: %(message)s'
            )
        },
        'stderr-formatter': {
            'format': (
                '%(name)s: %(message)s'
            )
        },
    },
    'disable_existing_loggers': True,
    'handlers': {
        'stderr': {
            'level': 'WARNING',
            'formatter': 'stderr-formatter',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stderr'
        },
        'core-log': {
            'level': 'INFO',
            'formatter': 'file-formatter',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': CORE_LOG_PATH,
            'maxBytes': 1 * MiB,
            'backupCount': 3
        },
        'studio-log': {
            'level': 'INFO',
            'formatter': 'file-formatter',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': STUDIO_LOG_PATH,
            'maxBytes': 1 * MiB,
            'backupCount': 3
        },
        'cli-log': {
            'level': 'INFO',
            'formatter': 'file-formatter',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': CLI_LOG_PATH,
            'maxBytes': 1 * MiB,
            'backupCount': 3
        },
        'repository-log': {
            'level': 'INFO',
            'formatter': 'file-formatter',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': REPOSITORY_LOG_PATH,
            'maxBytes': 1 * MiB,
            'backupCount': 3
        },
    },
    'loggers': {
        'eventum.core': {
            'handlers': ['core-log', 'stderr'],
            'level': 'INFO',
        },
        'eventum.studio': {
            'handlers': ['studio-log', 'stderr'],
            'level': 'INFO',
        },
        'eventum.cli': {
            'handlers': ['cli-log', 'stderr'],
            'level': 'INFO',
        },
        'eventum.repository': {
            'handlers': ['repository-log', 'stderr'],
            'level': 'INFO',
        },
    }
}


def apply():
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR, exist_ok=True)

    logging.config.dictConfig(config=LOGGING_CONFIG)
