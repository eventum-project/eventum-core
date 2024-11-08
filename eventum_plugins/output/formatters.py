from enum import StrEnum
import json
from typing import assert_never


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
