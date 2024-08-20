
from enum import StrEnum


class TimeMode(StrEnum):
    """Possible time modes of timestamps generation by input plugins."""
    SAMPLE = 'sample'
    LIVE = 'live'
