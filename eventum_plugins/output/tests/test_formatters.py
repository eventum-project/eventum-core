from eventum_plugins.output.formatters import format_event, Format


def test_format_plain():
    event = """
{
    "name": "Bob",
    "age": 22
}
"""
    assert format_event(
        event=event,
        format=Format.PLAIN
    ) == event


def test_format_ndjson():
    assert format_event(
        event="""
{
    "name": "Bob",
    "age": 22
}
""",
        format=Format.NDJSON
    ) == '{"name": "Bob", "age": 22}'
