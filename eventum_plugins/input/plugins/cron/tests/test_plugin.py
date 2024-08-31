from datetime import datetime

import pytest
from numpy import datetime64
from pytz import timezone

from eventum_plugins.input.enums import TimeMode
from eventum_plugins.input.plugins.cron.config import CronInputPluginConfig
from eventum_plugins.input.plugins.cron.plugin import CronInputPlugin


@pytest.mark.timeout(1)
def test_cron_sample():
    plugin = CronInputPlugin(
        id=1,
        config=CronInputPluginConfig(
            expression='* * * * *',
            count=1,
            start=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone('UTC')),
            end=datetime(2024, 1, 1, 23, 59, 59, tzinfo=timezone('UTC'))
        ),
        mode=TimeMode.SAMPLE,
        timezone=timezone('UTC')
    )

    events = []

    for batch in plugin.generate():
        events.extend(batch)

    assert len(events) == 1440
    assert events[0] == datetime64('2024-01-01T00:00:00')
    assert events[-1] == datetime64('2024-01-01T23:59:00')


@pytest.mark.timeout(5)
def test_cron_live():
    now = datetime.now(tz=timezone('UTC'))
    start = now.replace(microsecond=now.microsecond + 500)
    plugin = CronInputPlugin(
        id=1,
        config=CronInputPluginConfig(
            expression='* * * * * *',
            count=1,
            start=start,
            end='after 2 seconds'
        ),
        mode=TimeMode.LIVE,
        timezone=timezone('UTC')
    )

    events = []

    for batch in plugin.generate():
        events.extend(batch)

    assert len(events) == 2
    assert events[0] == datetime64(
        start.replace(second=start.second + 1, microsecond=0, tzinfo=None)
    )
    assert events[-1] == datetime64(
        start.replace(second=start.second + 2, microsecond=0, tzinfo=None)
    )
