import pytest

from eventum_plugins.output.formatters import (Format, format_event,
                                               format_events, format_ndjson)


def test_format_ndjson_valid():
    event = '{"key":     "value"\n}'
    assert format_ndjson(event) == '{"key": "value"}'


def test_format_ndjson_invalid():
    event = '{"key": "value}'
    with pytest.raises(ValueError):
        format_ndjson(event)


def test_format_event_plain():
    event = '{"key": "value"}'
    assert format_event(event, Format.PLAIN) == event


def test_format_event_ndjson():
    event = '{"key": "value"}'
    assert format_event(event, Format.NDJSON) == '{"key": "value"}'


def test_format_events_plain():
    events = ['{"key": "value"}', '{"key": "value2"}']
    assert format_events(events, Format.PLAIN) == events


def test_format_events_ndjson():
    events = ['{"key":    "value"}', '{"key": "value2"\n}']
    assert format_events(events, Format.NDJSON) == [
        '{"key": "value"}',
        '{"key": "value2"}'
    ]


def test_format_events_invalid():
    events = ['{"key": "value"}', '{"key": "value2', '{"key": "value3"}']
    with pytest.raises(ValueError):
        format_events(events, Format.NDJSON, ignore_errors=False)


def test_format_events_ignore_errors():
    events = ['{"key": "value"}', '{"key": "value2', '{"key": "value3"}']
    formatted_events = format_events(events, Format.NDJSON, ignore_errors=True)
    assert len(formatted_events) == 2
    assert formatted_events[0] == '{"key": "value"}'
    assert formatted_events[1] == '{"key": "value3"}'


def test_format_events_ignore_errors_callback():
    error_count = 0

    def error_callback(e):
        nonlocal error_count
        error_count += 1

    events = ['{"key": "value"}', '{"key": "value2', '{"key": "value3"}']
    formatted_events = format_events(
        events=events,
        format=Format.NDJSON,
        ignore_errors=True,
        error_callback=error_callback
    )

    assert len(formatted_events) == 2
    assert formatted_events[0] == '{"key": "value"}'
    assert formatted_events[1] == '{"key": "value3"}'
    assert error_count == 1
