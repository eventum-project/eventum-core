from typing import Annotated

import dateparser
from pydantic import AfterValidator


def _try_parse_datetime(v: str) -> str:
    if dateparser.parse(v) is None:
        raise ValueError(f'Not valid datetime expression "{v}"')

    return v


HumanDatetimeString = Annotated[str, AfterValidator(_try_parse_datetime)]
