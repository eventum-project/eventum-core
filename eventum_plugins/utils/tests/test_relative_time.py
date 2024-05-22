from datetime import timedelta

import pytest

from eventum_plugins.utils.relative_time import parse_relative_time


def test_parse_relative_time():
    assert parse_relative_time('1d') == timedelta(days=1)
    assert parse_relative_time('12h') == timedelta(hours=12)
    assert parse_relative_time('15m') == timedelta(minutes=15)
    assert parse_relative_time('30s') == timedelta(seconds=30)
    assert parse_relative_time('-1d') == timedelta(days=-1)
    assert parse_relative_time('-15m2s') == timedelta(minutes=-15, seconds=-2)
    assert parse_relative_time('-1d30s') == timedelta(days=-1, seconds=-30)
    assert parse_relative_time('-12h10m15s') == timedelta(
        hours=-12, minutes=-10, seconds=-15
    )
    assert parse_relative_time('50d60h70m80s') == timedelta(
        days=50, hours=60, minutes=70, seconds=80
    )
    assert parse_relative_time('-50d60h70m80s') == timedelta(
        days=-50, hours=-60, minutes=-70, seconds=-80
    )
    assert parse_relative_time('+15d15h30m24s') == timedelta(
        days=15, hours=15, minutes=30, seconds=24
    )

    with pytest.raises(ValueError):
        parse_relative_time('16Days minus three hours')

    with pytest.raises(ValueError):
        parse_relative_time('16d3j')

    with pytest.raises(ValueError):
        parse_relative_time('')
