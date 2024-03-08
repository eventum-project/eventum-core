import os
from enum import StrEnum
from typing import Annotated, Any, TypeAlias
from datetime import datetime

from pydantic import BaseModel, BeforeValidator, model_validator
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


class TemplateCodecs(StrEnum):
    JSON = 'json'
    PLAIN = 'plain'


class TemplateConfig(BaseModel):
    codec: TemplateCodecs
    chance: float | None = None


class SubprocessConfig(BaseModel):
    config: str
    detach: bool


class EventConfig(BaseModel):
    params: dict
    samples: dict[str, ItemsSampleConfig | CSVSampleConfig]
    mode: TemplatePickingMode
    templates: dict[str, TemplateConfig]
    subprocesses: dict[str, SubprocessConfig]

    @model_validator(mode='after')
    def validate_templates(self):
        for template in self.templates.values():
            if self.mode == TemplatePickingMode.CHANCE:
                if template.chance is None:
                    raise ValueError(
                        'Parameter "chance" must be set for specified template'
                        ' picking mode'
                    )
            else:
                if template.chance is not None:
                    raise ValueError(
                        'Parameter "chance" is not applicable for specified'
                        ' template picking mode'
                    )

        return self


class OutputType(StrEnum):
    STDOUT = 'stdout'
    FILE = 'file'


class StdOutOutputConfig(BaseModel):
    pass


class FileOutputConfig(BaseModel):
    path: str


InputConfig: TypeAlias = (
    TimestampsInputConfig | PatternsInputConfig
    | SampleInputConfig | CronInputConfig
)

OutputConfig: TypeAlias = (
    StdOutOutputConfig | FileOutputConfig
)


InputConfigMapping: TypeAlias = dict[InputType, InputConfig]
OutputConfigMapping: TypeAlias = dict[OutputType, OutputConfig]


class ApplicationConfig(BaseModel):
    input: InputConfigMapping
    event: EventConfig
    output: OutputConfigMapping
