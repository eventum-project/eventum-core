import numpy as np

from eventum_plugins.utils.arrays import chunk_array


def test_chunk_array():
    arr = np.array(list(range(1001)))
    chunks = chunk_array(arr, 100)

    assert len(chunks) == 11
    assert chunks[0][0] == 0 and chunks[9][99] == 999
    assert chunks[-1][0] == 1000
    assert len(chunks[0]) == 100 and len(chunks[-1]) == 1

    arr[0] = -1
    assert chunks[0][0] == -1
