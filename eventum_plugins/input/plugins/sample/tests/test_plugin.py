from pytz import timezone

from eventum_plugins.input.plugins.sample.config import SampleInputPluginConfig
from eventum_plugins.input.plugins.sample.plugin import SampleInputPlugin


def test_sample_sample():
    config = SampleInputPluginConfig(count=100)
    plugin = SampleInputPlugin(
        config=config,
        timezone=timezone('UTC'),
        live_mode=False,
        id='test'
    )

    timestamps = []
    for batch in plugin.generate():
        timestamps.extend(batch)

    assert len(timestamps) == 100
    assert timestamps[0] == timestamps[-1]


def test_sample_live():
    config = SampleInputPluginConfig(count=100)
    plugin = SampleInputPlugin(
        config=config,
        timezone=timezone('UTC'),
        live_mode=True,
        id='test'
    )

    timestamps = []
    for batch in plugin.generate():
        timestamps.extend(batch)

    assert len(timestamps) == 100
    assert timestamps[0] == timestamps[-1]
