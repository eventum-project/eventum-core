import pytest

from eventum.plugins.output.exceptions import FormatError
from eventum.plugins.output.fields import (Format, JsonFormatterConfig,
                                           SimpleFormatterConfig,
                                           TemplateFormatterConfig)
from eventum.plugins.output.formatters import (EventumHttpInputFormatter,
                                               FormattingResult,
                                               JsonBatchFormatter,
                                               JsonFormatter, PlainFormatter,
                                               TemplateBatchFormatter,
                                               TemplateFormatter)


def test_plain_formatter():
    formatter = PlainFormatter(
        config=SimpleFormatterConfig(format=Format.PLAIN)
    )

    events = ['event1', 'event2', 'event3']

    result = formatter.format_events(events)

    assert result == FormattingResult(
        events=events,
        formatted_count=3,
        errors=[]
    )


def test_json_formatter():
    formatter = JsonFormatter(
        config=JsonFormatterConfig(format=Format.JSON, indent=2)
    )

    events = ['"event1"', '{"key": "value"}', 'invalid json']

    result = formatter.format_events(events)

    assert result.events == ['"event1"', '{\n  "key": "value"\n}',]
    assert result.formatted_count == 2
    assert len(result.errors) == 1
    assert isinstance(result.errors[0], FormatError)


def test_json_batch_formatter():
    formatter = JsonBatchFormatter(
        config=JsonFormatterConfig(format=Format.JSON_BATCH, indent=2)
    )

    events = ['"event1"', '{"key": "value"}', 'invalid json']

    result = formatter.format_events(events)

    assert result.events == [
        '[\n  "event1",\n  {\n    "key": "value"\n  }\n]'
    ]
    assert result.formatted_count == 2
    assert len(result.errors) == 1

    assert isinstance(result.errors[0], FormatError)


def test_template_formatter_with_template():
    formatter = TemplateFormatter(
        config=TemplateFormatterConfig(
            format=Format.TEMPLATE,
            template='{{ event | upper }}'
        )
    )

    events = ['event1', 'event2', 'event3']
    result = formatter.format_events(events)

    assert result == FormattingResult(
        events=['EVENT1', 'EVENT2', 'EVENT3'],
        formatted_count=3,
        errors=[]
    )


def test_template_formatter_with_template_path(tmp_path):
    template_file = tmp_path / 'template.j2'
    template_file.write_text('{{ event | lower }}')

    formatter = TemplateFormatter(
        config=TemplateFormatterConfig(
            format=Format.TEMPLATE,
            template_path=str(template_file)
        )
    )

    events = ['EVENT1', 'EVENT2', 'EVENT3']
    result = formatter.format_events(events)

    assert result == FormattingResult(
        events=['event1', 'event2', 'event3'],
        formatted_count=3,
        errors=[]
    )


def test_template_formatter_template_not_found():
    with pytest.raises(ValueError):
        TemplateFormatter(
            config=TemplateFormatterConfig(
                format=Format.TEMPLATE,
                template_path='non_existent_file'
            )
        )


def test_template_formatter_invalid_template(tmp_path):
    template_file = tmp_path / 'template.j2'
    template_file.write_text('{% invalid jinja %}')

    with pytest.raises(ValueError):
        TemplateFormatter(
            config=TemplateFormatterConfig(
                format=Format.TEMPLATE,
                template_path=str(template_file)
            )
        )


def test_template_formatter_both_template_and_path():
    with pytest.raises(ValueError):
        TemplateFormatter(
            config=TemplateFormatterConfig(
                format=Format.TEMPLATE,
                template='{{ event }}',
                template_path='some_path'
            )
        )


def test_template_formatter_neither_template_nor_path():
    with pytest.raises(ValueError):
        TemplateFormatter(
            config=TemplateFormatterConfig(format=Format.TEMPLATE)
        )


def test_template_formatter_template_error():
    formatter = TemplateFormatter(
        config=TemplateFormatterConfig(
            format=Format.TEMPLATE,
            template='{{ event - 1 }}'
        )
    )

    events = ['event1']
    result = formatter.format_events(events)

    assert len(result.errors) == 1


def test_template_batch_formatter():
    formatter = TemplateBatchFormatter(
        config=TemplateFormatterConfig(
            format=Format.TEMPLATE_BATCH,
            template="{{ events | join(', ') }}"
        )
    )

    events = ['event1', 'event2', 'event3']
    result = formatter.format_events(events)

    assert result == FormattingResult(
        events=['event1, event2, event3'],
        formatted_count=3,
        errors=[]
    )


def test_eventum_http_input_formatter():
    formatter = EventumHttpInputFormatter(
        config=SimpleFormatterConfig(
            format=Format.EVENTUM_HTTP_INPUT
        )
    )

    events = ['event1', 'event2', 'event3']
    result = formatter.format_events(events)

    assert result == FormattingResult(
        events=['{"count": 3}'],
        formatted_count=3,
        errors=[]
    )
