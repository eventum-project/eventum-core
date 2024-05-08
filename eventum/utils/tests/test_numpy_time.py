import numpy as np

from eventum.utils.numpy_time import timedelta_to_seconds


def test_timedelta_to_seconds():
    seconds = timedelta_to_seconds(np.timedelta64(1234, 'ms'))
    assert seconds == np.float64(1.234)
