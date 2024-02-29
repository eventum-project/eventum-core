from datetime import datetime, timedelta
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
        # TODO randomizer affect
        return self._config.multiplier.ratio

    def _get_random_delta_cycle(self) -> list[timedelta]:
        """Helper for `_get_delta_cycle` implementing random
        distribution.
        """
        size = self._interval_size
        duration = self._interval_duration

        return list(np.sort(np.random.random(size)) * duration)

    def _get_beta_delta_cycle(self) -> list[timedelta]:
        """Helper for `_get_delta_cycle` implementing beta
        distribution.
        """
        size = self._interval_size
        duration = self._interval_duration
        a = self._config.spreader.parameters.a
        b = self._config.spreader.parameters.b

        return list(np.sort(np.random.beta(a, b, size)) * duration)

    def _get_triangular_delta_cycle(self) -> list[timedelta]:
        """Helper for `_get_delta_cycle` implementing triangular
        distribution.
        """
        size = self._interval_size
        duration = self._interval_duration

        left = self._config.spreader.parameters.left
        mode = self._config.spreader.parameters.mode
        right = self._config.spreader.parameters.right

        return list(
            np.sort(np.random.triangular(left, mode, right, size)) * duration
        )

    def _get_delta_cycle(self) -> list[timedelta]:
        """Compute list of time points in the distribution for one
        interval where each point is expressed as time from beginning
        of the interval.

        Method calls corresponding method implementing specific
        distribution.
        """
        distr_name = self._config.spreader.distribution.value.lower()
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

        start = self._config.oscillator.start
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


# import eventum.core.models.time_pattern_config as models
# from matplotlib import pyplot as plt

# lst = []
# TimePatternInputPlugin(
#     config=models.TimePatternConfig(
#             label='test',
#             oscillator=models.OscillatorConfig(
#                 interval=8,
#                 unit=models.TimeUnit.HOURS,
#                 start='2024-02-28T00:00:00+03:00',
#                 end='2024-02-29T00:00:00+03:00'
#             ),
#             multiplier=models.MultiplierConfig(ratio=10000),
#             randomizer=models.RandomizerConfig(
#                 deviation=0,
#                 direction=models.RandomizerDirection.MIXED
#             ),
#             spreader=models.SpreaderConfig(
#                 distribution=models.Distribution.TRIANGULAR,
#                 parameters=models.TriangularDistributionParameters(
#                     left=0.6,
#                     mode=0.7,
#                     right=1
#                 )
#             )
#         )
# ).sample(lambda ts: lst.append(ts))

# plt.hist(lst, bins=100)
# plt.show()
