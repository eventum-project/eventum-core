from numpy import datetime64
from numpy.typing import NDArray


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

    left = 0
    right = length - 1

    while left <= right:
        middle = (left + right) // 2
        if timestamps[middle] <= after:
            left = middle + 1
        else:
            right = middle - 1

    return timestamps[left:]
