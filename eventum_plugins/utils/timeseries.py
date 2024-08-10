from numpy import datetime64, searchsorted
from numpy.typing import NDArray


def get_future_slice(
    timestamps: NDArray[datetime64],
    after: datetime64
) -> NDArray[datetime64]:
    """Get slice of timestamps `after` the moment using binary search."""
    index = searchsorted(a=timestamps, v=after, side='right')
    return timestamps[index:]


def get_past_slice(
    timestamps: NDArray[datetime64],
    before: datetime64
) -> NDArray[datetime64]:
    """Get slice of timestamps `before` the moment using binary search."""
    index = searchsorted(a=timestamps, v=before, side='right')
    return timestamps[:index]
