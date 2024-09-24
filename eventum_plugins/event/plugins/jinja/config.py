

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import (BaseModel, Field, RootModel, StringConstraints,
                      field_validator)

from eventum_plugins.event.base.config import EventPluginConfig


class SampleType(StrEnum):
    CSV = 'csv'
    ITEMS = 'items'


class CSVSampleConfig(BaseModel, frozen=True, extra='forbid'):
    type: Literal[SampleType.CSV]
    header: bool = False
    delimiter: str = Field(',', min_length=1)
    source: str = Field(..., pattern=r'.*\.csv')


class ItemsSampleConfig(BaseModel, frozen=True, extra='forbid'):
    type: Literal[SampleType.ITEMS]
    source: list[str] = Field(..., min_length=1)


class SampleConfig(RootModel, frozen=True):
    root: CSVSampleConfig | ItemsSampleConfig = Field(discriminator='type')


class TemplatePickingMode(StrEnum):
    ALL = 'all'
    ANY = 'any'
    CHANCE = 'chance'
    SPIN = 'spin'
    FSM = 'fsm'


TemplatePath = Annotated[str, StringConstraints(pattern=r'.*\.jinja')]


class TemplateConfigForGeneralModes(BaseModel, frozen=True, extra='forbid'):
    source: TemplatePath | list[TemplatePath] = Field(..., min_length=1)


class TemplateConfigForChanceMode(TemplateConfigForGeneralModes, frozen=True):
    chance: float = Field(..., gt=0.0)


class Condition(BaseModel, frozen=True, extra='forbid'):
    ...


class TemplateTransition(BaseModel, frozen=True, extra='forbid'):
    to: str = Field(..., min_length=1)
    when: Condition


class TemplateConfigForFSMMode(TemplateConfigForGeneralModes, frozen=True):
    transition: TemplateTransition | None = None
    initial: bool = False


class JinjaEventConfigCommonFields(BaseModel, frozen=True, extra='forbid'):
    params: dict
    samples: dict[str, SampleConfig]


class JinjaEventConfigForGeneralModes(
    EventPluginConfig,
    JinjaEventConfigCommonFields,
    frozen=True
):
    mode: Literal[
        TemplatePickingMode.ALL,
        TemplatePickingMode.ANY,
        TemplatePickingMode.SPIN
    ]
    templates: list[
        dict[str, TemplateConfigForGeneralModes]
    ] = Field(..., min_length=1)


class JinjaEventConfigForChanceMode(
    EventPluginConfig,
    JinjaEventConfigCommonFields,
    frozen=True
):
    mode: Literal[TemplatePickingMode.CHANCE]
    templates: list[
        dict[str, TemplateConfigForChanceMode]
    ] = Field(..., min_length=1)


class JinjaEventConfigForFSMMode(
    EventPluginConfig,
    JinjaEventConfigCommonFields,
    frozen=True
):
    mode: Literal[TemplatePickingMode.FSM]
    templates: list[
        dict[str, TemplateConfigForFSMMode]
    ] = Field(..., min_length=1)

    @field_validator('templates')
    def validate_single_initial(
        cls,
        v: list[dict[str, TemplateConfigForFSMMode]]
    ) -> list[dict[str, TemplateConfigForFSMMode]]:
        initial_encountered = False
        for template_info in v:
            config = next(iter(template_info.values()))

            if config.initial and initial_encountered:
                raise ValueError('Only one template can be initial')

            if config.initial:
                initial_encountered = True

        return v


class JinjaEventConfig(RootModel, frozen=True):
    root: (
        JinjaEventConfigForGeneralModes
        | JinjaEventConfigForChanceMode
        | JinjaEventConfigForFSMMode
    ) = Field(discriminator='mode')
