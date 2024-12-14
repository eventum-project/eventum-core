from pytz import timezone

from eventum_plugins.input.plugins.static.config import StaticInputPluginConfig
from eventum_plugins.input.plugins.static.plugin import StaticInputPlugin


def test_static_sample():
    config = StaticInputPluginConfig(count=100)
    plugin = StaticInputPlugin(
        config=config,
        params={
            'id': 1,
            'live_mode': False,
            'timezone': timezone('UTC')
        }
    )

    timestamps = []
    for batch in plugin.generate():
        timestamps.extend(batch)

    assert len(timestamps) == 100
    assert timestamps[0] == timestamps[-1]


def test_static_live():
    config = StaticInputPluginConfig(count=100)
    plugin = StaticInputPlugin(
        config=config,
        params={
            'id': 1,
            'live_mode': True,
            'timezone': timezone('UTC')
        }
    )

    timestamps = []
    for batch in plugin.generate():
        timestamps.extend(batch)

    assert len(timestamps) == 100
    assert timestamps[0] == timestamps[-1]
