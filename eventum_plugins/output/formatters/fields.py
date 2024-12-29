import os
from abc import ABC
from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, Field, RootModel, model_validator

from eventum_plugins.output.formatters.encodings import Encoding


class Format(StrEnum):
    PLAIN = 'plain'
    JSON = 'json'
    JSON_BATCH = 'json-batch'
    TEMPLATE = 'template'
    TEMPLATE_BATCH = 'template-batch'
    EVENTUM_HTTP_INPUT = 'eventum-http-input'


class BaseFormatterConfig(BaseModel, ABC, frozen=True, extra='forbid'):
    """Base formatter config.

    Parameters
    ----------
    encoding : Encoding, default='utf-8'
        Target encoding

    separator : str, default=os.linesep
        Separator between events
    """
    encoding: Encoding = Field(default='utf_8')
    line_separator: str = Field(default=os.linesep)


class SimpleFormatterConfig(BaseFormatterConfig, frozen=True):
    """Config for formats without additional parameters.

    format : Literal[Format.PLAIN, Format.EVENTUM_HTTP_INPUT]
        Target format
    """
    format: Literal[Format.PLAIN, Format.EVENTUM_HTTP_INPUT]


class JsonFormatterConfig(BaseFormatterConfig, frozen=True):
    """Config for json-like formats.

    Parameters
    ----------
    format : Literal[Format.JSON, Format.JSON_BATCH]
        Target format

    indent : int, default=0
        Indentation size
    """
    format: Literal[Format.JSON, Format.JSON_BATCH]
    indent: int = Field(default=0, ge=0)


class TemplateFormatterConfig(BaseFormatterConfig, frozen=True):
    """Config for template-like formats.

    Parameters
    ----------
    format : Literal[Format.TEMPLATE, Format.TEMPLATE_BATCH]
        Target format

    template : str | None, default=None
        Template content

    template_path : str | None, default=None
        Template path

    Notes
    -----
    Template and template path are mutually exclusive parameters

    To access original event (for `template` mode) or events sequence
    (for `template-batch` mode) use `event` or `events` variable in
    template correspondingly
    """
    format: Literal[Format.TEMPLATE, Format.TEMPLATE_BATCH]
    template: str | None = Field(default=None, min_length=1)
    template_path: str | None = Field(default=None, min_length=1)

    @model_validator(mode='after')
    def validate_template_or_path_provided(self) -> Self:
        if self.template is None and self.template_path is None:
            raise ValueError('Template or template path must be provided')

        if self.template is not None and self.template_path is not None:
            raise ValueError(
                'Template or template path must be provided, but not both'
            )

        return self


FormatterT = (
    SimpleFormatterConfig | JsonFormatterConfig | TemplateFormatterConfig
)


class FormatterConfig(RootModel):
    root: FormatterT = Field(discriminator='format')
