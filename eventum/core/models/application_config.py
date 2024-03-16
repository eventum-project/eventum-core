import os
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any, TypeAlias

from pydantic import (BaseModel, BeforeValidator, field_validator)

from eventum.utils.fs import validate_yaml_filename


class InputType(StrEnum):
    TIMESTAMPS = 'timestamps'
    PATTERNS = 'patterns'
    CRON = 'cron'
    SAMPLE = 'sample'


def try_parse_datetime(obj: Any) -> Any | list[datetime]:
    if isinstance(obj, list):
        casted_list = []
        for el in obj:
            try:
                casted_list.append(datetime.fromisoformat(el))
            except (ValueError, TypeError):
                return obj

        return casted_list

    return obj


def validate_filenames(obj: Any) -> Any:
    if isinstance(obj, list):
        for el in obj:
            if not isinstance(el, str):
                return obj

            validate_yaml_filename(os.path.basename(el))

    return obj


TimestampsInputConfig = Annotated[
    list[datetime], BeforeValidator(try_parse_datetime)
]

PatternsInputConfig = Annotated[
    list[str], BeforeValidator(validate_filenames)
]


class CronInputConfig(BaseModel):
    expression: str
    count: int


class SampleInputConfig(BaseModel):
    count: int


class SampleType(StrEnum):
    CSV = 'csv'
    ITEMS = 'items'


class CSVSampleConfig(BaseModel):
    type: SampleType
    header: bool
    delimiter: str = ','
    source: str


class ItemsSampleConfig(BaseModel):
    type: SampleType
    source: list[str]


class TemplatePickingMode(StrEnum):
    ALL = 'all'
    ANY = 'any'
    CHANCE = 'chance'
    SPIN = 'spin'


class TemplateConfig(BaseModel):
    template: str
    chance: float = 1.0


class SubprocessConfig(BaseModel):
    config: str


class JinjaEventConfig(BaseModel):
    params: dict
    samples: dict[str, ItemsSampleConfig | CSVSampleConfig]
    mode: TemplatePickingMode
    templates: dict[str, TemplateConfig]
    subprocesses: dict[str, SubprocessConfig]


class OutputType(StrEnum):
    STDOUT = 'stdout'
    FILE = 'file'


class OutputFormat(StrEnum):
    ORIGINAL = 'original'
    JSON_LINES = 'json-lines'


class StdOutOutputConfig(BaseModel):
    format: OutputFormat = OutputFormat.ORIGINAL


class FileOutputConfig(BaseModel):
    path: str
    format: OutputFormat = OutputFormat.ORIGINAL


InputConfig: TypeAlias = (
    TimestampsInputConfig | PatternsInputConfig
    | CronInputConfig | SampleInputConfig
)

OutputConfig: TypeAlias = (
    StdOutOutputConfig | FileOutputConfig
)


InputConfigMapping: TypeAlias = dict[InputType, InputConfig]
OutputConfigMapping: TypeAlias = dict[OutputType, OutputConfig]


class ApplicationConfig(BaseModel):
    input: InputConfigMapping
    event: JinjaEventConfig
    output: OutputConfigMapping

    @field_validator('input')
    def validate_input(cls, v: Any):
        if len(v) != 1:
            raise ValueError(
                f'Only one input must be adjusted but you have {len(v)}'
            )

        return v

    @field_validator('output')
    def validate_output(cls, v: Any):
        if len(v) == 0:
            raise ValueError(
                'At least one output must be adjusted'
            )

        return v
