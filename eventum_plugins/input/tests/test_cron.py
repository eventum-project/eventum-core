from datetime import datetime

import pytest
from freezegun import freeze_time
from numpy import datetime64
from pydantic import ValidationError
from pytz import timezone

from eventum_plugins.input.cron import CronInputConfig, CronInputPlugin


@pytest.mark.parametrize(
    ('expression',),
    [
        ('* * * * *', ),
        ('*/5 * * * *', ),
        ('0-30/2 */12 * * *', ),
        ('@daily', )
    ]
)
def test_valid_config(expression):
    CronInputConfig(expression=expression, count=1)


@pytest.mark.parametrize(
    ('expression', 'count'),
    [
        ('* * * * *', 0),
        ('* * * * *', -1),
        ('0-66 * * * *', 1),
        ('@nano-secondly', 999999)
    ]
)
def test_invalid_config(expression, count):
    with pytest.raises(ValidationError):
        CronInputConfig(expression=expression, count=count)


def test_cron_live():
    plugin = CronInputPlugin(
        config=CronInputConfig(expression='* * * * *', count=1),
        tz=timezone('UTC')
    )

    events = []

    def on_event(event):
        events.append(event)
        raise InterruptedError

    with freeze_time('2024-01-01T00:00:59.500Z', tz_offset=0, tick=True):
        try:
            plugin.live(on_event=on_event)
        except InterruptedError:
            pass

    expected = datetime64(datetime.fromisoformat('2024-01-01T00:01:00.000'))
    assert events.pop() == expected
