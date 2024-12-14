import json
from enum import StrEnum
from typing import Any, Callable, Iterable, assert_never


class Format(StrEnum):
    PLAIN = 'plain'
    NDJSON = 'ndjson'


def format_ndjson(event: str) -> str:
    """Format event to new line delimited json format.

    Parameters
    ----------
    event : str
        Event to format

    Returns
    -------
    str
        Formatted event

    Raises
    ------
    ValueError
        If formatting failed
    """
    try:
        return json.dumps(json.loads(event), ensure_ascii=False)
    except json.JSONDecodeError as e:
        raise ValueError(e) from None


def format_event(event: str, format: Format) -> str:
    """Format event using specified format.

    Parameters
    ----------
    event : str
        Event to format

    format : Format
        Format to use

    Returns
    -------
    str
        Formatted event

    Raises
    ------
    ValueError
        If formatting failed
    """
    match format:
        case Format.PLAIN:
            return event
        case Format.NDJSON:
            return format_ndjson(event)
        case f:
            assert_never(f)


def format_events(
    events: Iterable[str],
    format: Format,
    ignore_errors: bool = False,
    error_callback: Callable[[str, ValueError], Any] | None = None
) -> list[str]:
    """Format events using specified format.

    Parameters
    ----------
    events : Iterable[str]
        Events to format

    format : Format
        Format to use

    ignore_errors : bool, default = False
        Proceed formatting events if error occurred for some event,
        otherwise the first formatting error is propagated

    error_callback : Callable[[str, ValueError], Any] | None = None
        Callback that is called each time formatting error occurs,
        actual only if ignore_errors is `True`, the first parameter
        is the original event and the second one is the exception

    Returns
    -------
    list[str]
        Formatted events

    Raises
    ------
    ValueError
        If formatting fails for some event and `ignore_errors` is `False`
    """
    formatted_events: list[str] = []
    if ignore_errors:
        if error_callback is not None:      # minimize condition checks
            for event in events:
                try:
                    formatted_events.append(format_event(event, format))
                except ValueError as e:
                    error_callback(event, e)
        else:
            for event in events:
                try:
                    formatted_events.append(format_event(event, format))
                except ValueError:
                    pass
    else:
        for event in events:
            formatted_events.append(format_event(event, format))

    return formatted_events
