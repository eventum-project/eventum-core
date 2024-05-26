from datetime import datetime

import pytest
from freezegun import freeze_time
from numpy import datetime64
from pydantic import ValidationError
from pytz import timezone

from eventum_plugins.input.timer import TimerInputConfig, TimerInputPlugin


def test_valid_config():
    TimerInputConfig(seconds=1, count=1, repeat=True)


def test_invalid_config():
    with pytest.raises(ValidationError):
        TimerInputConfig(seconds=0, count=1, repeat=True)


def test_timer_live():
    config = TimerInputConfig(seconds=0.125, count=1, repeat=False)
    plugin = TimerInputPlugin(config=config, tz=timezone('UTC'))

    events = []

    with freeze_time('2024-01-01T00:00:00.000Z', tz_offset=0):
        plugin.live(on_event=events.append)

    assert events.pop() == datetime64(
        datetime.fromisoformat('2024-01-01T00:00:00.125')
    )
