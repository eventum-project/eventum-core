from numpy import datetime64
from numpy.typing import NDArray


def _find_nearest_timestamp(
    timestamps: NDArray[datetime64],
    target: datetime64
) -> int:
    """Find index of nearest timestamps to `target` using binary
    search. Raise `ValueError` if timestamps array is empty."""
    length = len(timestamps)

    if length == 0:
        raise ValueError('Empty array of timestamps')

    left = 0
    right = length - 1

    while left <= right:
        middle = (left + right) // 2
        if timestamps[middle] <= target:
            left = middle + 1
        else:
            right = middle - 1

    return left


def get_future_slice(
    timestamps: NDArray[datetime64],
    after: datetime64
) -> NDArray[datetime64]:
    """Get slice of timestamps `after` the moment using binary search."""
    length = len(timestamps)

    if length == 0:
        return timestamps

    if timestamps[-1] <= after:
        return timestamps[length:]
    elif after < timestamps[0]:
        return timestamps

    index = _find_nearest_timestamp(timestamps, after)
    return timestamps[index:]


def get_past_slice(
    timestamps: NDArray[datetime64],
    before: datetime64
) -> NDArray[datetime64]:
    """Get slice of timestamps `before` the moment using binary search."""
    length = len(timestamps)

    if length == 0:
        return timestamps

    if timestamps[-1] <= before:
        return timestamps
    elif before < timestamps[0]:
        return timestamps[:0]

    index = _find_nearest_timestamp(timestamps, before)
    return timestamps[:index]
