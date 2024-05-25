from datetime import datetime

import pytest
from freezegun import freeze_time
from numpy import datetime64
from pydantic import ValidationError
from pytz import timezone

from eventum_plugins.input.sample import SampleInputConfig, SampleInputPlugin


def test_valid_config():
    SampleInputConfig(count=1)


def test_invalid_config():
    with pytest.raises(ValidationError):
        SampleInputConfig(count=0)


def test_sample():
    config = SampleInputConfig(count=100)
    plugin = SampleInputPlugin(config=config, tz=timezone('UTC'))

    events = []

    with freeze_time('2024-01-01T00:00:00.000Z', tz_offset=0):
        plugin.sample(on_event=events.append)

    assert len(events) == 100
    assert events[0] == events[-1] == datetime64(
        datetime.fromisoformat('2024-01-01T00:00:00.000')
    )
