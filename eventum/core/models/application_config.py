from enum import StrEnum
from typing import TypeAlias

from pydantic import BaseModel, model_validator


class InputType(StrEnum):
    PATTERNS = 'patterns'
    TIMESTAMPS = 'timestamps'
    CRON = 'cron'
    SAMPLE = 'sample'


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
    header: bool
    separator: str | None
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
    def validate_templates_parameters(self):
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


class OutputType(StrEnum):
    STDOUT = 'stdout'
    FILE = 'file'


class StdOutOutputConfig(BaseModel):
    pass


class FileOutputConfig(BaseModel):
    path: str


InputConfig: TypeAlias = (
    PatternsInputConfig | TimestampsInputConfig
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
