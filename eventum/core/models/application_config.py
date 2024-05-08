import os
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any, TypeAlias

from croniter import croniter
from pydantic import BaseModel, BeforeValidator, Field, field_validator

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
    count: int = Field(..., gt=0)

    @field_validator('expression')
    def validate_expression(cls, v: Any):
        if croniter.is_valid(v):
            return v
        raise ValueError('Invalid cron expression')


class SampleInputConfig(BaseModel):
    count: int = Field(..., gt=0)


class SampleType(StrEnum):
    CSV = 'csv'
    ITEMS = 'items'


class CSVSampleConfig(BaseModel):
    type: SampleType
    header: bool = False
    delimiter: str = Field(',', min_length=1)
    source: str = Field(..., pattern=r'.*\.csv')

    @field_validator('type')
    def validate_type(cls, v: Any):
        if v == SampleType.CSV:
            return v

        raise ValueError(
            f'Type must be "{SampleType.CSV}" of {SampleType}'
        )


class ItemsSampleConfig(BaseModel):
    type: SampleType
    source: list[str] = Field(..., min_length=1)

    @field_validator('type')
    def validate_type(cls, v: Any):
        if v == SampleType.ITEMS:
            return v

        raise ValueError(
            f'Type must be "{SampleType.ITEMS}" of {SampleType}'
        )


class TemplatePickingMode(StrEnum):
    ALL = 'all'
    ANY = 'any'
    CHANCE = 'chance'
    SPIN = 'spin'


class TemplateConfig(BaseModel):
    template: str = Field(..., pattern=r'.*\.(jinja|j2)')
    chance: float = Field(1.0, gt=0.0)


class JinjaEventConfig(BaseModel):
    params: dict
    samples: dict[str, ItemsSampleConfig | CSVSampleConfig]
    mode: TemplatePickingMode
    templates: dict[str, TemplateConfig] = Field(..., min_length=1)


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
        if os.path.isabs(v):
            return v
        raise ValueError('Path must be absolute')


class OpensearchOutputConfig(BaseModel):
    hosts: list[str] = Field(..., min_length=1)
    user: str = Field(..., min_length=1)
    index: str = Field(..., min_length=1)
    verify_ssl: bool
    ca_cert_path: str | None = None


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
    input: InputConfigMapping = Field(..., min_length=1, max_length=1)
    event: EventConfig
    output: OutputConfigMapping = Field(..., min_length=1)
