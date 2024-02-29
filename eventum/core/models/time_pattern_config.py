from datetime import datetime, timedelta, time
from enum import StrEnum
from typing import Annotated, Any, TypeAlias

from pydantic import BaseModel, BeforeValidator

from eventum.utils.relative_time import parse_relative_time


class TimeUnit(StrEnum):
    SECONDS = 'seconds'
    MINUTES = 'minutes'
    HOURS = 'hours'
    DAYS = 'days'


class Distribution(StrEnum):
    RANDOM = 'Random'
    BETA = 'Beta'
    LINEAR = 'Linear'
    GAUSSIAN = 'Gaussian'


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
    interval: int
    unit: TimeUnit
    start: time | datetime | TimeKeyword | RelativeTime
    end: time | datetime | TimeKeyword | RelativeTime


class MultiplierConfig(BaseModel):
    ratio: int


class RandomizerConfig(BaseModel):
    deviation: int
    direction: RandomizerDirection


class BetaDistributionParameters(BaseModel):
    a: float
    b: float


DistributionParameters: TypeAlias = (
    BetaDistributionParameters | None
)


class SpreaderConfig(BaseModel):
    distribution: Distribution
    parameters: DistributionParameters


class TimePatternConfig(BaseModel):
    label: str
    oscillator: OscillatorConfig
    multiplier: MultiplierConfig
    randomizer: RandomizerConfig
    spreader: SpreaderConfig
