import numpy as np

from eventum_plugins.utils.timeseries import get_future_slice


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
