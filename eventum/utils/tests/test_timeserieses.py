import numpy as np
from eventum.utils.timeseries import get_future_slice


def test_get_future_slice():
    start = np.datetime64('now')
    timestamps = np.array([start + np.timedelta64(i, 's') for i in range(100)])
    now = timestamps[50]

    slice = get_future_slice(timestamps, now)

    assert slice[0] == timestamps[51]
