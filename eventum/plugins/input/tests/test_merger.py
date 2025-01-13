from datetime import datetime, timedelta

import numpy as np
from pytz import timezone

from eventum.plugins.input.merger import InputPluginsMerger
from eventum.plugins.input.plugins.linspace.config import \
    LinspaceInputPluginConfig
from eventum.plugins.input.plugins.linspace.plugin import LinspaceInputPlugin


def test_merger():
    start = datetime.now(tz=timezone('UTC'))

    plugin_1 = LinspaceInputPlugin(
        config=LinspaceInputPluginConfig(
            start=start + timedelta(seconds=0.5),
            end='+1s',
            count=100_000,
        ),
        params={
            'id': 1,
            'timezone': timezone('UTC'),
        }
    )

    plugin_2 = LinspaceInputPlugin(
        config=LinspaceInputPluginConfig(
            start=start + timedelta(seconds=0.6),
            end='+1s',
            count=100_000,
        ),
        params={
            'id': 2,
            'timezone': timezone('UTC'),
        }
    )

    plugin_3 = LinspaceInputPlugin(
        config=LinspaceInputPluginConfig(
            start=start + timedelta(seconds=0.7),
            end='+1s',
            count=100_000,
        ),
        params={
            'id': 3,
            'timezone': timezone('UTC'),
        }
    )

    plugins_lst = [plugin_1, plugin_2, plugin_3]

    merger = InputPluginsMerger(plugins=plugins_lst)

    batches = list(merger.iter_merged(
        10000, skip_past=False, include_id=False))

    array = np.concatenate(batches)
    assert array.size == 300_000
    assert np.all(array[:-1] <= array[1:])


def test_merger_with__ids():
    start = datetime.now(tz=timezone('UTC'))

    plugin_1 = LinspaceInputPlugin(
        config=LinspaceInputPluginConfig(
            start=start + timedelta(seconds=0.5),
            end='+1s',
            count=100_000,
        ),
        params={
            'id': 1,
            'timezone': timezone('UTC'),
        }
    )

    plugin_2 = LinspaceInputPlugin(
        config=LinspaceInputPluginConfig(
            start=start + timedelta(seconds=0.6),
            end='+1s',
            count=100_000,
        ),
        params={
            'id': 2,
            'timezone': timezone('UTC'),
        }
    )

    plugin_3 = LinspaceInputPlugin(
        config=LinspaceInputPluginConfig(
            start=start + timedelta(seconds=0.7),
            end='+1s',
            count=100_000,
        ),
        params={
            'id': 3,
            'timezone': timezone('UTC'),
        }
    )

    plugins_lst = [plugin_1, plugin_2, plugin_3]

    merger = InputPluginsMerger(plugins=plugins_lst)

    batches = list(merger.iter_merged(
        10000, skip_past=False, include_id=True))

    array = np.concatenate(batches)

    assert array.size == 300_000

    occurrences = dict(zip(*np.unique(array['id'], return_counts=True)))

    assert occurrences[1] == 100_000
    assert occurrences[2] == 100_000
    assert occurrences[3] == 100_000
