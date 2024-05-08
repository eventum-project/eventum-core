from datetime import datetime, timedelta

import pytest

from eventum.core.plugins.input.base import InputPluginConfigurationError
from eventum.core.plugins.input.timestamps import TimestampsInputPlugin


def test_sample_mode():
    now = datetime.now()
    timestamps = [now + timedelta(milliseconds=i) for i in range(100)]

    out = []
    TimestampsInputPlugin(timestamps=timestamps).sample(on_event=out.append)

    assert len(out) == len(timestamps)


def test_live_mode():
    now = datetime.now().astimezone() + timedelta(milliseconds=100)
    timestamps = [now + timedelta(milliseconds=i) for i in range(100)]

    out = []
    TimestampsInputPlugin(timestamps=timestamps).live(on_event=out.append)

    assert len(out) == len(timestamps)


def test_improper_configuration():
    with pytest.raises(InputPluginConfigurationError):
        TimestampsInputPlugin(timestamps=[])
