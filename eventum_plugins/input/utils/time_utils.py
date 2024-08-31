from datetime import datetime

from numpy import datetime64, timedelta64
from pytz import BaseTzInfo


def now64(timezone: BaseTzInfo) -> datetime64:
    """Get current time in specified timezone as `datetime64`.

    Parameters
    ----------
    timezone : BaseTzInfo
        Timezone for value of `datetime64` object

    Returns
    -------
    datetime64
        Numpy `datetime64` object with current time in specified
        `timezone`
    """
    return datetime64(datetime.now().astimezone(timezone).replace(tzinfo=None))


def timedelta64_to_seconds(timedelta: timedelta64) -> float:
    """Convert numpy `timedelta64` to floating point number that
    represents seconds.

    Parameters
    ----------
    timedelta : timedelta64
        Timedelta to convert

    Returns
    -------
    float
        Floating point number representing number of seconds in
        `timedelta`
    """
    return float(timedelta / timedelta64(1000000, 'us'))


def to_naive(timestamp: datetime, timezone: BaseTzInfo) -> datetime:
    """Convert datetime to naive format for specified timezone. If
    datetime object is naive then it's returned without any conversion.

    Parameters
    ----------
    timestamp : datetime
        Timestamp to convert

    timezone: BaseTzInfo
        Timezone for localization resulting datetime value

    Returns
    -------
    datetime
        Naive datetime object
    """
    return (
        timestamp.astimezone(timezone).replace(tzinfo=None)
        if timestamp.tzinfo else timestamp
    )
