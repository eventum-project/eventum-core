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


def chunk_array(array: NDArray, size: int) -> list[NDArray]:
    """Split array inti chunks with size `chunk_size`. Last chunk size
    can be smaller than `chunk_size`. Chunks are slices of original
    array.
    """
    return [array[i:i + size] for i in range(0, array.size, size)]
