import os
import tempfile
from datetime import datetime, timedelta

import pytest
from numpy import datetime64
from pytz import timezone

from eventum_plugins.input.plugins.timestamps.config import \
    TimestampsInputPluginConfig
from eventum_plugins.input.plugins.timestamps.plugin import \
    TimestampsInputPlugin


@pytest.mark.timeout(1)
def test_timestamps_sample():
    config = TimestampsInputPluginConfig(
        source=(
            datetime.fromisoformat('2024-01-01T00:00:00.000Z'),
            datetime.fromisoformat('2024-01-01T00:00:00.050Z'),
            datetime.fromisoformat('2024-01-01T00:00:00.100Z'),
        )
    )
    plugin = TimestampsInputPlugin(
        config=config,
        timezone=timezone('UTC'),
        id='test',
        live_mode=False
    )
    timestamps = []
    for batch in plugin.generate():
        timestamps.extend(batch)

    assert timestamps == [
        datetime64('2024-01-01T00:00:00.000'),
        datetime64('2024-01-01T00:00:00.050'),
        datetime64('2024-01-01T00:00:00.100'),
    ]


@pytest.mark.timeout(1)
def test_timestamps_live():
    now = datetime.now(tz=timezone('UTC'))
    config = TimestampsInputPluginConfig(
        source=[
            now + timedelta(seconds=0.3),
            now + timedelta(seconds=0.4),
            now + timedelta(seconds=0.5)
        ]
    )
    plugin = TimestampsInputPlugin(
        config=config,
        timezone=timezone('UTC'),
        id='test',
        live_mode=True
    )

    timestamps = []

    for batch in plugin.generate():
        timestamps.extend(batch)

    assert timestamps == [
        datetime64((now + timedelta(seconds=0.3)).replace(tzinfo=None)),
        datetime64((now + timedelta(seconds=0.4)).replace(tzinfo=None)),
        datetime64((now + timedelta(seconds=0.5)).replace(tzinfo=None)),
    ]


@pytest.fixture
def timestamps_filename():
    filename = tempfile.mktemp()
    with open(filename, 'w') as f:
        f.write(f'2024-01-01T00:00:00.000{os.linesep}')
        f.write(f'2024-01-01T00:00:00.050{os.linesep}')
        f.write(f'2024-01-01T00:00:00.100{os.linesep}')

    return filename


@pytest.mark.timeout(1)
def test_timestamps_from_file(timestamps_filename):
    config = TimestampsInputPluginConfig(source=timestamps_filename)
    plugin = TimestampsInputPlugin(
        config=config,
        timezone=timezone('UTC'),
        id='test',
        live_mode=False
    )

    timestamps = []
    for batch in plugin.generate():
        timestamps.extend(batch)

    assert timestamps == [
        datetime64('2024-01-01T00:00:00.000'),
        datetime64('2024-01-01T00:00:00.050'),
        datetime64('2024-01-01T00:00:00.100'),
    ]
