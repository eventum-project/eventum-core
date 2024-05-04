from datetime import datetime, time
from enum import StrEnum
from typing import Annotated, Any, TypeAlias, assert_never

from eventum.utils.relative_time import parse_relative_time
from pydantic import AfterValidator, BaseModel, Field, model_validator


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
    period: int = Field(..., ge=1)
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
    ratio: int = Field(..., ge=1)

    def __hash__(self) -> int:
        return hash(self.ratio)


class RandomizerConfig(BaseModel):
    deviation: float = Field(..., ge=0, le=1)
    direction: RandomizerDirection

    def __hash__(self) -> int:
        return hash((self.deviation, self.direction))


class BetaDistributionParameters(BaseModel):
    a: float = Field(..., ge=0)
    b: float = Field(..., ge=0)

    def __hash__(self) -> int:
        return hash((self.a, self.b))


class TriangularDistributionParameters(BaseModel):
    left: float = Field(..., ge=0, lt=1)
    mode: float = Field(..., ge=0, le=1)
    right: float = Field(..., gt=0, le=1)

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
    low: float = Field(..., ge=0, lt=1)
    high: float = Field(..., gt=0, le=1)

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
    label: str = Field(..., min_length=1)
    oscillator: OscillatorConfig
    multiplier: MultiplierConfig
    randomizer: RandomizerConfig
    spreader: SpreaderConfig
