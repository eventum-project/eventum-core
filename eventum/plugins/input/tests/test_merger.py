from datetime import datetime, timedelta

import numpy as np
import pytest
from pytz import timezone

from eventum.plugins.input.merger import InputPluginsLiveMerger
from eventum.plugins.input.plugins.linspace.config import \
    LinspaceInputPluginConfig
from eventum.plugins.input.plugins.linspace.plugin import LinspaceInputPlugin


def test_merger_with_ordering():
    start = datetime.now(tz=timezone('UTC'))

    plugin_1 = LinspaceInputPlugin(
        config=LinspaceInputPluginConfig(
            start=start + timedelta(seconds=0.5),
            end='+1s',
            count=100_000,
        ),
        params={
            'id': 1,
            'live_mode': True,
            'timezone': timezone('UTC'),
            'batch_size': 100,
            'batch_delay': 0.1
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
            'live_mode': True,
            'timezone': timezone('UTC'),
            'batch_size': 100,
            'batch_delay': 0.1
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
            'live_mode': True,
            'timezone': timezone('UTC'),
            'batch_size': 100,
            'batch_delay': 0.1
        }
    )

    plugins_lst = [plugin_1, plugin_2, plugin_3]

    plugins = InputPluginsLiveMerger(
        plugins=plugins_lst,
        target_delay=0.1,
        batch_size=1000,
        ordering=True
    )

    batches = list(plugins.generate(include_id=False))

    assert all([batch.size <= 1000 for batch in batches])

    array = np.concatenate(batches)

    assert array.size == 300_000
    assert np.all(array[:-1] <= array[1:])


def test_merger_with_ordering_and_ids():
    start = datetime.now(tz=timezone('UTC'))

    plugin_1 = LinspaceInputPlugin(
        config=LinspaceInputPluginConfig(
            start=start + timedelta(seconds=0.5),
            end='+1s',
            count=100_000,
        ),
        params={
            'id': 1,
            'live_mode': True,
            'timezone': timezone('UTC'),
            'batch_size': 100,
            'batch_delay': 0.1
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
            'live_mode': True,
            'timezone': timezone('UTC'),
            'batch_size': 100,
            'batch_delay': 0.1
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
            'live_mode': True,
            'timezone': timezone('UTC'),
            'batch_size': 100,
            'batch_delay': 0.1
        }
    )

    plugins_lst = [plugin_1, plugin_2, plugin_3]

    plugins = InputPluginsLiveMerger(
        plugins=plugins_lst,
        target_delay=0.1,
        batch_size=1000,
        ordering=True
    )

    batches = list(plugins.generate(include_id=True))

    assert all([batch.size <= 1000 for batch in batches])

    array = np.concatenate(batches)

    assert array.size == 300_000

    occurrences = dict(zip(*np.unique(array['id'], return_counts=True)))

    assert occurrences[1] == 100_000
    assert occurrences[2] == 100_000
    assert occurrences[3] == 100_000


def test_merger_without_ordering():
    start = datetime.now(tz=timezone('UTC'))

    plugin_1 = LinspaceInputPlugin(
        config=LinspaceInputPluginConfig(
            start=start + timedelta(seconds=0.5),
            end='+1s',
            count=100_000,
        ),
        params={
            'id': 1,
            'live_mode': True,
            'timezone': timezone('UTC'),
            'batch_size': 3000,
            'batch_delay': 0.1
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
            'live_mode': True,
            'timezone': timezone('UTC'),
            'batch_size': 2000,
            'batch_delay': 0.1
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
            'live_mode': True,
            'timezone': timezone('UTC'),
            'batch_size': 1000,
            'batch_delay': 0.1
        }
    )

    plugins_lst = [plugin_1, plugin_2, plugin_3]

    plugins = InputPluginsLiveMerger(
        plugins=plugins_lst,
        target_delay=0.1,
        batch_size=1000,
        ordering=False
    )

    batches = list(plugins.generate(include_id=False))

    assert all([batch.size <= 1000 for batch in batches])

    array = np.concatenate(batches)

    assert array.size == 300_000
    assert not np.all(array[:-1] <= array[1:])


def test_merger_without_ordering_with_ids():
    start = datetime.now(tz=timezone('UTC'))

    plugin_1 = LinspaceInputPlugin(
        config=LinspaceInputPluginConfig(
            start=start + timedelta(seconds=0.5),
            end='+1s',
            count=100_000,
        ),
        params={
            'id': 1,
            'live_mode': True,
            'timezone': timezone('UTC'),
            'batch_size': 3000,
            'batch_delay': 0.1
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
            'live_mode': True,
            'timezone': timezone('UTC'),
            'batch_size': 2000,
            'batch_delay': 0.1
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
            'live_mode': True,
            'timezone': timezone('UTC'),
            'batch_size': 1000,
            'batch_delay': 0.1
        }
    )

    plugins_lst = [plugin_1, plugin_2, plugin_3]

    plugins = InputPluginsLiveMerger(
        plugins=plugins_lst,
        target_delay=0.1,
        batch_size=1000,
        ordering=False
    )

    batches = list(plugins.generate(include_id=True))

    assert all([batch.size <= 1000 for batch in batches])

    array = np.concatenate(batches)

    assert array.size == 300_000

    occurrences = dict(zip(*np.unique(array['id'], return_counts=True)))

    assert occurrences[1] == 100_000
    assert occurrences[2] == 100_000
    assert occurrences[3] == 100_000


def test_merger_invalid_params():
    plugin_sample = LinspaceInputPlugin(
        config=LinspaceInputPluginConfig(
            start='now',
            end='+1s',
            count=100_000,
        ),
        params={
            'id': 1,
            'live_mode': False,
            'timezone': timezone('UTC'),
            'batch_size': 100,
            'batch_delay': 0.1
        }
    )

    plugin_live = LinspaceInputPlugin(
        config=LinspaceInputPluginConfig(
            start='now',
            end='+1s',
            count=100_000,
        ),
        params={
            'id': 2,
            'live_mode': True,
            'timezone': timezone('UTC'),
            'batch_size': 100,
            'batch_delay': 0.1
        }
    )

    with pytest.raises(ValueError):
        InputPluginsLiveMerger(
            plugins=[],
            target_delay=0.1,
            batch_size=100,
            ordering=True
        )

    with pytest.raises(ValueError):
        InputPluginsLiveMerger(
            plugins=[plugin_sample],
            target_delay=0.1,
            batch_size=100,
            ordering=True
        )

    with pytest.raises(ValueError):
        InputPluginsLiveMerger(
            plugins=[plugin_live],
            target_delay=0.001,
            batch_size=100,
            ordering=True
        )

    with pytest.raises(ValueError):
        InputPluginsLiveMerger(
            plugins=[plugin_live],
            target_delay=0.1,
            batch_size=0,
            ordering=True
        )
