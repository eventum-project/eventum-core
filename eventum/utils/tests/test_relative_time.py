from datetime import timedelta

from eventum.utils.relative_time import parse_relative_time


def test_parse_relative_time():
    assert parse_relative_time('1d') == timedelta(days=1)
    assert parse_relative_time('12h') == timedelta(hours=12)
    assert parse_relative_time('15m') == timedelta(minutes=15)
    assert parse_relative_time('30s') == timedelta(seconds=30)
    assert parse_relative_time('-1d') == timedelta(days=-1)
    assert parse_relative_time('-15m-2s') == timedelta(minutes=-15, seconds=-2)
    assert parse_relative_time('-1d+30s') == timedelta(days=-1, seconds=30)
    assert parse_relative_time('12h-10m+15s') == timedelta(
        hours=12, minutes=-10, seconds=15
    )
    assert parse_relative_time('50d+60h+70m+80s') == timedelta(
        days=50, hours=60, minutes=70, seconds=80
    )
    assert parse_relative_time('-50d-60h-70m-80s') == timedelta(
        days=-50, hours=-60, minutes=-70, seconds=-80
    )
    assert parse_relative_time('+15d-15h+30m-24s') == timedelta(
        days=15, hours=-15, minutes=30, seconds=-24
    )
