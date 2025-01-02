from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any, Literal, Self

from pydantic import (BaseModel, Field, RootModel, StringConstraints,
                      field_validator, model_validator)

from eventum.plugins.event.base.config import EventPluginConfig
from eventum.plugins.event.plugins.jinja.fsm.fields import Condition
from eventum.plugins.event.plugins.jinja.mixins import (
    TemplateAliasesUniquenessValidatorMixin,
    TemplateSingleItemElementsValidatorMixin)


class SampleType(StrEnum):
    """Types of sample."""
    ITEMS = 'items'
    CSV = 'csv'
    JSON = 'json'


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
    source: tuple = Field(min_length=1)


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
    delimiter: str = Field(default=',', min_length=1)
    source: str = Field(pattern=r'.*\.csv')


class JSONSampleConfig(BaseModel, frozen=True, extra='forbid'):
    """Configuration of json sample.

    Attributes
    ----------
    type : Literal[SampleType.JSON]
        Discriminator field for sample configuration

    source : str
        Path to json file
    """
    type: Literal[SampleType.JSON]
    source: str = Field(pattern=r'.*\.json')


SampleConfigModel = (
    ItemsSampleConfig | CSVSampleConfig | JSONSampleConfig
)


class SampleConfig(RootModel, frozen=True):
    """Configuration of sample."""
    root: SampleConfigModel = Field(
        discriminator='type'
    )


class TemplatePickingMode(StrEnum):
    """Picking modes of templates.

    - `all` - render all templates at a time
    - `any` - render one randomly chosen template
    - `chance` - render one template depending on specified chances
    - `spin` - cyclically render one template after another
    - `fsm` - render template depending on current state
    - `chain` - cyclically render templates by user defined chain
    """
    ALL = 'all'
    ANY = 'any'
    CHANCE = 'chance'
    SPIN = 'spin'
    FSM = 'fsm'
    CHAIN = 'chain'


TemplatePath = Annotated[str, StringConstraints(pattern=r'.*\.jinja')]


class TemplateConfigForGeneralModes(BaseModel, frozen=True, extra='forbid'):
    """Template configuration for general picking modes.

    Attributes
    ----------
    template : TemplatePath
        Path to template
    """
    template: TemplatePath = Field(min_length=1)


class TemplateConfigForChanceMode(TemplateConfigForGeneralModes, frozen=True):
    """Template configuration for `chance` picking mode.

    Attributes
    ----------
    chance : float
        Proportional value of probability of rendering template
    """
    chance: float = Field(gt=0.0)


class TemplateTransition(BaseModel, frozen=True, extra='forbid'):
    """Transition configuration for `fsm` picking mode.

    Attributes
    ----------
    to : str
        Name of target state for transition

    when : Condition
        Condition for performing transition
    """
    to: str = Field(min_length=1)
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


class TemplateConfigForChainMode(TemplateConfigForGeneralModes, frozen=True):
    """Template configuration for `chain` picking mode.

    Attributes
    ----------
    chain : list[str]
        Chain of template aliases
    """
    chain: list[str] = Field(min_length=1)


class JinjaEventPluginConfigCommonFields(
    EventPluginConfig,
    frozen=True
):
    """Configuration common fields for `jinja` event plugin.

    Attributes
    ----------
    params : dict[str, Any]
        Constant parameters passed to templates

    sample : dict[str, SampleConfig]
        Samples passed to templates
    """
    params: dict[str, Any]
    samples: dict[str, SampleConfig]

    def get_picking_common_fields(self) -> dict[str, Any]:
        """Get common fields used in templates picking.

        Returns
        -------
        dict[str, Any]
            Field names to their values mapping
        """
        return dict()


class JinjaEventPluginConfigForGeneralModes(
    TemplateSingleItemElementsValidatorMixin,
    TemplateAliasesUniquenessValidatorMixin,
    JinjaEventPluginConfigCommonFields,
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
    ] = Field(min_length=1)


class JinjaEventPluginConfigForChanceMode(
    TemplateSingleItemElementsValidatorMixin,
    TemplateAliasesUniquenessValidatorMixin,
    JinjaEventPluginConfigCommonFields,
    frozen=True
):
    """Configuration for `jinja` event plugin for `chance` picking
    mode.

    Attributes
    ----------
    mode : Literal[TemplatePickingMode.CHANCE]
        Template picking mode

    templates : list[dict[str, TemplateConfigForChanceMode]]
        List of template configurations
    """
    mode: Literal[TemplatePickingMode.CHANCE]
    templates: list[
        dict[str, TemplateConfigForChanceMode]
    ] = Field(min_length=1)


class JinjaEventPluginConfigForFSMMode(
    TemplateSingleItemElementsValidatorMixin,
    TemplateAliasesUniquenessValidatorMixin,
    JinjaEventPluginConfigCommonFields,
    frozen=True
):
    """Configuration for `jinja` event plugin for `fsm` picking mode.

    Attributes
    ----------
    mode : Literal[TemplatePickingMode.FSM]
        Template picking mode

    templates : list[dict[str, TemplateConfigForFSMMode]]
        List of template configurations
    """
    mode: Literal[TemplatePickingMode.FSM]
    templates: list[
        dict[str, TemplateConfigForFSMMode]
    ] = Field(min_length=1)

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


class JinjaEventPluginConfigForChainMode(
    TemplateSingleItemElementsValidatorMixin,
    TemplateAliasesUniquenessValidatorMixin,
    JinjaEventPluginConfigCommonFields,
    frozen=True
):
    """Configuration for `jinja` event plugin for `chain` picking
    mode.

    Attributes
    ----------
    mode : Literal[TemplatePickingMode.CHAIN]
        Template picking mode

    templates : list[dict[str, TemplateConfigForGeneralModes]]
        List of template configurations
    """
    mode: Literal[TemplatePickingMode.CHAIN]
    chain: list[str] = Field(min_length=1)
    templates: list[
        dict[str, TemplateConfigForGeneralModes]
    ] = Field(min_length=1)

    @model_validator(mode='after')
    def validate_chain_aliases(self) -> Self:
        allowed_aliases = set(
            next(iter(template_info.keys()))
            for template_info in self.templates
        )
        chain_aliases = set(self.chain)

        if not allowed_aliases.issuperset(chain_aliases):
            unknown_aliases = allowed_aliases - chain_aliases
            raise ValueError(
                f'Unknown template aliases in chain: {unknown_aliases} '
            )

        return self

    def get_picking_common_fields(self) -> dict[str, Any]:
        fields = super().get_picking_common_fields()
        fields['chain'] = self.chain

        return fields


ConfigModel = (
    JinjaEventPluginConfigForGeneralModes
    | JinjaEventPluginConfigForChanceMode
    | JinjaEventPluginConfigForFSMMode
    | JinjaEventPluginConfigForChainMode
)


class JinjaEventPluginConfig(RootModel, frozen=True):
    """Configuration for `jinja` event plugin."""
    root: ConfigModel = Field(discriminator='mode')
