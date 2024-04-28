from datetime import datetime, time
from enum import StrEnum
from typing import Annotated, Any, TypeAlias, assert_never

from pydantic import (BaseModel, AfterValidator, field_validator,
                      model_validator)

from eventum.utils.relative_time import parse_relative_time


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


def check_relative_time(obj: Any) -> str:
    if isinstance(obj, str):
        parse_relative_time(obj)

    return obj


RelativeTime = Annotated[str, AfterValidator(check_relative_time)]


class OscillatorConfig(BaseModel):
    period: float
    unit: TimeUnit
    start: time | datetime | TimeKeyword | RelativeTime
    end: time | datetime | TimeKeyword | RelativeTime

    def __hash__(self) -> int:
        return hash(
            (
                self.period,
                self.unit,
                self.start,
                self.end
            )
        )


class MultiplierConfig(BaseModel):
    ratio: int

    def __hash__(self) -> int:
        return hash(self.ratio)

    @field_validator('ratio')
    def validate_ratio(cls, v: Any):
        if v <= 0:
            raise ValueError('Ratio must be greater or equal to 1')
        return v


class RandomizerConfig(BaseModel):
    deviation: float
    direction: RandomizerDirection

    def __hash__(self) -> int:
        return hash((self.deviation, self.direction))

    @field_validator('deviation')
    def validate_deviation(cls, v: Any):
        if 0 <= v <= 1:
            return v
        raise ValueError('Deviation must be in range [0, 1]')


class BetaDistributionParameters(BaseModel):
    a: float
    b: float

    def __hash__(self) -> int:
        return hash((self.a, self.b))

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

    def __hash__(self) -> int:
        return hash((self.left, self.mode, self.right))


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

    def __hash__(self) -> int:
        return hash((self.low, self.high))


DistributionParameters: TypeAlias = (
    UniformDistributionParameters |
    TriangularDistributionParameters |
    BetaDistributionParameters
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

        raise ValueError(
            f'Improper parameters model for "{self.distribution}" distribution'
        )

    def __hash__(self) -> int:
        return hash((self.distribution, self.parameters))


class TimePatternConfig(BaseModel):
    label: str
    oscillator: OscillatorConfig
    multiplier: MultiplierConfig
    randomizer: RandomizerConfig
    spreader: SpreaderConfig

    @field_validator('label')
    def validate_high(cls, v: Any):
        if v:
            return v

        raise ValueError('Label cannot be empty string')
