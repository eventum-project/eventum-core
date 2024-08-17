from datetime import datetime

from numpy import datetime64, float64, timedelta64
from pytz import BaseTzInfo


def get_now(tz: BaseTzInfo) -> datetime64:
    """Get current datetime in specified timezone."""
    return datetime64(datetime.now(tz).replace(tzinfo=None))


def timedelta_to_seconds(delta: timedelta64) -> float64:
    """Convert numpy `timedelta64` to floating point number that
    represents seconds.
    """
    return delta / timedelta64(1000000, 'us')


def localize(timestamp: datetime, tz: BaseTzInfo) -> datetime:
    """Convert datetime to naive format for specified timezone. If
    datetime object is naive then it's returned without any conversion.
    """
    return (
        timestamp.astimezone(tz=tz).replace(tzinfo=None)
        if timestamp.tzinfo else timestamp
    )
