import numpy as np
from pytz import timezone

from eventum.plugins.input.adapters import IdentifiedTimestampsPluginAdapter
from eventum.plugins.input.plugins.cron.config import CronInputPluginConfig
from eventum.plugins.input.plugins.cron.plugin import CronInputPlugin


def test_identified_timestamps_plugin_adapter():
    plugin = CronInputPlugin(
        config=CronInputPluginConfig(
            start='now',
            end='+60s',
            expression='* * * * * *',
            count=1
        ),
        params={'id': 1437, 'timezone': timezone('UTC')}
    )
    adapted = IdentifiedTimestampsPluginAdapter(plugin=plugin)

    plugin_arrays = []
    for array in plugin.generate(size=1000, skip_past=False):
        plugin_arrays.append(array)

    adapter_arrays = []
    for array in adapted.iterate(size=1000, skip_past=False):
        adapter_arrays.append(array)

    plugin_arr = np.concatenate(plugin_arrays)
    adapter_arr = np.concatenate(adapter_arrays)

    assert np.array_equal(plugin_arr, adapter_arr['timestamp'])

    ids = set(adapter_arr['id'])
    assert len(ids) == 1
    assert ids.pop() == 1437
