import logging.config
import logging.handlers
import platform

LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'file-formatter': {
            'format': (
                '%(name)s %(levelname)s: %(message)s'
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
        'system-log': {
            'level': 'INFO',
            'formatter': 'file-formatter',
            'class': 'logging.handlers.NTEventLogHandler',
            'appname': 'eventum-core'
        } if platform.system() == 'Windows' else {
            'level': 'INFO',
            'formatter': 'file-formatter',
            'class': 'logging.handlers.SysLogHandler',
            'address': '/dev/log'
        }
    },
    'loggers': {
        'core': {
            'handlers': ['system-log', 'stderr'],
            'level': 'INFO',
        }
    }
}


def apply():
    logging.config.dictConfig(config=LOGGING_CONFIG)
