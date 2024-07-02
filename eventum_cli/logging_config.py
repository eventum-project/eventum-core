import logging.config
import logging.handlers
import os
import pathlib

LOG_DIR = os.path.join(pathlib.Path.home(), '.eventum', 'logs')
MiB = 1024 * 1024


def apply(
    stderr_level: int = logging.WARNING,
    file_level: int = logging.INFO,
    log_filename: str = 'eventum.log'
):
    log_path = os.path.join(LOG_DIR, log_filename)
    config = {
        'version': 1,
        'formatters': {
            'file-formatter': {
                'format': (
                    '%(asctime)s %(name)s [%(levelname)s]: %(message)s'
                )
            },
            'stderr-formatter': {
                'format': (
                    '%(name)s: %(message)s'
                )
            },
        },
        'handlers': {
            'stderr': {
                'level': logging._levelToName[stderr_level],
                'formatter': 'stderr-formatter',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stderr'
            },
            'file': {
                'level': logging._levelToName[file_level],
                'formatter': 'file-formatter',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': log_path,
                'maxBytes': 5 * MiB,
                'backupCount': 10
            }
        },
        'loggers': {
            'eventum_cli': {
                'handlers': ['file', 'stderr'],
                'level': 'INFO',
            },
            '__main__': {
                'handlers': ['file', 'stderr'],
                'level': 'INFO',
            },
            'eventum_core': {
                'handlers': ['file', 'stderr'],
                'level': 'INFO',
            },
            'eventum_plugins': {
                'handlers': ['file', 'stderr'],
                'level': 'INFO',
            },
            'eventum_content_manager': {
                'handlers': ['file', 'stderr'],
                'level': 'INFO',
            },
        }
    }

    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)

    logging.config.dictConfig(config=config)
