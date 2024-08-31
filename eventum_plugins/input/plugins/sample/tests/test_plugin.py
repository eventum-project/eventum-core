from pytz import timezone

from eventum_plugins.input.enums import TimeMode
from eventum_plugins.input.plugins.sample.plugin import SampleInputPlugin
from eventum_plugins.input.plugins.sample.config import SampleInputPluginConfig


def test_sample_sample():
    config = SampleInputPluginConfig(count=100)
    plugin = SampleInputPlugin(
        config=config,
        timezone=timezone('UTC'),
        mode=TimeMode.SAMPLE,
        id=1
    )

    events = []
    for batch in plugin.generate():
        events.extend(batch)

    assert len(events) == 100
    assert events[0] == events[-1]


def test_sample_live():
    config = SampleInputPluginConfig(count=100)
    plugin = SampleInputPlugin(
        config=config,
        timezone=timezone('UTC'),
        mode=TimeMode.LIVE,
        id=1
    )

    events = []
    for batch in plugin.generate():
        events.extend(batch)

    assert len(events) == 100
    assert events[0] == events[-1]
