from enum import StrEnum
from typing import Any, Dict, TypeAlias

from pydantic import BaseModel, root_validator


class InputType(StrEnum):
    patterns = 'patterns'
    timestamps = 'timestamps'
    cron = 'cron'
    sample = 'sample'


PatternsInputConfig: TypeAlias = list[str]
TimestampsInputConfig: TypeAlias = list[str]


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
    header: bool | None = False
    separator: str | None = ','
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
    chance: int | None


class SubrocessConfig(BaseModel):
    config: str
    detach: bool


class EventConfig(BaseModel):
    params: dict
    samples: dict[str, ItemsSampleConfig | CSVSampleConfig]
    mode: TemplatePickingMode
    templates: dict[str, TemplateConfig]
    subprocesses: dict[str, SubrocessConfig]

    @root_validator
    def validate_templates_parameters(cls, values: Dict[str, Any]):
        for template in values['templates'].values():
            if values['mode'] == TemplatePickingMode.CHANCE:
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


class OutputType(StrEnum):
    STDOUT = 'stdout'
    FILE = 'file'


class StdOutOutputConfig(BaseModel):
    pass


class FileOutputConfig(BaseModel):
    path: str


InputConfigs: TypeAlias = (
    PatternsInputConfig | TimestampsInputConfig
    | SampleInputConfig | CronInputConfig
)

OutputConfigs: TypeAlias = (
    StdOutOutputConfig | FileOutputConfig
)


class ApplicationConfig(BaseModel):
    input: dict[InputType, InputConfigs]
    event: EventConfig
    output: dict[OutputType, OutputConfigs]
