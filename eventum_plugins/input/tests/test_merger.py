from datetime import datetime, timedelta

import numpy as np
import pytest
from pytz import timezone

from eventum_plugins.input.enums import TimeMode
from eventum_plugins.input.merger import InputPluginsLiveMerger
from eventum_plugins.input.plugins.linspace.config import \
    LinspaceInputPluginConfig
from eventum_plugins.input.plugins.linspace.plugin import LinspaceInputPlugin
from eventum_plugins.input.utils.array_utils import merge_arrays


def test_merger():
    start = datetime.now(tz=timezone('UTC'))

    plugin_1 = LinspaceInputPlugin(
        config=LinspaceInputPluginConfig(
            start=start + timedelta(seconds=0.5),
            end='+1s',
            count=100_000,
        ),
        id=1,
        mode=TimeMode.LIVE,
        timezone=timezone('UTC'),
        batch_size=100,
        batch_delay=0.1
    )

    plugin_2 = LinspaceInputPlugin(
        config=LinspaceInputPluginConfig(
            start=start + timedelta(seconds=0.6),
            end='+1s',
            count=100_000,
        ),
        id=2,
        mode=TimeMode.LIVE,
        timezone=timezone('UTC'),
        batch_size=100,
        batch_delay=0.1
    )

    plugin_3 = LinspaceInputPlugin(
        config=LinspaceInputPluginConfig(
            start=start + timedelta(seconds=0.7),
            end='+1s',
            count=100_000,
        ),
        id=3,
        mode=TimeMode.LIVE,
        timezone=timezone('UTC'),
        batch_size=100,
        batch_delay=0.1
    )

    plugins_lst = [plugin_1, plugin_2, plugin_3]

    plugins = InputPluginsLiveMerger(
        plugins=plugins_lst,
        target_delay=0.1,
        batch_size=1000
    )

    batches = list(plugins.generate())

    assert all([batch.size <= 1000 for batch in batches])

    array = merge_arrays(batches)

    assert array.size == 300_000
    assert np.all(array[:-1] <= array[1:])


def test_merger_invalid_params():
    plugin_sample = LinspaceInputPlugin(
        config=LinspaceInputPluginConfig(
            start='now',
            end='+1s',
            count=100_000,
        ),
        id=1,
        mode=TimeMode.SAMPLE,
        timezone=timezone('UTC'),
        batch_size=100,
        batch_delay=0.1
    )

    plugin_live = LinspaceInputPlugin(
        config=LinspaceInputPluginConfig(
            start='now',
            end='+1s',
            count=100_000,
        ),
        id=1,
        mode=TimeMode.LIVE,
        timezone=timezone('UTC'),
        batch_size=100,
        batch_delay=0.1
    )

    with pytest.raises(ValueError):
        InputPluginsLiveMerger(plugins=[], target_delay=0.1, batch_size=100)

    with pytest.raises(ValueError):
        InputPluginsLiveMerger(
            plugins=[plugin_sample],
            target_delay=0.1,
            batch_size=100
        )

    with pytest.raises(ValueError):
        InputPluginsLiveMerger(
            plugins=[plugin_live],
            target_delay=0.001,
            batch_size=100
        )

    with pytest.raises(ValueError):
        InputPluginsLiveMerger(
            plugins=[plugin_live],
            target_delay=0.1,
            batch_size=0
        )
