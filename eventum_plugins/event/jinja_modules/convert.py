import datetime as dt


def to_datetime(timestamp: str) -> dt.datetime:
    """Return datetime object parsed from ISO8601 timestamp string."""
    return dt.datetime.fromisoformat(timestamp)
