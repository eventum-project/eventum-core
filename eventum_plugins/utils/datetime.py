from datetime import datetime

from pytz import BaseTzInfo


def convert_to_naive(timestamp: datetime, tz: BaseTzInfo) -> datetime:
    """Convert datetime object to naive format."""
    return (
        timestamp.astimezone(tz=tz).replace(tzinfo=None)
        if timestamp.tzinfo else timestamp
    )
