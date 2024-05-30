import logging.config
import logging.handlers
import platform


def apply(
    stderr_level: int = logging.WARNING,
    syslog_level: int = logging.INFO
):
    config = {
        'version': 1,
        'formatters': {
            'syslog-formatter': {
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
        'handlers': {
            'stderr': {
                'level': logging._levelToName[stderr_level],
                'formatter': 'stderr-formatter',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stderr'
            },
            'syslog': {
                'level': logging._levelToName[syslog_level],
                'formatter': 'syslog-formatter',
                'class': 'logging.handlers.NTEventLogHandler',
                'appname': 'eventum-core'
            } if platform.system() == 'Windows' else {
                'level': logging._levelToName[syslog_level],
                'formatter': 'syslog-formatter',
                'class': 'logging.handlers.SysLogHandler',
                'address': '/dev/log'
            }
        },
        'loggers': {
            'eventum_cli': {
                'handlers': ['syslog', 'stderr'],
                'level': 'INFO',
            },
            '__main__': {
                'handlers': ['syslog', 'stderr'],
                'level': 'INFO',
            },
            'eventum_core': {
                'handlers': ['syslog', 'stderr'],
                'level': 'INFO',
            },
            'eventum_plugins': {
                'handlers': ['syslog', 'stderr'],
                'level': 'INFO',
            },
            'eventum_content_manager': {
                'handlers': ['syslog', 'stderr'],
                'level': 'INFO',
            },
        }
    }

    logging.config.dictConfig(config=config)
