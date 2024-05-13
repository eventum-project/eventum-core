from enum import StrEnum
from typing import Any, TypeAlias

from pydantic import BaseModel, Field, field_validator


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


EventConfig: TypeAlias = (
    JinjaEventConfig
)
