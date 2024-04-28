import os
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any, TypeAlias

from pydantic import (BaseModel, BeforeValidator, field_validator)

from eventum.utils.fs import validate_yaml_filename


class InputName(StrEnum):
    TIMESTAMPS = 'timestamps'
    TIME_PATTERNS = 'time_patterns'
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

TimePatternsInputConfig = Annotated[
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
    header: bool = False
    delimiter: str = ','
    source: str

    @field_validator('source')
    def validate_source(cls, v: Any):
        if v:
            return v

        raise ValueError('Source cannot be empty string')


class ItemsSampleConfig(BaseModel):
    type: SampleType
    source: list[str]

    @field_validator('source')
    def validate_source(cls, v: Any):
        if v:
            return v
        raise ValueError('Source cannot be empty list')


class TemplatePickingMode(StrEnum):
    ALL = 'all'
    ANY = 'any'
    CHANCE = 'chance'
    SPIN = 'spin'


class TemplateConfig(BaseModel):
    template: str
    chance: float = 1.0


class JinjaEventConfig(BaseModel):
    params: dict
    samples: dict[str, ItemsSampleConfig | CSVSampleConfig]
    mode: TemplatePickingMode
    templates: dict[str, TemplateConfig]


class OutputName(StrEnum):
    STDOUT = 'stdout'
    NULL = 'null'
    FILE = 'file'
    OPENSEARCH = 'opensearch'


class OutputFormat(StrEnum):
    ORIGINAL = 'original'
    JSON_LINES = 'json-lines'


class StdOutOutputConfig(BaseModel):
    format: OutputFormat = OutputFormat.ORIGINAL


class NullOutputConfig(BaseModel):
    ...


class FileOutputConfig(BaseModel):
    path: str
    format: OutputFormat = OutputFormat.ORIGINAL

    @field_validator('path')
    def validate_path(cls, v: Any):
        if v:
            return v
        raise ValueError('Path cannot be empty string')


class OpensearchOutputConfig(BaseModel):
    hosts: list[str]
    user: str
    index: str
    verify_ssl: bool
    ca_cert_path: str | None = None

    @field_validator('hosts')
    def validate_hosts(cls, v: Any):
        if v:
            return v
        raise ValueError('Hosts cannot be empty list')

    @field_validator('user')
    def validate_user(cls, v: Any):
        if v:
            return v
        raise ValueError('User cannot be empty string')

    @field_validator('index')
    def validate_index(cls, v: Any):
        if v:
            return v
        raise ValueError('User cannot be empty string')


InputConfig: TypeAlias = (
    TimestampsInputConfig | TimePatternsInputConfig
    | CronInputConfig | SampleInputConfig
)

EventConfig: TypeAlias = (
    JinjaEventConfig
)

OutputConfig: TypeAlias = (
    OpensearchOutputConfig | FileOutputConfig | StdOutOutputConfig
    | NullOutputConfig
)


InputConfigMapping: TypeAlias = dict[InputName, InputConfig]
OutputConfigMapping: TypeAlias = dict[OutputName, OutputConfig]


class ApplicationConfig(BaseModel):
    input: InputConfigMapping
    event: EventConfig
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
        if v:
            return v
        raise ValueError('At least one output must be adjusted')
