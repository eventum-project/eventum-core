from enum import IntEnum
from typing import assert_never


class ExitCode(IntEnum):
    SUCCESS = 0
    UNEXPECTED_ERROR = 1
    CONFIG_ERROR = 2
    PLUGIN_ERROR = 3


def get_exit_code_description(code: ExitCode) -> str:
    """Get description of exit code.

    Parameters
    ----------
    code : ExitCode
        Exit code to get description for

    Returns
    -------
    str
        Description of exit code
    """
    match code:
        case ExitCode.SUCCESS:
            return 'Exited successfully'
        case ExitCode.UNEXPECTED_ERROR:
            return 'Unexpected error occurred'
        case ExitCode.CONFIG_ERROR:
            return 'Failed to load generator configuration'
        case ExitCode.PLUGIN_ERROR:
            return 'Failed to initialize plugins'
        case v:
            assert_never(v)
