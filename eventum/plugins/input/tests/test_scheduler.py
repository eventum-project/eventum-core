import time

import pytest
from pytz import timezone

from eventum.plugins.input.adapters import IdentifiedTimestampsPluginAdapter
from eventum.plugins.input.batcher import TimestampsBatcher
from eventum.plugins.input.plugins.static.config import StaticInputPluginConfig
from eventum.plugins.input.plugins.static.plugin import StaticInputPlugin
from eventum.plugins.input.plugins.timer.config import TimerInputPluginConfig
from eventum.plugins.input.plugins.timer.plugin import TimerInputPlugin
from eventum.plugins.input.scheduler import BatchScheduler


@pytest.fixture
def instant_source():
    return IdentifiedTimestampsPluginAdapter(
        StaticInputPlugin(
            config=StaticInputPluginConfig(count=1000),
            params={'id': 1, 'timezone': timezone('UTC')}
        )
    )


@pytest.fixture
def delayed_source():
    return IdentifiedTimestampsPluginAdapter(
        TimerInputPlugin(
            config=TimerInputPluginConfig(
                start='now',
                seconds=0.5,
                count=1000,
                repeat=1
            ),
            params={'id': 1, 'timezone': timezone('UTC')}
        )
    )


def test_scheduler(instant_source):
    scheduler = BatchScheduler(
        batcher=TimestampsBatcher(
            source=instant_source,
            batch_size=100,
            batch_delay=None
        ),
        timezone=timezone('UTC')
    )

    t1 = time.time()
    batches = list(scheduler.iterate(skip_past=False))
    t2 = time.time()

    assert len(batches) == 10
    assert (t2 - t1) < 0.5


def test_scheduler_delay(delayed_source):
    scheduler = BatchScheduler(
        batcher=TimestampsBatcher(
            source=delayed_source,
            batch_size=100,
            batch_delay=None
        ),
        timezone=timezone('UTC')
    )

    t1 = time.time()
    batches = list(scheduler.iterate(skip_past=False))
    t2 = time.time()

    assert len(batches) == 10
    assert (t2 - t1) >= 0.5
