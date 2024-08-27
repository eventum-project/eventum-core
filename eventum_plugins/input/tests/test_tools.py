from datetime import datetime, timedelta

import pytest
import pytz

from eventum_plugins.input.tools import normalize_daterange


def test_normalize_daterange():
    expected_start = datetime.fromisoformat('2024-01-01T00:00:00.000Z')
    expected_end = datetime(2077, 1, 1, 0, 0, tzinfo=pytz.timezone('UTC'))

    start, end = normalize_daterange(
        start=expected_start,
        end='1st Jan of 2077 year',
        timezone=pytz.timezone('UTC')
    )

    assert start == expected_start
    assert end == expected_end


def test_normalize_daterange_time_keyword():
    approx_expected_start = datetime.now(tz=pytz.timezone('UTC'))
    enough_for_me = datetime(2100, 1, 1, 0, 0, tzinfo=pytz.timezone('UTC'))

    start, end = normalize_daterange(
        start='now',
        end='never',
        timezone=pytz.timezone('UTC'),
    )

    assert 0 < (start - approx_expected_start).total_seconds() < 1
    assert end > enough_for_me


def test_normalize_daterange_human_relative_end():
    expected_start = datetime.fromisoformat('2024-01-01T00:00:00.000Z')
    expected_end = expected_start + timedelta(hours=12, minutes=5)

    start, end = normalize_daterange(
        start=expected_start,
        end='after 12 hours and five minute',
        timezone=pytz.timezone('UTC')
    )

    assert start == expected_start
    assert end == expected_end


def test_normalize_daterange_none_values_now_start():
    approx_expected_start = datetime.now(tz=pytz.timezone('UTC'))
    enough_for_me = datetime(2100, 1, 1, 0, 0, tzinfo=pytz.timezone('UTC'))

    start, end = normalize_daterange(
        start=None,
        end=None,
        timezone=pytz.timezone('UTC'),
        none_start='now'
    )

    assert 0 < (start - approx_expected_start).total_seconds() < 1
    assert end > enough_for_me


def test_normalize_daterange_none_values_min_start():
    enough_early_for_me = datetime(
        10, 1, 1, 0, 0, tzinfo=pytz.timezone('UTC')
    )
    enough_late_for_me = datetime(
        2100, 1, 1, 0, 0, tzinfo=pytz.timezone('UTC')
    )

    start, end = normalize_daterange(
        start=None,
        end=None,
        timezone=pytz.timezone('UTC'),
        none_start='min'
    )

    assert start < enough_early_for_me
    assert end > enough_late_for_me


def test_normalize_daterange_invalid():
    with pytest.raises(ValueError):
        normalize_daterange(
            start=datetime(
                2024, 1, 1, 0, 0, tzinfo=pytz.timezone('UTC')
            ),
            end=datetime(
                2014, 1, 1, 0, 0, tzinfo=pytz.timezone('UTC')
            ),
            timezone=pytz.timezone('UTC'),
        )

    with pytest.raises(ValueError):
        normalize_daterange(
            start='never',
            end=None,
            timezone=pytz.timezone('UTC'),
        )

    with pytest.raises(ValueError):
        normalize_daterange(
            start='qwerty',
            end=None,
            timezone=pytz.timezone('UTC'),
        )
