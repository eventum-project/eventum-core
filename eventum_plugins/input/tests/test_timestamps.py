import os
import tempfile
from datetime import datetime

import pytest
from freezegun import freeze_time
from numpy import datetime64
from pydantic import ValidationError
from pytz import timezone

from eventum_plugins.input.timestamps import (TimestampsInputConfig,
                                              TimestampsInputPlugin)


def test_valid_config():
    TimestampsInputConfig(
        source=(
            datetime.fromisoformat('2024-01-01T00:00:00.000Z'),
            datetime.fromisoformat('2024-01-01T00:00:00.050Z'),
            datetime.fromisoformat('2024-01-01T00:00:00.100Z'),
        )
    )


def test_invalid_config():
    with pytest.raises(ValidationError):
        TimestampsInputConfig(source=tuple())


def test_timestamps_live():
    config = TimestampsInputConfig(
        source=(
            datetime.fromisoformat('2024-01-01T00:00:00.000Z'),
            datetime.fromisoformat('2024-01-01T00:00:00.500Z'),
            datetime.fromisoformat('2024-01-01T00:00:01.000Z'),
        )
    )
    plugin = TimestampsInputPlugin(config=config, tz=timezone('UTC'))

    events = []

    with freeze_time('2024-01-01T00:00:00.300Z', tz_offset=0, tick=True):
        plugin.live(on_event=events.append)

    assert events == [
        datetime64(datetime.fromisoformat('2024-01-01T00:00:00.500')),
        datetime64(datetime.fromisoformat('2024-01-01T00:00:01.000')),
    ]


def test_timestamps_sample():
    config = TimestampsInputConfig(
        source=(
            datetime.fromisoformat('2024-01-01T00:00:00.000Z'),
            datetime.fromisoformat('2024-01-01T00:00:00.050Z'),
            datetime.fromisoformat('2024-01-01T00:00:00.100Z'),
        )
    )
    plugin = TimestampsInputPlugin(config=config, tz=timezone('UTC'))

    events = []
    plugin.sample(on_event=events.append)

    assert events == [
        datetime64(datetime.fromisoformat('2024-01-01T00:00:00.000')),
        datetime64(datetime.fromisoformat('2024-01-01T00:00:00.050')),
        datetime64(datetime.fromisoformat('2024-01-01T00:00:00.100')),
    ]

@pytest.fixture
def timestamps_filename():
    filename = tempfile.mktemp()
    with open(filename, 'w') as f:
        f.write(f'2024-01-01T00:00:00.000{os.linesep}')
        f.write(f'2024-01-01T00:00:00.050{os.linesep}')
        f.write(f'2024-01-01T00:00:00.100{os.linesep}')

    return filename


def test_timestamps_from_file(timestamps_filename):
    config = TimestampsInputConfig(source=timestamps_filename)
    plugin = TimestampsInputPlugin(config=config, tz=timezone('UTC'))

    events = []
    plugin.sample(on_event=events.append)

    assert events == [
        datetime64(datetime.fromisoformat('2024-01-01T00:00:00.000')),
        datetime64(datetime.fromisoformat('2024-01-01T00:00:00.050')),
        datetime64(datetime.fromisoformat('2024-01-01T00:00:00.100')),
    ]
