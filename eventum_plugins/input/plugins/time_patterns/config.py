
from enum import StrEnum
from typing import Any, TypeAlias
from warnings import warn

from pydantic import BaseModel, Field, field_validator, model_validator

from eventum_plugins.input.base.config import InputPluginConfig
from eventum_plugins.input.fields import VersatileDatetimeStrict
from eventum_plugins.input.mixins import DaterangeValidatorMixin


class TimeUnit(StrEnum):
    SECONDS = 'seconds'
    MINUTES = 'minutes'
    HOURS = 'hours'
    DAYS = 'days'


class Distribution(StrEnum):
    UNIFORM = 'uniform'
    TRIANGULAR = 'triangular'
    BETA = 'beta'


class RandomizerDirection(StrEnum):
    DECREASE = 'decrease'
    INCREASE = 'increase'
    MIXED = 'mixed'


class OscillatorConfig(
    DaterangeValidatorMixin,
    BaseModel,
    extra='forbid',
    frozen=True
):
    period: int = Field(..., ge=1)
    unit: TimeUnit
    start: VersatileDatetimeStrict = Field(..., union_mode='left_to_right')
    end: VersatileDatetimeStrict = Field(..., union_mode='left_to_right')


class MultiplierConfig(BaseModel, extra='forbid', frozen=True):
    ratio: int = Field(..., ge=1)


class RandomizerConfig(BaseModel, extra='forbid', frozen=True):
    deviation: float = Field(..., ge=0, le=1)
    direction: RandomizerDirection
    sampling: int = Field(1024, ge=256)

    # XXX: Remove in 1.3.0
    @field_validator('direction', mode='before')
    def convert_to_new_format(v: Any) -> Any:
        if not isinstance(v, str):
            return v

        if v[0].isupper():
            warn(
                'Capitalized options in "time_patterns" input plugin config '
                'are deprecated and their support will be removed in version '
                f'1.3.0. Use lowercase instead ("{v}" -> "{v.lower()}").',
                DeprecationWarning
            )
            return v.lower()

        return v


class BetaDistributionParameters(BaseModel, extra='forbid', frozen=True):
    a: float = Field(..., ge=0)
    b: float = Field(..., ge=0)


class TriangularDistributionParameters(BaseModel, extra='forbid', frozen=True):
    left: float = Field(..., ge=0, lt=1)
    mode: float = Field(..., ge=0, le=1)
    right: float = Field(..., gt=0, le=1)

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
    low: float = Field(..., ge=0, lt=1)
    high: float = Field(..., gt=0, le=1)

    @model_validator(mode='after')
    def validate_points(self):
        if self.low < self.high:
            return self
        raise ValueError(
            'Values do not comply "low < high" condition'
        )


DistributionParameters: TypeAlias = (
    UniformDistributionParameters |
    TriangularDistributionParameters |
    BetaDistributionParameters
)


class SpreaderConfig(BaseModel, extra='forbid', frozen=True):
    _DISTRIBUTION_PARAMETERS_MAP = {
        Distribution.UNIFORM: UniformDistributionParameters,
        Distribution.TRIANGULAR: TriangularDistributionParameters,
        Distribution.BETA: BetaDistributionParameters
    }

    distribution: Distribution
    parameters: DistributionParameters

    @model_validator(mode='after')
    def validate_parameters_model(self):
        if self.distribution not in self._DISTRIBUTION_PARAMETERS_MAP:
            raise NotImplementedError

        expected_model = self._DISTRIBUTION_PARAMETERS_MAP[self.distribution]

        if isinstance(self.parameters, expected_model):
            return self

        raise ValueError(
            f'Improper parameters model for "{self.distribution}" distribution'
        )

    # XXX: Remove in 1.3.0
    @field_validator('distribution', mode='before')
    def convert_to_new_format(v: Any) -> Any:
        if not isinstance(v, str):
            return v

        if v[0].isupper():
            warn(
                'Capitalized options in "time_patterns" input plugin config '
                'are deprecated and their support will be removed in version '
                f'1.3.0. Use lowercase instead ("{v}" -> "{v.lower()}").',
                DeprecationWarning
            )
            return v.lower()

        return v


class TimePatternConfig(BaseModel, extra='forbid', frozen=True):
    label: str = Field(..., min_length=1)
    oscillator: OscillatorConfig
    multiplier: MultiplierConfig
    randomizer: RandomizerConfig
    spreader: SpreaderConfig


class TimePatternsInputPluginConfig(InputPluginConfig, frozen=True):
    configs: list[str] = Field(..., min_length=1)
