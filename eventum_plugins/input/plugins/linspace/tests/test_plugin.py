from datetime import datetime, timedelta

import pytest
from numpy import datetime64
from pytz import timezone

from eventum_plugins.input.plugins.linspace.config import \
    LinspaceInputPluginConfig
from eventum_plugins.input.plugins.linspace.plugin import LinspaceInputPlugin


@pytest.mark.timeout(1)
@pytest.mark.parametrize(
    ('start', 'end', 'count', 'endpoint', 'expected'),
    [
        ('2024-01-01T00:00:00.000Z', '2024-01-01T00:00:03.000Z', 3, False, [
            datetime64('2024-01-01T00:00:00.000'),
            datetime64('2024-01-01T00:00:01.000'),
            datetime64('2024-01-01T00:00:02.000'),
        ]),
        ('2024-01-01T00:00:00.000Z', '2024-01-01T00:00:01.000Z', 5, True, [
            datetime64('2024-01-01T00:00:00.000'),
            datetime64('2024-01-01T00:00:00.250'),
            datetime64('2024-01-01T00:00:00.500'),
            datetime64('2024-01-01T00:00:00.750'),
            datetime64('2024-01-01T00:00:01.000'),
        ]),
    ]
)
def test_linspace_sample(start, end, count, endpoint, expected):
    config = LinspaceInputPluginConfig(
        start=datetime.fromisoformat(start),
        end=datetime.fromisoformat(end),
        count=count,
        endpoint=endpoint
    )

    plugin = LinspaceInputPlugin(
        config=config,
        timezone=timezone('UTC'),
        live_mode=False,
        id='test'
    )

    timestamps = []
    for batch in plugin.generate():
        timestamps.extend(batch)

    assert timestamps == expected


@pytest.mark.timeout(1)
def test_linspace_live():
    start = datetime.now(tz=timezone('UTC'))
    end = start + timedelta(microseconds=500)
    config = LinspaceInputPluginConfig(
        start=start,
        end=end,
        count=100,
        endpoint=True
    )

    plugin = LinspaceInputPlugin(
        config=config,
        timezone=timezone('UTC'),
        live_mode=False,
        id='test'
    )

    timestamps = []
    for batch in plugin.generate():
        timestamps.extend(batch)

    assert len(timestamps) <= 100
    assert timestamps[-1] == datetime64(end.replace(tzinfo=None))
    assert timestamps[0] >= datetime64(start.replace(tzinfo=None))
