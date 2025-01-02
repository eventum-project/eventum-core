import numpy as np

from eventum.plugins.input.utils.array_utils import (chunk_array,
                                                     get_future_slice,
                                                     get_past_slice,
                                                     merge_arrays)


def test_get_future_slice():
    start = np.datetime64('now')
    timestamps = np.array([start + np.timedelta64(i, 's') for i in range(100)])

    # <  - after moment
    # *  - timestamp
    # [] - returned slice

    # *****<[*****]
    after_moment = timestamps[50]
    slice = get_future_slice(timestamps, after_moment)
    assert slice[0] == timestamps[51]

    # <[*****]
    same_slice = get_future_slice(slice, after_moment)
    assert same_slice[0] == slice[0]

    # *****<[]
    future_moment = slice[-1] + np.timedelta64(1, 's')
    empty_slice = get_future_slice(slice, future_moment)
    assert len(empty_slice) == 0


def test_get_past_slice():
    start = np.datetime64('now')
    before_start = start - np.timedelta64(1, 's')
    timestamps = np.array([start + np.timedelta64(i, 's') for i in range(100)])

    # <  - after moment
    # *  - timestamp
    # [] - returned slice

    # [*****]<*****
    before_moment = timestamps[50]
    slice = get_past_slice(timestamps, before_moment)
    assert slice[-1] == timestamps[50]

    # []<*****
    empty_slice = get_past_slice(slice, before_start)
    assert len(empty_slice) == 0

    # [*****]<
    same_slice = get_past_slice(slice, timestamps[50])
    assert same_slice[-1] == slice[-1]


def test_chunking_array():
    arr = np.array(list(range(1050)))
    chunks = chunk_array(arr, 100)

    assert len(chunks) == 11
    assert all([len(chunk) == 100 for chunk in chunks[:-1]])
    assert len(chunks[-1]) == 50

    assert np.array_equal(arr, np.concatenate(chunks))


def test_chunking_even_array():
    arr = np.array(list(range(1000)))
    chunks = chunk_array(arr, 100)

    assert len(chunks) == 10
    assert all([len(chunk) == 100 for chunk in chunks])
    assert np.array_equal(arr, np.concatenate(chunks))


def test_chunking_empty_array():
    arr = np.array([])
    chunks = chunk_array(arr, 100)

    assert len(chunks) == 0


def test_chunks_allocation():
    arr = np.array(list(range(100)))
    chunks = chunk_array(arr, 10)

    arr[0] = -1
    assert chunks[0][0] == -1


def test_merge_arrays():
    arrays = []

    values = set()
    for _ in range(10):
        arr = np.random.uniform(0, 1000, 1000)
        values |= set(arr)
        arrays.append(arr)

    result = merge_arrays(arrays)

    assert result.size == 10_000
    assert set(result) == set(values)
    assert np.all(result[:-1] <= result[1:])
