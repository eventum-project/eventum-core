from numpy.typing import NDArray


def chunk_array(array: NDArray, size: int) -> list[NDArray]:
    """Split array inti chunks with size `chunk_size`. Last chunk size
    can be smaller than `chunk_size`. Chunks are slices of original
    array.
    """
    return [array[i:i + size] for i in range(0, array.size, size)]
