from datetime import datetime

import pytz
from numpy import datetime64, timedelta64

from eventum_plugins.input.utils.time_utils import (now64,
                                                    timedelta64_to_seconds,
                                                    to_naive)


def test_now64():
    tz = pytz.timezone('Europe/Moscow')
    now = datetime.now().astimezone(tz).replace(tzinfo=None)

    expected = datetime64(now, 'us')
    result = now64(timezone=tz)

    assert 0 <= ((result - expected) / timedelta64(1000000, 'us')) < 0.5


def test_timedelta64_to_seconds():
    assert timedelta64_to_seconds(timedelta64(125, 'ms')) == 0.125


def test_to_naive():
    timestamp = datetime(2024, 1, 1, 0, 0, 0, tzinfo=pytz.timezone('UTC'))
    result = to_naive(timestamp, timezone=pytz.timezone('Europe/Moscow'))

    assert result == datetime64(
        timestamp.astimezone(
            pytz.timezone('Europe/Moscow')
        ).replace(tzinfo=None)
    )
