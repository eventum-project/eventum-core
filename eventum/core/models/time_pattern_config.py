from datetime import datetime, time, timedelta
from enum import StrEnum
from typing import Annotated, Any, TypeAlias, assert_never

from eventum.utils.relative_time import parse_relative_time
from pydantic import (BaseModel, BeforeValidator, field_validator,
                      model_validator)


class TimeUnit(StrEnum):
    SECONDS = 'seconds'
    MINUTES = 'minutes'
    HOURS = 'hours'
    DAYS = 'days'


class Distribution(StrEnum):
    UNIFORM = 'Uniform'
    TRIANGULAR = 'Triangular'
    BETA = 'Beta'


class RandomizerDirection(StrEnum):
    DECREASE = 'Decrease'
    INCREASE = 'Increase'
    MIXED = 'Mixed'


class TimeKeyword(StrEnum):
    NOW = 'now'
    NEVER = 'never'


def try_parse_relative_time(obj: Any) -> Any | timedelta:
    if isinstance(obj, str):
        try:
            return parse_relative_time(obj)
        except ValueError:
            return obj

    return obj


RelativeTime = Annotated[timedelta, BeforeValidator(try_parse_relative_time)]


class OscillatorConfig(BaseModel):
    period: float
    unit: TimeUnit
    start: time | datetime | TimeKeyword | RelativeTime
    end: time | datetime | TimeKeyword | RelativeTime


class MultiplierConfig(BaseModel):
    ratio: int


class RandomizerConfig(BaseModel):
    deviation: float
    direction: RandomizerDirection


class BetaDistributionParameters(BaseModel):
    a: float
    b: float

    @field_validator('a')
    def validate_a(cls, v: Any):
        if v >= 0:
            return v
        raise ValueError('"a" must be greater or equal to 0')

    @field_validator('b')
    def validate_b(cls, v: Any):
        if v >= 0:
            return v
        raise ValueError('"b" must be greater or equal to 0')


class TriangularDistributionParameters(BaseModel):
    left: float
    mode: float
    right: float

    @field_validator('left')
    def validate_left(cls, v: Any):
        if 0 <= v < 1:
            return v
        raise ValueError('"left" must be in [0; 1) range')

    @field_validator('mode')
    def validate_mode(cls, v: Any):
        if 0 <= v <= 1:
            return v
        raise ValueError('"mode" must be in [0; 1] range')

    @field_validator('right')
    def validate_right(cls, v: Any):
        if 0 < v <= 1:
            return v
        raise ValueError('"right" must be in (0; 1] range')

    @model_validator(mode='after')
    def validate_points(self):
        if self.left <= self.mode <= self.right:
            return self
        raise ValueError(
            'Values do not comply "left <= mode <= right" condition'
        )


class UniformDistributionParameters(BaseModel):
    low: float
    high: float

    @field_validator('low')
    def validate_low(cls, v: Any):
        if 0 <= v < 1:
            return v
        raise ValueError('"low" must be in [0; 1) range')

    @field_validator('high')
    def validate_high(cls, v: Any):
        if 0 < v <= 1:
            return v
        raise ValueError('"high" must be in (0; 1] range')

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
    BetaDistributionParameters |
    None
)


class SpreaderConfig(BaseModel):
    distribution: Distribution
    parameters: DistributionParameters

    @model_validator(mode='after')
    def validate_parameters_model(self):
        match self.distribution:
            case Distribution.UNIFORM:
                expected_params_model = UniformDistributionParameters
            case Distribution.TRIANGULAR:
                expected_params_model = TriangularDistributionParameters
            case Distribution.BETA:
                expected_params_model = BetaDistributionParameters
            case distribution:
                assert_never(distribution)

        if isinstance(self.parameters, expected_params_model):
            return self

        raise TypeError(
            f'Improper parameters model for "{self.distribution}" distribution'
        )


class TimePatternConfig(BaseModel):
    label: str
    oscillator: OscillatorConfig
    multiplier: MultiplierConfig
    randomizer: RandomizerConfig
    spreader: SpreaderConfig
