from datetime import datetime


def get_future_slice(
    timestamps: list[datetime],
    now: datetime
) -> list[datetime]:
    """Get slice of timestamps after the `now` using binary search."""
    left = 0
    right = len(timestamps) - 1

    while (right - left) >= 1:
        middle = (left + right) // 2
        if timestamps[middle] <= now:
            left = middle + 1
        else:
            right = middle - 1

    return timestamps[left:-1]
