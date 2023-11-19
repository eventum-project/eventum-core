from dataclasses import dataclass
from datetime import datetime
from enum import Enum


@dataclass
class DistributionParameters:
    pass


class TimeUnit(Enum):
    SECONDS = 's'
    MINUTES = 'm'
    HOURS = 'h'
    DAYS = 'd'


class DistributionFunction(Enum):
    LINEAR = 'Linear'
    RANDOM = 'Random'
    GAUSSIAN = 'Gaussian'


class RandomizerDirection(Enum):
    DECREASE = 'Decrease'
    INCREASE = 'Increase'
    MIXED = 'Mixed'


@dataclass
class OscillatorConfig:
    interval: int
    unit: TimeUnit | str
    start: datetime | str
    end: datetime | str


@dataclass
class MultiplierConfig:
    ratio: int


@dataclass
class RandomizerConfig:
    deviation: int
    direction: RandomizerDirection | str


@dataclass
class SpreaderConfig:
    function: DistributionFunction | str
    parameters: DistributionParameters


@dataclass
class TimePatternConfig:
    label: str
    oscillator: OscillatorConfig
    multiplier: MultiplierConfig
    randomizer: RandomizerConfig
    spreader: SpreaderConfig
