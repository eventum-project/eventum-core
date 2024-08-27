from datetime import datetime
from typing import Literal, assert_never

import dateparser
from pytz import BaseTzInfo

from eventum_plugins.input.fields import (HumanDatetimeString,
                                          RelativeTimeString, TimeKeyword,
                                          TimeKeywordString)
from eventum_plugins.input.relative_time import parse_relative_time


def normalize_daterange(
    start: (
        datetime | TimeKeywordString | RelativeTimeString
        | HumanDatetimeString | None
    ),
    end: (
        datetime | TimeKeywordString | RelativeTimeString
        | HumanDatetimeString | None
    ),
    timezone: BaseTzInfo,
    none_start: Literal['now', 'min'] = 'min',
) -> tuple[datetime, datetime]:
    """Normalize date range for specified start and end parameters.

    Parameters
    ----------
    start : datetime | RelativeTimeString | HumanDatetimeString\
        | TimeKeywordString | None
        Start of the date range, used as relative base if `end` is
        relative expression

    end : datetime | RelativeTimeString | HumanDatetimeString\
        | TimeKeywordString | None
        End of the date range

    timezone : BaseTzInfo
        Timezone that is used for returned datetime objects

    none_start : Literal['now', 'min']
        What time to used when `start` parameter is `None`: 'now' -
        current time; `min` - minimal value of datetime;

    Returns
    -------
    tuple[datetime, datetime]
        Normalized start and end of the date range as a tuple in
        specified timezone

    Raises
    ------
    ValueError
        If provided values cannot be parsed as datetime objects or
        date range is improper (e.g. start time is later than end time)
    """
    now = datetime.now(tz=timezone)
    min = datetime.min.replace(tzinfo=timezone)
    max = datetime.max.replace(tzinfo=timezone)

    match start:
        case datetime():
            start_time = start.astimezone(timezone)
        case str():
            try:
                keyword = TimeKeyword(start)
            except ValueError:
                try:
                    timedelta = parse_relative_time(start)
                    start_time = now + timedelta
                except ValueError:
                    start_time = dateparser.parse(
                        start,
                        settings={              # type: ignore[arg-type]
                            'TIMEZONE': timezone.zone,
                            'RETURN_AS_TIMEZONE_AWARE': True
                        }
                    )
                    if start_time is None:
                        raise ValueError(
                            f'Failed to parse expression "{start}" '
                            'in parameter "start"'
                        )
            else:
                match keyword:
                    case TimeKeyword.NOW:
                        start_time = now
                    case TimeKeyword.NEVER:
                        raise ValueError(
                            'Parameter "start" cannot be "never"'
                        )
                    case v:
                        assert_never(v)
        case _:
            match none_start:
                case 'min':
                    start_time = min
                case 'now':
                    start_time = now
                case v:
                    assert_never(v)

    match end:
        case datetime():
            end_time = end.astimezone(timezone)
        case str():
            try:
                keyword = TimeKeyword(end)
            except ValueError:
                try:
                    timedelta = parse_relative_time(end)
                    end_time = start_time + timedelta
                except ValueError:
                    end_time = dateparser.parse(
                        end,
                        settings={                  # type: ignore[arg-type]
                            'RELATIVE_BASE': start_time,
                            'TIMEZONE': timezone.zone,
                            'RETURN_AS_TIMEZONE_AWARE': True

                        }
                    )
                if end_time is None:
                    raise ValueError(
                        f'Failed to parse expression "{end}" '
                        'in parameter "end"'
                    )
            else:
                match keyword:
                    case TimeKeyword.NOW:
                        end_time = now
                    case TimeKeyword.NEVER:
                        end_time = max
                    case v:
                        assert_never(v)
        case _:
            end_time = max

    if start_time > end_time:
        raise ValueError('Start time is later then end time')

    return (start_time, end_time)
