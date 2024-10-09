from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import (BaseModel, Field, RootModel, StringConstraints,
                      field_validator)

from eventum_plugins.event.base.config import EventPluginConfig
from eventum_plugins.event.plugins.jinja.fsm.fields import Condition


class SampleType(StrEnum):
    """Types of sample."""
    CSV = 'csv'
    ITEMS = 'items'


class CSVSampleConfig(BaseModel, frozen=True, extra='forbid'):
    """Configuration of csv sample.

    Attributes
    ----------
    type : Literal[SampleType.CSV]
        Discriminator field for sample configuration

    header : bool, default=False
        Whether the provided csv sample includes header

    delimiter : str, default=','
        Delimiter for csv values

    source : str
        Path to csv file
    """
    type: Literal[SampleType.CSV]
    header: bool = False
    delimiter: str = Field(',', min_length=1)
    source: str = Field(..., pattern=r'.*\.csv')


class ItemsSampleConfig(BaseModel, frozen=True, extra='forbid'):
    """Configuration of sample of directly provided items.

    Attributes
    ----------
    type : Literal[SampleType.CSV]
        Discriminator field for sample configuration

    source : tuple
        List of sample items
    """
    type: Literal[SampleType.ITEMS]
    source: tuple[Any, ...] = Field(..., min_length=1)


class SampleConfig(RootModel, frozen=True):
    """Configuration of sample."""
    root: CSVSampleConfig | ItemsSampleConfig = Field(discriminator='type')


class TemplatePickingMode(StrEnum):
    """Picking modes of templates.

    - `all` - render all templates at a time
    - `any` - render one randomly chosen template
    - `chance` - render one template depending on specified chances
    - `spin` - render one template after another in turn
    - `fsm` - render template depending on current state
    """
    ALL = 'all'
    ANY = 'any'
    CHANCE = 'chance'
    SPIN = 'spin'
    FSM = 'fsm'


TemplatePath = Annotated[str, StringConstraints(pattern=r'.*\.jinja')]


class TemplateConfigForGeneralModes(BaseModel, frozen=True, extra='forbid'):
    """Template configuration for general picking modes.

    Attributes
    ----------
    source : TemplatePath | list[TemplatePath]
        Path or list of paths to templates
    """
    source: TemplatePath | list[TemplatePath] = Field(..., min_length=1)


class TemplateConfigForChanceMode(TemplateConfigForGeneralModes, frozen=True):
    """Template configuration for `chance` picking mode.

    Attributes
    ----------
    chance : float
        Proportional value of probability of rendering template
    """
    chance: float = Field(..., gt=0.0)


class TemplateTransition(BaseModel, frozen=True, extra='forbid'):
    """Transition configuration for `fsm` picking mode.

    Attributes
    ----------
    to : str
        Name of target state for transition

    when : Condition
        Condition for performing transition
    """
    to: str = Field(..., min_length=1)
    when: Condition


class TemplateConfigForFSMMode(TemplateConfigForGeneralModes, frozen=True):
    """Template configuration for `fsm` picking mode.

    Attributes
    ----------
    transition : TemplateTransition | None, default=None
        Transition configuration

    initial : bool, default=False
        Whether to define state as initial
    """
    transition: TemplateTransition | None = None
    initial: bool = False


class JinjaEventConfigCommonFields(BaseModel, frozen=True, extra='forbid'):
    """Configuration common fields for `jinja` event plugin.

    Attributes
    ----------
    params : dict
        Constant parameters passed to templates

    sample : dict[str, SampleConfig]
        Samples passed to templates
    """
    params: dict
    samples: dict[str, SampleConfig]


class JinjaEventConfigForGeneralModes(
    EventPluginConfig,
    JinjaEventConfigCommonFields,
    frozen=True
):
    """Configuration for `jinja` event plugin for general picking
    modes.

    Attributes
    ----------
    mode : Literal[\
        TemplatePickingMode.ALL,\
        TemplatePickingMode.ANY,\
        TemplatePickingMode.SPIN\
    ]
        Template picking mode

    templates : list[dict[str, TemplateConfigForGeneralModes]]
        List of template configurations
    """
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
    """Configuration for `jinja` event plugin for `chance` picking
    mode.

    Attributes
    ----------
    mode : Literal[TemplatePickingMode.CHANCE]
        Template picking mode

    templates : list[dict[str, TemplateConfigForGeneralModes]]
        List of template configurations
    """
    mode: Literal[TemplatePickingMode.CHANCE]
    templates: list[
        dict[str, TemplateConfigForChanceMode]
    ] = Field(..., min_length=1)


class JinjaEventConfigForFSMMode(
    EventPluginConfig,
    JinjaEventConfigCommonFields,
    frozen=True
):
    """Configuration for `jinja` event plugin for `fsm` picking mode.

    Attributes
    ----------
    mode : Literal[TemplatePickingMode.FSM]
        Template picking mode

    templates : list[dict[str, TemplateConfigForGeneralModes]]
        List of template configurations
    """
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
    """Configuration for `jinja` event plugin."""
    root: (
        JinjaEventConfigForGeneralModes
        | JinjaEventConfigForChanceMode
        | JinjaEventConfigForFSMMode
    ) = Field(discriminator='mode')
