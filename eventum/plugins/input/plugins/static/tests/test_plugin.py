from datetime import datetime

from pytz import timezone

from eventum.plugins.input.plugins.static.config import StaticInputPluginConfig
from eventum.plugins.input.plugins.static.plugin import StaticInputPlugin


def test_plugin():
    config = StaticInputPluginConfig(count=100)
    plugin = StaticInputPlugin(
        config=config,
        params={
            'id': 1,
            'timezone': timezone('UTC')
        }
    )

    now = datetime.now().astimezone(timezone('UTC'))
    timestamps = []
    for batch in plugin.generate():
        timestamps.extend(batch)

    assert len(timestamps) == 100
    assert len(set(timestamps)) == 1

    ts = timezone('UTC').localize(
        datetime.fromisoformat(str(timestamps[0]))
    )
    assert abs((ts - now).total_seconds()) < 1
