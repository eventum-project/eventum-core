from abc import ABC


class BaseTimeDistribution(ABC):
    ...


class CronTimeDistribution(BaseTimeDistribution):
    ...


class ManualTimeDistribution(BaseTimeDistribution):
    ...


class SampleTimeDistribution(BaseTimeDistribution):
    ...


class TimePatternDistribution(BaseTimeDistribution):
    ...


class TimePatternPoolDistribution(BaseTimeDistribution):
    ...
