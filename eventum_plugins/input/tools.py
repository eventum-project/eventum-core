from datetime import datetime

import dateparser
from pytz import BaseTzInfo

from eventum_plugins.input.fields import (HumanDatetimeString,
                                          RelativeTimeString)
from eventum_plugins.input.relative_time import parse_relative_time


def normalize_daterange(
    start: datetime | RelativeTimeString | HumanDatetimeString | None,
    end: datetime | RelativeTimeString | HumanDatetimeString | None,
    timezone: BaseTzInfo
) -> tuple[datetime, datetime]:
    """Normalize date range for specified start and end parameters.
    Parameter values can be of type `datetime`, `str` or `None`. In
    case of value is `None` in start param - current time is used, in
    end param - "never" (maximum datetime value) is used. In case of
    value is of type `str`, it should represent human readable datetime
    or relative time that can be parsed. Furthermore start datetime is
    used as relative base for end param expression parsing. In case of
    value is of type `datetime`, it is only converted to the specified
    timezone. Types of start and end params can be different from each
    other within one function call.

    Parameters
    ----------
    start : datetime | RelativeTimeString | HumanDatetimeString | None
        Start of the date range

    end : datetime | RelativeTimeString | HumanDatetimeString | None
        End of the date range

    timezone : BaseTzInfo
        Timezone that is used for datetime objects of date range

    Returns
    -------
    tuple[datetime, datetime]
        Start and end of the daterange as a tuple
    """
    match start:
        case datetime():
            start_time = start.astimezone(timezone)
        case str():
            try:
                timedelta = parse_relative_time(start)
                start_time = datetime.now(tz=timezone) + timedelta
            except ValueError:
                start_time = dateparser.parse(
                    start,
                    settings={                      # type: ignore[arg-type]
                        'TIMEZONE': timezone.zone,
                        'RETURN_AS_TIMEZONE_AWARE': True
                    }
                )
                assert isinstance(start_time, datetime)
        case _:
            start_time = datetime.now(tz=timezone)

    match end:
        case datetime():
            end_time = end.astimezone(timezone)
        case str():
            try:
                timedelta = parse_relative_time(end)
                end_time = start_time + timedelta
            except ValueError:
                end_time = dateparser.parse(
                    end,
                    settings={                      # type: ignore[arg-type]
                        'RELATIVE_BASE': start_time,
                        'TIMEZONE': timezone.zone,
                        'RETURN_AS_TIMEZONE_AWARE': True

                    }
                )
            assert isinstance(end_time, datetime)
        case _:
            end_time = datetime.max.replace(tzinfo=timezone)

    return (start_time, end_time)
