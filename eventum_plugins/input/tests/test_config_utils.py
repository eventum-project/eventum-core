from datetime import datetime, timedelta

import pytz

from eventum_plugins.input.base.config import InputPluginConfig
from eventum_plugins.input.config_utils import retrieve_daterange
from eventum_plugins.input.fields import HumanDatetimeString


class TestConfigModule(InputPluginConfig, frozen=True):
    start: datetime | HumanDatetimeString | None = None
    end: datetime | HumanDatetimeString | None = None
    some_field: str = 'some info'

    # disable pytest discovery
    __test__ = False


def test_retrieve_daterange():
    expected_start = datetime.fromisoformat('2024-01-01T00:00:00.000Z')
    expected_end = datetime(2077, 1, 1, 0, 0, tzinfo=pytz.timezone('UTC'))

    start, end = retrieve_daterange(
        TestConfigModule(
            start=expected_start,
            end='1st Jan of 2077 year'
        ),
        timezone=pytz.timezone('UTC')
    )

    assert start == expected_start
    assert end == expected_end


def test_retrieve_daterange_relative_end():
    expected_start = datetime.fromisoformat('2024-01-01T00:00:00.000Z')
    expected_end = expected_start + timedelta(hours=12, minutes=5)

    start, end = retrieve_daterange(
        TestConfigModule(
            start=expected_start,
            end='after 12 hours and five minute'
        ),
        timezone=pytz.timezone('UTC')
    )

    assert start == expected_start
    assert end == expected_end


def test_retrieve_daterange_none_values():
    approx_expected_start = datetime.now(tz=pytz.timezone('UTC'))
    enough_for_me = datetime(2100, 1, 1, 0, 0, tzinfo=pytz.timezone('UTC'))

    start, end = retrieve_daterange(
        TestConfigModule(
            start=None,
            end=None
        ),
        timezone=pytz.timezone('UTC')
    )

    assert 0 < (start - approx_expected_start).total_seconds() < 1
    assert end > enough_for_me
