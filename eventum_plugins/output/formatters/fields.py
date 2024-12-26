import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal, Self, Sequence

import msgspec
from jinja2 import (BaseLoader, Environment, FileSystemLoader, TemplateError,
                    TemplateNotFound)
from pydantic import BaseModel, Field, RootModel, model_validator

from eventum_plugins.output.formatters.encodings import Encoding
from eventum_plugins.output.formatters.exceptions import FormatError


class Format(StrEnum):
    PLAIN = 'plain'
    JSON = 'json'
    JSON_BATCH = 'json-batch'
    TEMPLATE = 'template'
    TEMPLATE_BATCH = 'template-batch'


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
        List with formatting errors of specific events if there were
        any
    """
    events: list[str]
    formatted_count: int
    errors: list[FormatError]


class BaseFormatter(ABC, BaseModel):
    """Base formatter.

    Parameters
    ----------
    encoding : Encoding, default='utf-8'
        Target encoding
    """
    encoding: Encoding = Field(default='utf_8')

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


class PlainFormatter(BaseFormatter):
    """Formatter that preserves original format of events.

    format : Literal[Format.PLAIN]
        Target format
    """
    format: Literal[Format.PLAIN]

    def format_events(self, events: Sequence[str]) -> FormattingResult:
        return FormattingResult(
            events=list(events),
            formatted_count=len(events),
            errors=[]
        )


class JsonFormatter(BaseFormatter):
    """Formatter for formatting events as JSON.

    Parameters
    ----------
    format : Literal[Format.JSON]
        Target format

    indent : int, default=0
        Indentation size
    """
    format: Literal[Format.JSON]
    indent: int = Field(default=0, ge=0)

    def format_events(self, events: Sequence[str]) -> FormattingResult:
        formatted_events: list[str] = []
        errors: list[FormatError] = []
        for event in events:
            try:
                formatted_events.append(
                    msgspec.json.format(event, indent=self.indent)
                )
            except msgspec.DecodeError as e:
                errors.append(FormatError(str(e), original_event=event))

        return FormattingResult(
            events=formatted_events,
            formatted_count=len(formatted_events),
            errors=errors
        )


class JsonBatchFormatter(BaseFormatter):
    """Formatter for formatting events into a single JSON list.

    Parameters
    ----------
    format : Literal[Format.JSON_BATCH]
        Target format

    indent : int, default=0
        Indentation size
    """
    format: Literal[Format.JSON_BATCH]
    indent: int = Field(default=0, ge=0)

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
            indent=self.indent
        )

        return FormattingResult(
            events=[event],
            formatted_count=len(validated_events),
            errors=errors
        )


class TemplateFormatter(BaseFormatter):
    """Formatter for formatting events using user defined template.

    Parameters
    ----------
    format : Literal[Format.TEMPLATE]
        Target format

    template : str | None, default=None
        Template content

    template_path : str | None, default=None
        Template path

    Notes
    -----
    To access original event in template use `event` variable
    """
    format: Literal[Format.TEMPLATE]
    template: str | None = Field(default=None, min_length=1)
    template_path: str | None = Field(default=None, min_length=1)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        if self.template_path is not None:
            env = Environment(
                loader=FileSystemLoader(searchpath=os.getcwd())
            )
            try:
                self._template = env.get_template(self.template_path)
            except TemplateNotFound:
                raise ValueError('Template is not found')
            except TemplateError as e:
                raise ValueError(f'Cannot load template: {e}')
        elif self.template is not None:
            env = Environment(loader=BaseLoader())

            try:
                self._template = env.from_string(self.template)
            except TemplateError as e:
                raise ValueError(f'Cannot load template: {e}')

    @model_validator(mode='after')
    def validate_template_or_path_provided(self) -> Self:
        if self.template is None and self.template_path is None:
            raise ValueError('Template or template path must be provided')

        if self.template is not None and self.template_path is not None:
            raise ValueError(
                'Template or template path must be provided, but not both'
            )

        return self

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


class TemplateBatchFormatter(TemplateFormatter):
    """Formatter for formatting events using user defined template
    into a single event.

    Parameters
    ----------
    format : Literal[Format.TEMPLATE_BATCH]
        Target format

    template : str | None, default=None
        Template content

    template_path : str | None, default=None
        Template path

    Notes
    -----
    To access original events sequence in template use `events`
    variable
    """
    format: Literal[Format.TEMPLATE]
    template: str | None = Field(default=None, min_length=1)
    template_path: str | None = Field(default=None, min_length=1)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

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


OutputFormats = (
    PlainFormatter | JsonFormatter | JsonBatchFormatter
    | TemplateFormatter
)


class Formatter(RootModel):
    root: OutputFormats = Field(discriminator='format')
