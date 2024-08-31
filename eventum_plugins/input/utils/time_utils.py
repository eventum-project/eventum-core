from datetime import datetime

from numpy import datetime64, timedelta64
from pytz import BaseTzInfo


def now64(tz: BaseTzInfo) -> datetime64:
    """Get current time in specified timezone as `datetime64`."""
    return datetime64(datetime.now().astimezone(tz).replace(tzinfo=None))


def timedelta64_to_seconds(delta: timedelta64) -> float:
    """Convert numpy `timedelta64` to floating point number that
    represents seconds.
    """
    return float(delta / timedelta64(1000000, 'us'))


def to_naive(timestamp: datetime, tz: BaseTzInfo) -> datetime:
    """Convert datetime to naive format for specified timezone. If
    datetime object is naive then it's returned without any conversion.
    """
    return (
        timestamp.astimezone(tz).replace(tzinfo=None)
        if timestamp.tzinfo else timestamp
    )
