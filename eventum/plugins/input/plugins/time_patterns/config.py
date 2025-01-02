
from abc import ABC
from enum import StrEnum
from typing import Literal, TypeAlias

from pydantic import BaseModel, Field, model_validator

from eventum.plugins.input.base.config import InputPluginConfig
from eventum.plugins.input.fields import VersatileDatetimeStrict
from eventum.plugins.input.mixins import DaterangeValidatorMixin


class TimeUnit(StrEnum):
    """Time units for oscillator."""
    WEEKS = 'weeks'
    DAYS = 'days'
    HOURS = 'hours'
    MINUTES = 'minutes'
    SECONDS = 'seconds'
    MILLISECONDS = 'milliseconds'
    MICROSECONDS = 'microseconds'


class Distribution(StrEnum):
    """Distributions for spreader."""
    UNIFORM = 'uniform'
    TRIANGULAR = 'triangular'
    BETA = 'beta'


class RandomizerDirection(StrEnum):
    """Directions for randomizer."""
    DECREASE = 'decrease'
    INCREASE = 'increase'
    MIXED = 'mixed'


class OscillatorConfig(
    DaterangeValidatorMixin,
    BaseModel,
    extra='forbid',
    frozen=True
):
    """Configuration of oscillator.

    Attributes
    ----------
    period : float
        Duration of one period

    unit : TimeUnit
        Time unit of the period

    start : VersatileDatetimeStrict
        Start time of the distribution;
        if relative time is provided current time used as relative base

    end : VersatileDatetimeStrict
        End time of the distribution;
        if relative time is provided start time of distribution used as
        relative base
    """
    period: float = Field(gt=0)
    unit: TimeUnit
    start: VersatileDatetimeStrict = Field(union_mode='left_to_right')
    end: VersatileDatetimeStrict = Field(union_mode='left_to_right')


class MultiplierConfig(BaseModel, extra='forbid', frozen=True):
    """Configuration of multiplier.

    Attributes
    ----------
    ratio : int
        Multiplication ratio
    """
    ratio: int = Field(ge=1)


class RandomizerConfig(BaseModel, extra='forbid', frozen=True):
    """Configuration of randomizer.

    Attributes
    ----------
    deviation : float
        Deviation ratio

    direction : RandomizerDirection
        Direction of deviation

    sampling : int, default=1024
        Size of sample with random deviation ratios
    """
    deviation: float = Field(ge=0, le=1)
    direction: RandomizerDirection
    sampling: int = Field(default=1024, ge=16)


class BetaDistributionParameters(BaseModel, extra='forbid', frozen=True):
    """Configuration of parameters for beta distribution.

    Attributes
    ----------
    a : float
        Parameter alpha for the distribution

    b : float
        Parameter beta for the distribution
    """
    a: float = Field(ge=0)
    b: float = Field(ge=0)


class TriangularDistributionParameters(BaseModel, extra='forbid', frozen=True):
    """Configuration of parameters for triangular distribution.

    Attributes
    ----------
    left : float
        Left edge of the distribution

    mode : float
        Mode position of the distribution

    right : float
        Right edge of the distribution
    """
    left: float = Field(ge=0, lt=1)
    mode: float = Field(ge=0, le=1)
    right: float = Field(gt=0, le=1)

    @model_validator(mode='after')
    def validate_points(self):
        if (
            self.left <= self.mode <= self.right
            and not (self.left == self.mode == self.right)
        ):
            return self
        raise ValueError(
            'Values do not comply "left <= mode <= right" condition'
        )


class UniformDistributionParameters(BaseModel, extra='forbid', frozen=True):
    """Configuration of parameters for uniform distribution.

    Attributes
    ----------
    low : float
        Low edge of the distribution

    high : float
        High edge of the distribution
    """
    low: float = Field(ge=0, lt=1)
    high: float = Field(gt=0, le=1)

    @model_validator(mode='after')
    def validate_points(self):
        if self.low < self.high:
            return self
        raise ValueError(
            'Values do not comply "low < high" condition'
        )


class BaseSpreaderConfig(ABC, BaseModel, extra='forbid', frozen=True):
    """Configuration of spreader.

    Attributes
    ----------
    distribution: Distribution
        Distribution function for spreading

    parameters: DistributionParameters
        Parameters of distribution
    """
    ...


class UniformSpreaderConfig(BaseSpreaderConfig, frozen=True):
    distribution: Literal[Distribution.UNIFORM]
    parameters: UniformDistributionParameters


class TriangularSpreaderConfig(BaseSpreaderConfig, frozen=True):
    distribution: Literal[Distribution.TRIANGULAR]
    parameters: TriangularDistributionParameters


class BetaSpreaderConfig(BaseSpreaderConfig, frozen=True):
    distribution: Literal[Distribution.BETA]
    parameters: BetaDistributionParameters


SpreaderConfig: TypeAlias = (
    UniformSpreaderConfig | TriangularSpreaderConfig | BetaSpreaderConfig
)


class TimePatternConfig(InputPluginConfig, extra='forbid', frozen=True):
    """Configuration of a single time pattern.

    Attributes
    ----------
    label: str
        Label with a description

    oscillator: OscillatorConfig
        Configuration of oscillator

    multiplier: MultiplierConfig
        Configuration of multiplier

    randomizer: RandomizerConfig
        Configuration of randomizer

    spreader: SpreaderConfig
        Configuration of spreader
    """
    label: str = Field(min_length=1)
    oscillator: OscillatorConfig
    multiplier: MultiplierConfig
    randomizer: RandomizerConfig
    spreader: SpreaderConfig = Field(discriminator='distribution')


class TimePatternsInputPluginConfig(InputPluginConfig, frozen=True):
    """Configuration for `time_patterns` input plugin.

    Attributes
    ----------
    patterns : list[str]
        File paths to time pattern configurations

    ordered_merging : bool, default = False
        Whether to merge timestamps from different patterns with
        keeping resulting timestamps sequence ordered (actual only for
        live mode with usage of multiple configs)
    """

    patterns: list[str] = Field(min_length=1)
    ordered_merging: bool = False
