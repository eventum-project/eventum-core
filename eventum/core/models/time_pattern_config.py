from datetime import datetime, timedelta, time
from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator

from eventum.utils.relative_time import parse_relative_time


class TimeUnit(StrEnum):
    SECONDS = 'seconds'
    MINUTES = 'minutes'
    HOURS = 'hours'
    DAYS = 'days'


class DistributionFunction(StrEnum):
    LINEAR = 'Linear'
    RANDOM = 'Random'
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


class SpreaderConfig(BaseModel):
    function: DistributionFunction
    parameters: dict = {}


class TimePatternConfig(BaseModel):
    label: str
    oscillator: OscillatorConfig
    multiplier: MultiplierConfig
    randomizer: RandomizerConfig
    spreader: SpreaderConfig
