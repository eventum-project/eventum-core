from typing import Annotated

import dateparser
from pydantic import AfterValidator

from eventum_plugins.input.relative_time import parse_relative_time


def _try_parse_human_datetime(v: str) -> str:
    if dateparser.parse(v) is None:
        raise ValueError(f'Not valid datetime expression "{v}"')

    return v


HumanDatetimeString = Annotated[str, AfterValidator(_try_parse_human_datetime)]


def _try_parse_relative_time(v: str) -> str:
    try:
        parse_relative_time(v)
        return v
    except ValueError:
        raise ValueError(f'Not valid relative time expression "{v}"')


RelativeTimeString = Annotated[str, AfterValidator(_try_parse_relative_time)]
