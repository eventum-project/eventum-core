from datetime import datetime
from typing import Literal, TypeAlias, assert_never

import dateparser
from pytz import BaseTzInfo

from eventum.plugins.input.fields import TimeKeyword, VersatileDatetime
from eventum.plugins.input.relative_time import parse_relative_time

NonePoint: TypeAlias = Literal['now', 'min', 'max']


def normalize_versatile_datetime(
    value: VersatileDatetime,
    timezone: BaseTzInfo,
    relative_base: datetime | None = None,
    none_point: NonePoint = 'now',
) -> datetime:
    """Normalize value representing datetime.

    Parameters
    ----------
    value : VersatileDatetime
        Value to normalize

    timezone : BaseTzInfo
        Timezone that is used for returned datetime object

    relative_base : datetime | None
        Base time to use when value represents relative time, default
        is current time

    none_point : NonePoint, default='now'
        What time to use when `value` parameter is `None`: 'now' -
        current time; `min` - minimal value of datetime; `max` -
        maximal value of datetime

    Returns
    -------
    datetime
        Normalized value as datetime object in specified timezone

    Raises
    ------
    ValueError
        If provided value cannot be parsed as datetime objects

    OverflowError
        If resulting datetime value is overflowed for specified timezone
    """
    now = datetime.now().astimezone(timezone)
    relative_base = relative_base or now

    min = now.replace(
        year=1, month=1, day=1,
        hour=0, minute=0, second=0, microsecond=0
    )

    max = now.replace(
        year=9999, month=12, day=31,
        hour=23, minute=59, second=59, microsecond=999998   # 8 is for croniter
    )

    match value:
        case datetime():
            time = value.astimezone(timezone)
        case str():
            try:
                keyword = TimeKeyword(value)
            except ValueError:
                try:
                    delta = parse_relative_time(value)
                    time = relative_base + delta
                except ValueError:
                    parsed_time = dateparser.parse(
                        value,
                        settings={
                            'RELATIVE_BASE': relative_base,
                            'TIMEZONE': timezone._tzname or 'UTC',
                            'RETURN_AS_TIMEZONE_AWARE': True
                        }
                    )
                    if parsed_time is None:
                        raise ValueError(
                            f'Cannot parse expression "{value}"'
                        ) from None

                    time = parsed_time
            else:
                match keyword:
                    case TimeKeyword.NOW:
                        time = now
                    case TimeKeyword.NEVER:
                        time = max
                    case v:
                        assert_never(v)
        case _:
            match none_point:
                case 'now':
                    time = now
                case 'min':
                    time = min
                case 'max':
                    time = max
                case x_none_point:
                    assert_never(x_none_point)

    return time


NoneStartPoint: TypeAlias = Literal['now', 'min']
NoneEndPoint: TypeAlias = Literal['now', 'max']


def normalize_versatile_daterange(
    start: VersatileDatetime,
    end: VersatileDatetime,
    timezone: BaseTzInfo,
    none_start: NoneStartPoint = 'min',
    none_end: NoneEndPoint = 'max'
) -> tuple[datetime, datetime]:
    """Normalize date range for specified start and end parameters.

    Parameters
    ----------
    start : VersatileDatetime
        Start of the date range, used as relative base for `end`

    end : VersatileDatetime
        End of the date range

    timezone : BaseTzInfo
        Timezone that is used for returned datetime objects

    none_start : NoneStartPoint, default='min'
        What time to use when `start` parameter is `None`: 'now' -
        current time; `min` - minimal value of datetime;

    none_end : NoneStartPoint, default='max'
        What time to use when `end` parameter is `None`: 'now' -
        current time; `max` - maximal value of datetime;

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

    OverflowError
        If some of the resulting datetime values are overflowed for
        specified timezone
    """
    if start == TimeKeyword.NEVER.value:
        raise ValueError(f'Start time cannot be "{TimeKeyword.NEVER}"')

    try:
        start = normalize_versatile_datetime(
            value=start,
            timezone=timezone,
            none_point=none_start
        )
    except ValueError as e:
        raise ValueError(f'Cannot parse start time: {e}') from None

    try:
        end = normalize_versatile_datetime(
            value=end,
            timezone=timezone,
            relative_base=start,
            none_point=none_end
        )
    except ValueError as e:
        raise ValueError(f'Cannot parse end time: {e}') from None

    if start > end:
        raise ValueError('End time cannot be earlier than start time')

    return (start, end)
