from datetime import datetime, timedelta, time, date
from typing import Any, Callable, NoReturn

import numpy as np
from eventum.core.models.time_pattern_config import (TimePatternConfig,
                                                     RandomizerDirection,
                                                     TimeKeyword)
from eventum.core.plugins.input.base import (LiveInputPlugin,
                                             SampleInputPlugin,
                                             InputPluginError)


class TimePatternInputPluginError(InputPluginError):
    """Exception for TimePatternInputPlugin errors."""


class TimePatternInputPlugin(LiveInputPlugin, SampleInputPlugin):
    """Input plugin for generating events with consistent pattern
    of distribution in time.
    """

    def __init__(self, config: TimePatternConfig) -> None:
        self._config = config
        self._randomizer_factors = self._get_randomizer_factors()

    def _get_randomizer_factors(self, size: int = 1000) -> np.ndarray:
        """Get sample of factors for multiply them on size for
        randomizer effect.
        """
        match self._config.randomizer.direction:
            case RandomizerDirection.DECREASE:
                return np.random.uniform(
                    low=(1 - self._config.randomizer.deviation / 100),
                    high=1,
                    size=size
                )
            case RandomizerDirection.INCREASE:
                return np.random.uniform(
                    low=1,
                    high=(1 + self._config.randomizer.deviation / 100),
                    size=size
                )
            case RandomizerDirection.MIXED:
                return np.random.uniform(
                    low=(1 - self._config.randomizer.deviation / 100),
                    high=(1 + self._config.randomizer.deviation / 100),
                    size=size
                )

    @property
    def _period_duration(self) -> timedelta:
        """Get duration of one period."""
        return timedelta(
            **{self._config.oscillator.unit: self._config.oscillator.period}
        )

    @property
    def _period_size(self) -> int:
        """Number of time points in period. Each time the property
        is accessed the value can be different due to randomizer effect.
        """
        return int(
            self._config.multiplier.ratio
            * np.random.choice(self._randomizer_factors)
        )

    def _get_uniform_distribution(self) -> list[timedelta]:
        """Helper for `_get_distribution` implementing uniform
        distribution.
        """
        size = self._period_size
        duration = self._period_duration
        low = self._config.spreader.parameters.low
        high = self._config.spreader.parameters.high

        return list(np.sort(np.random.uniform(low, high, size)) * duration)

    def _get_beta_distribution(self) -> list[timedelta]:
        """Helper for `_get_distribution` implementing beta
        distribution.
        """
        size = self._period_size
        duration = self._period_duration
        a = self._config.spreader.parameters.a
        b = self._config.spreader.parameters.b

        return list(np.sort(np.random.beta(a, b, size)) * duration)

    def _get_triangular_distribution(self) -> list[timedelta]:
        """Helper for `_get_distribution` implementing triangular
        distribution.
        """
        size = self._period_size
        duration = self._period_duration

        left = self._config.spreader.parameters.left
        mode = self._config.spreader.parameters.mode
        right = self._config.spreader.parameters.right

        return list(
            np.sort(np.random.triangular(left, mode, right, size)) * duration
        )

    def _get_distribution(self) -> list[timedelta]:
        """Compute list of time points in the distribution for one
        period where each point is expressed as time from the beginning
        of the period.

        Method calls corresponding method implementing specific
        distribution.
        """
        distr_name = self._config.spreader.distribution.value.lower()
        attr_name = f'_get_{distr_name}_distribution'

        try:
            return getattr(self, attr_name)()
        except AttributeError as e:
            raise NotImplementedError(
                f'TimePatternInputPlugin does not implement {attr_name} method'
                f' for {distr_name} distribution'
            ) from e

    def _get_period_timeseries(self, start: datetime) -> list[datetime]:
        """Compute list of datetimes in the distribution for one
        period from `start` by using `_get_distribution` - the
        distribution of timedeltas.
        """
        return [start + delta for delta in self._get_distribution()]

    def _get_normalized_interval_bounds(self) -> tuple[datetime, datetime]:
        """Get absolute timestamps converting relative time (timedelta),
        keywords or only time component.
        """

        match self._config.oscillator.start:
            case datetime(val):
                start = val
            case timedelta(val):
                start = datetime.now() + val
            case time(val):
                start = datetime.combine(date.today(), val)
            case TimeKeyword.NOW:
                start = datetime.now()
            case TimeKeyword.NEVER:
                raise TimePatternInputPluginError(
                    'Value of "start" cannot be '
                    f'"{self._config.oscillator.start}"'
                )

        match self._config.oscillator.end:
            case datetime(val):
                end = val
            case timedelta(val):
                end = datetime.now() + val
            case time(val):
                end = datetime.combine(date.today(), val)
            case TimeKeyword.NOW:
                end = datetime.now()
            case TimeKeyword.NEVER:
                end = datetime(year=9999, month=12, day=31)

        if start >= end:
            raise TimePatternInputPluginError(
                '"start" time must be earlier than "end" time'
            )

        return (start, end)

    def sample(self, on_event: Callable[[datetime], Any]) -> None:
        if (
            not isinstance(self._config.oscillator.start, datetime)
            or not isinstance(self._config.oscillator.end, datetime)
        ):
            raise TimePatternInputPluginError(
                'Only timestamps are allowed to specify for start'
                ' and end time in sample mode'
            )

        start, end = self._get_normalized_interval_bounds()

        while start < end:
            for timestamp in self._get_period_timeseries(start):
                if timestamp < self._config.oscillator.end:
                    on_event(timestamp)
                else:
                    break

            start += self._period_duration

    def live(self, on_event: Callable[[str], Any]) -> NoReturn:
        ...


class TimePatternPoolInputPlugin(LiveInputPlugin, SampleInputPlugin):
    ...
