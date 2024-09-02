from datetime import datetime, timedelta

import pytest
from numpy import datetime64, timedelta64
from pytz import timezone

from eventum_plugins.input.enums import TimeMode
from eventum_plugins.input.plugins.timer.config import TimerInputPluginConfig
from eventum_plugins.input.plugins.timer.plugin import TimerInputPlugin


@pytest.mark.timeout(1)
def test_timer_sample():
    start = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone('UTC'))

    plugin = TimerInputPlugin(
        config=TimerInputPluginConfig(
            start=start,
            seconds=1.0,
            count=3,
            repeat=86400
        ),
        id=1,
        mode=TimeMode.SAMPLE,
        timezone=timezone('UTC')
    )

    timestamps = []
    for batch in plugin.generate():
        timestamps.extend(batch)

    assert len(timestamps) == (86400 * 3)
    assert timestamps[0] == datetime64('2024-01-01T00:00:01')
    assert timestamps[-1] == datetime64('2024-01-02T00:00:00')


@pytest.mark.timeout(1)
def test_timer_live():
    now = datetime.now(tz=timezone('UTC'))
    expected_end = now + timedelta(seconds=0.5)
    plugin = TimerInputPlugin(
        config=TimerInputPluginConfig(
            start='now',
            seconds=0.1,
            count=1,
            repeat=5
        ),
        id=1,
        mode=TimeMode.LIVE,
        timezone=timezone('UTC')
    )
    timestamps = []
    for batch in plugin.generate():
        timestamps.extend(batch)

    assert len(timestamps) == 5
    assert (
        datetime64(expected_end.replace(tzinfo=None))
        - timestamps[-1]
    ) < timedelta64(100, 'ms')
