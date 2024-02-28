from datetime import datetime, timedelta
from copy import copy
from typing import Any, Callable, NoReturn

import numpy as np
from eventum.core.models.time_pattern_config import TimePatternConfig
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

    @property
    def _interval_duration(self) -> timedelta:
        """Get duration of one interval."""
        return timedelta(
            **{self._config.oscillator.unit: self._config.oscillator.interval}
        )

    @property
    def _interval_size(self) -> int:
        """Number of time points in interval. Each time the property
        is accessed the value can be different due to randomizer affect.
        """
        return self._config.multiplier.ratio

    def _get_random_delta_cycle(self) -> list[timedelta]:
        """Helper for `_get_delta_cycle` implementing random
        distribution.
        """
        size = self._interval_size
        duration = self._interval_duration

        return list(np.sort(np.random.random(size)) * duration)

    def _get_delta_cycle(self) -> list[timedelta]:
        """Compute list of time points in the distribution for one
        interval where each point is expressed as time from beggining
        of the interval.

        Method calls coresponding method implementing specific
        distribution.
        """
        distr_name = self._config.spreader.function.value.lower()
        attr_name = f'_get_{distr_name}_delta_cycle'

        try:
            return TimePatternInputPlugin.__getattribute__(self, attr_name)()
        except AttributeError as e:
            raise NotImplementedError(
                f'TimePatternInputPlugin does not implement {attr_name} method'
                f' for {distr_name} distribution'
            ) from e

    def _get_interval(self, start: datetime) -> list[datetime]:
        """Compute list of datetimes in the distribution for one
        interval from `start` by using delta cycle.
        """
        return [start + delta for delta in self._get_delta_cycle()]

    def sample(self, on_event: Callable[[datetime], Any]) -> None:
        if (
            not isinstance(self._config.oscillator.start, datetime)
            or not isinstance(self._config.oscillator.end, datetime)
        ):
            raise TimePatternInputPluginError(
                'Only timestamps are allowed to specify for start'
                ' and end time in sample mode'
            )

        start = copy(self._config.oscillator.start)
        end = self._config.oscillator.end
        interval = self._interval_duration

        while start < end:
            for timestamp in self._get_interval(start):
                if timestamp < self._config.oscillator.end:
                    on_event(timestamp)
                else:
                    break

            start += interval

    def live(self, on_event: Callable[[str], Any]) -> NoReturn:
        ...


class TimePatternPoolInputPlugin(LiveInputPlugin, SampleInputPlugin):
    ...
