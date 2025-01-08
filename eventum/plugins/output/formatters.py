import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, Sequence, TypeVar

import msgspec
from jinja2 import (BaseLoader, Environment, FileSystemLoader, Template,
                    TemplateError, TemplateNotFound)

from eventum.plugins.output.exceptions import FormatError
from eventum.plugins.output.fields import (BaseFormatterConfig, Format,
                                           JsonFormatterConfig,
                                           SimpleFormatterConfig,
                                           TemplateFormatterConfig)


@dataclass(frozen=True, slots=True)
class FormattingResult:
    """Resulting data of formatting.

    Parameters
    ----------
    events : list[str]
        List of formatted events, number of events can be the same as
        original or not due to formatting errors of specific events
        from the entire provided list or reduction behavior of specific
        formatters which take multiple events and produce for example
        one aggregated event

    formatted_count : int
        Number of successfully formatted events, this field is helpful
        for tracking number of successfully formatted events with taking
        into account possible events aggregation

    errors : list[FormatError]
        List with formatting errors of specific events or entire
        sequence of events (for specific aggregating formatters)
    """
    events: list[str]
    formatted_count: int
    errors: list[FormatError]


T = TypeVar('T', bound=BaseFormatterConfig)


class Formatter(ABC, Generic[T]):
    """Base formatter.

    Parameters
    ----------
    config : T
        Formatter config

    Raises
    ------
    ValueError
        If any error occurs during formatter initialization for
        parameters specified in provided config

    Other Parameters
    ----------------
    format : Format
        Format to which to bind formatter class
    """
    _registered_formatters: dict[
        Format,
        type['Formatter[Any]']
    ] = dict()

    def __init_subclass__(cls, format: Format, **kwargs: Any) -> None:
        if format in Formatter._registered_formatters:
            registered_formatter = Formatter._registered_formatters[format]
            raise ValueError(
                f'Formatter {registered_formatter} is already registered '
                f'for format "{format}"'
            )

        Formatter._registered_formatters[format] = cls

        return super().__init_subclass__(**kwargs)

    def __init__(self, config: T) -> None:
        self._config = config

    @abstractmethod
    def format_events(self, events: Sequence[str]) -> FormattingResult:
        """Format events.

        Parameters
        ----------
        Sequence[str]
            Events to format

        Returns
        -------
        FormattingResult
            Result of events formatting
        """
        ...

    @classmethod
    def get_formatter(cls, format: Format) -> type['Formatter[Any]']:
        """Get appropriate formatter for specified format.

        Parameters
        ----------
        format : Format
            Format

        Returns
        -------
        type['Formatter[Any]']
            Formatter

        Raises
        ------
        ValueError
            If no appropriate formatter found for format
        """
        try:
            return cls._registered_formatters[format]
        except KeyError:
            raise ValueError(f'No formatter found for format "{format}"')


class PlainFormatter(Formatter[SimpleFormatterConfig], format=Format.PLAIN):
    """Formatter that preserves original format of events."""

    def __init__(self, config: SimpleFormatterConfig) -> None:
        super().__init__(config)

    def format_events(self, events: Sequence[str]) -> FormattingResult:
        return FormattingResult(
            events=list(events),
            formatted_count=len(events),
            errors=[]
        )


class JsonFormatter(Formatter[JsonFormatterConfig], format=Format.JSON):
    """Formatter that formats events as JSON."""

    def __init__(self, config: JsonFormatterConfig) -> None:
        super().__init__(config)

    def format_events(self, events: Sequence[str]) -> FormattingResult:
        formatted_events: list[str] = []
        errors: list[FormatError] = []

        for event in events:
            try:
                formatted_events.append(
                    msgspec.json.format(event, indent=self._config.indent)
                )
            except msgspec.DecodeError as e:
                errors.append(FormatError(str(e), original_event=event))

        return FormattingResult(
            events=formatted_events,
            formatted_count=len(formatted_events),
            errors=errors
        )


class JsonBatchFormatter(
    Formatter[JsonFormatterConfig],
    format=Format.JSON_BATCH
):
    """Formatter that formats events into a single JSON list."""

    def __init__(self, config: JsonFormatterConfig) -> None:
        super().__init__(config)

    def format_events(self, events: Sequence[str]) -> FormattingResult:
        validated_events: list[str] = []
        errors: list[FormatError] = []

        for event in events:
            try:
                validated_events.append(msgspec.json.format(event, indent=-1))
            except msgspec.DecodeError as e:
                errors.append(FormatError(str(e), original_event=event))

        event = msgspec.json.format(
            f'[{",".join(validated_events)}]',
            indent=self._config.indent
        )

        return FormattingResult(
            events=[event],
            formatted_count=len(validated_events),
            errors=errors
        )


def _load_template_from_string(template: str) -> Template:
    """Load template from string.

    Parameters
    ----------
    template : str
        Template source

    Returns
    -------
    Template
        Loaded template

    Raises
    ------
    ValueError
        If template cannot be loaded
    """
    env = Environment(loader=BaseLoader())

    try:
        return env.from_string(template)
    except TemplateError as e:
        raise ValueError(f'Cannot load template: {e}')


def _load_template_from_file(template_path: str) -> Template:
    """Load template from file.

    Parameters
    ----------
    template_path : str
        Path to file with template source

    Returns
    -------
    Template
        Loaded template

    Raises
    ------
    ValueError
        If template cannot be loaded
    """
    if os.path.isabs(template_path):
        base_path = os.path.dirname(template_path)
        template_name = os.path.basename(template_path)
    else:
        base_path = os.getcwd()
        template_name = template_path

    env = Environment(
        loader=FileSystemLoader(searchpath=base_path)
    )
    try:
        return env.get_template(template_name)
    except TemplateNotFound:
        raise ValueError('Template is not found')
    except TemplateError as e:
        raise ValueError(f'Cannot load template: {e}')


class TemplateFormatter(
    Formatter[TemplateFormatterConfig],
    format=Format.TEMPLATE
):
    """Formatter that formats events using user defined template."""

    def __init__(self, config: TemplateFormatterConfig) -> None:
        super().__init__(config)

        if config.template_path is not None:
            self._template = _load_template_from_file(config.template_path)
        elif config.template is not None:
            self._template = _load_template_from_string(config.template)
        else:
            raise AssertionError(
                'Missing config validation for template formatter'
            )

    def format_events(self, events: Sequence[str]) -> FormattingResult:
        formatted_events: list[str] = []
        errors: list[FormatError] = []

        for event in events:
            try:
                formatted_events.append(self._template.render(event=event))
            except Exception as e:
                errors.append(
                    FormatError(
                        (
                            f'Failed to render template: '
                            f'{e.__class__.__name__}: {e}',
                        ),
                        original_event=event
                    )
                )

        return FormattingResult(
            events=formatted_events,
            formatted_count=len(formatted_events),
            errors=errors
        )


class TemplateBatchFormatter(
    Formatter[TemplateFormatterConfig],
    format=Format.TEMPLATE_BATCH
):
    """Formatter that formats events into a single event using user
    defined template.
    """

    def __init__(self, config: TemplateFormatterConfig) -> None:
        super().__init__(config)

        if config.template_path is not None:
            self._template = _load_template_from_file(config.template_path)
        elif config.template is not None:
            self._template = _load_template_from_string(config.template)
        else:
            raise AssertionError(
                'Missing config validation for template formatter'
            )

    def format_events(self, events: Sequence[str]) -> FormattingResult:
        formatted_events: list[str] = []
        errors: list[FormatError] = []

        try:
            formatted_events.append(self._template.render(events=events))
        except Exception as e:
            errors.append(
                FormatError(
                    f'Failed render template: {e.__class__.__name__}: {e}'
                )
            )

        return FormattingResult(
            events=formatted_events,
            formatted_count=len(events),
            errors=errors
        )


class EventumHttpInputFormatter(
    Formatter[SimpleFormatterConfig],
    format=Format.EVENTUM_HTTP_INPUT
):
    """Formatter that formats events into request body for Eventum HTTP
    input plugin.
    """

    def __init__(self, config: SimpleFormatterConfig) -> None:
        super().__init__(config)

    def format_events(self, events: Sequence[str]) -> FormattingResult:
        return FormattingResult(
            events=[f'{{"count": {len(events)}}}'],
            formatted_count=len(events),
            errors=[]
        )


def get_formatter_class(format: Format) -> type[Formatter[Any]]:
    """Return specific formatter class depending on format.

    Parameters
    ----------
    format : Format
        Format

    Returns
    -------
    type[Formatter[Any]]
        Formatter class

    Raises
    ------
    ValueError
        If no appropriate formatter found for specified format
    """
    return Formatter.get_formatter(format)
