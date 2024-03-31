from datetime import datetime, UTC
from numpy import datetime64, timedelta64, float64


def utcnow() -> datetime64:
    """Get current time in UTC timezone."""
    return datetime64(datetime.now(UTC).replace(tzinfo=None))


def timedelta_to_seconds(delta: timedelta64) -> float64:
    """Convert numpy `timedelta64` to floating point number that
    represents seconds.
    """
    return delta / timedelta64(1000000, 'us')
