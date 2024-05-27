from datetime import datetime

from numpy import datetime64, float64, timedelta64
from pytz.tzinfo import BaseTzInfo


def get_now(tz: BaseTzInfo) -> datetime64:
    """Get current time in UTC timezone."""
    return datetime64(datetime.now(tz).replace(tzinfo=None))


def timedelta_to_seconds(delta: timedelta64) -> float64:
    """Convert numpy `timedelta64` to floating point number that
    represents seconds.
    """
    return delta / timedelta64(1000000, 'us')
