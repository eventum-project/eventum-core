from typing import Iterable

from pydantic_core import ErrorDetails


def prettify_errors(errors: list[ErrorDetails]) -> str:
    """Format pydantic dictionary gotten from `e.errors()` to pretty
    human readable string."""

    def _loc(location: Iterable[str | int]) -> str:
        """Format field location."""
        return '.'.join(map(str, location))

    messages: list[str] = []

    for error in errors:
        match error:
            case {'type': 'extra_forbidden', 'loc': loc}:
                msg = 'Field is unrecognized'
                messages.append(f'Field \"{_loc(loc)}\" - {msg}')
            case {'msg': msg, 'loc': loc}:
                messages.append(f'Field \"{_loc(loc)}\" - {msg}')

    return '; '.join(messages)
