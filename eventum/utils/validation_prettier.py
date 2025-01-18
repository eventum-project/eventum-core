from typing import Iterable

from pydantic_core import ErrorDetails


def prettify_validation_errors(errors: Iterable[ErrorDetails]) -> str:
    """Prettify pydantic validation errors gotten from
    `e.errors()` to user-friendly description string.

    Parameters
    ----------
    errors : Iterable[ErrorDetails]
        Iterable of error details

    Returns
    -------
    str
        User-friendly description of errors
    """

    def _loc(location: Iterable[str | int]) -> str:
        return '.'.join(map(str, location))

    messages: list[str] = []

    for error in errors:
        match error:
            case {'type': 'extra_forbidden', 'loc': loc}:
                msg = 'Unknown field'
                messages.append(f'Field \"{_loc(loc)}\" - {msg}')
            case {'msg': msg, 'loc': loc}:
                messages.append(f'Field \"{_loc(loc)}\" - {msg}')

    return '; '.join(messages)
