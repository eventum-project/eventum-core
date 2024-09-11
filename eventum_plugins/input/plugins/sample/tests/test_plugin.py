import pytest
from pytz import timezone

from eventum_plugins.input.enums import TimeMode
from eventum_plugins.input.plugins.sample.config import SampleInputPluginConfig
from eventum_plugins.input.plugins.sample.plugin import SampleInputPlugin


@pytest.mark.timeout(1)
def test_sample_sample():
    config = SampleInputPluginConfig(count=100)
    plugin = SampleInputPlugin(
        config=config,
        timezone=timezone('UTC'),
        mode=TimeMode.SAMPLE,
        id=1
    )

    timestamps = []
    for batch in plugin.generate():
        timestamps.extend(batch)

    assert len(timestamps) == 100
    assert timestamps[0] == timestamps[-1]


@pytest.mark.timeout(1)
def test_sample_live():
    config = SampleInputPluginConfig(count=100)
    plugin = SampleInputPlugin(
        config=config,
        timezone=timezone('UTC'),
        mode=TimeMode.LIVE,
        id=1
    )

    timestamps = []
    for batch in plugin.generate():
        timestamps.extend(batch)

    assert len(timestamps) == 100
    assert timestamps[0] == timestamps[-1]
