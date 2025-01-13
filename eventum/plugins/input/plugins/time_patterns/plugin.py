from datetime import datetime, timedelta
from typing import Iterator, assert_never

import numpy as np
import yaml
from numpy.typing import NDArray
from pydantic import ValidationError

from eventum.plugins.exceptions import PluginConfigurationError
from eventum.plugins.input.base.plugin import InputPlugin, InputPluginParams
from eventum.plugins.input.merger import InputPluginsMerger
from eventum.plugins.input.normalizers import normalize_versatile_daterange
from eventum.plugins.input.plugins.time_patterns.config import (
    Distribution, RandomizerDirection, TimePatternConfig,
    TimePatternsInputPluginConfig)
from eventum.plugins.input.utils.array_utils import (get_future_slice,
                                                     get_past_slice)
from eventum.plugins.input.utils.time_utils import (now64, skip_periods,
                                                    to_naive)


class TimePatternInputPlugin(InputPlugin[TimePatternConfig], register=False):
    """Input plugin for generating events with specific pattern of
    distribution in time.

    Notes
    -----
    Time pattern is determined by four components:
    ```txt
    1. Oscillator - defines the base frequency of event generation
    ^
    |
    |.     .     .     .     .
    o-----------------------------> t
    * One point is one signal

    2. Multiplier - multiplies the number of events by the specified value
    ^
    |:     :     :     :     :
    |:     :     :     :     :
    |:     :     :     :     :
    |:     :     :     :     :
    o-----------------------------> t
    Example multiplication with factor x8


    3. Randomizer - increases or decreases the number of events
    ^
    |.     :                 .
    |:     :     .     :     :
    |:     :     :     :     :
    |:     :     :     :     :
    o-----------------------------> t
    Randomizer variate number of signals for each period


    4. Spreader - distribute events within one time period
    ^
    |         .
    | ..::. ..::. ..:. .::. ..::.
    o-----------------------------> t
    Signals are distributed within one period using probability function
    ```
    """

    def __init__(
        self,
        config: TimePatternConfig,
        params: InputPluginParams
    ) -> None:
        super().__init__(config, params)

        self._randomizer_factors = self._generate_randomizer_factors(
            count=self._config.randomizer.sampling
        )

    def _generate_randomizer_factors(self, count: int) -> Iterator[float]:
        """Generate sample of factors for randomizer.

        Parameters
        ----------
        size : int
            Number of unique factors

        Yields
        ------
        float
            Randomizer factor

        Notes
        -----
        Factors are shuffled each time the sample is exhausted
        """
        match self._config.randomizer.direction:
            case RandomizerDirection.DECREASE:
                factors = np.random.uniform(
                    low=(1 - self._config.randomizer.deviation),
                    high=1,
                    size=count
                )
            case RandomizerDirection.INCREASE:
                factors = np.random.uniform(
                    low=1,
                    high=(1 + self._config.randomizer.deviation),
                    size=count
                )
            case RandomizerDirection.MIXED:
                factors = np.random.uniform(
                    low=(1 - self._config.randomizer.deviation),
                    high=(1 + self._config.randomizer.deviation),
                    size=count
                )
            case direction:
                assert_never(direction)

        while True:
            for factor in factors:
                yield float(factor)

            np.random.shuffle(factors)

    @property
    def _period_duration(self) -> timedelta:
        """Duration of one period."""
        unit = self._config.oscillator.unit.value
        value = self._config.oscillator.period

        return timedelta(**{unit: value})

    @property
    def _period_size(self) -> int:
        """Number of time points in period.

        Notes
        -----
        Each time the property is accessed the value can be different
        due to randomizer factor.
        """
        return int(
            self._config.multiplier.ratio
            * next(self._randomizer_factors)
        )

    def _generate_distribution(
        self,
        size: int,
        duration: np.timedelta64
    ) -> NDArray[np.timedelta64]:
        """Generate distribution of time points for one period where
        each point is expressed as time from the beginning of the
        period.

        Parameters
        ----------
        size : int
            Size of distribution

        duration : numpy.timedelta64
            Duration of period

        Returns
        -------
        NDArray[numpy.timedelta64]
            Generated distribution
        """
        params = self._config.spreader.parameters
        match self._config.spreader.distribution:
            case Distribution.UNIFORM:
                low = params.low        # type: ignore[union-attr]
                high = params.high      # type: ignore[union-attr]
                array = np.sort(np.random.uniform(low, high, size))
            case Distribution.TRIANGULAR:
                left = params.left      # type: ignore[union-attr]
                mode = params.mode      # type: ignore[union-attr]
                right = params.right    # type: ignore[union-attr]
                array = np.sort(np.random.triangular(left, mode, right, size))
            case Distribution.BETA:
                a = params.a            # type: ignore[union-attr]
                b = params.b            # type: ignore[union-attr]
                array = np.sort(np.random.beta(a, b, size))
            case val:
                assert_never(val)

        return array * duration

    def _generate_period_timeseries(
        self,
        start: np.datetime64,
        size: int,
        duration: np.timedelta64
    ) -> NDArray[np.datetime64]:
        """Generate array of timestamps distributed within one
        period.

        Parameters
        ----------
        start : numpy.datetime64
            Start timestamp of period

        size : int
            Number of timestamps in period

        duration : numpy.timedelta64
            Duration of period

        Returns
        -------
        NDArray[numpy.datetime64]
            Generated array of timestamps
        """
        return self._generate_distribution(size, duration) + start

    def generate(
        self,
        size: int,
        skip_past: bool = True
    ) -> Iterator[NDArray[np.datetime64]]:
        start_dt, end_dt = normalize_versatile_daterange(
            start=self._config.oscillator.start,
            end=self._config.oscillator.end,
            timezone=self._timezone,
            none_start='now',
            none_end='max'
        )
        self._logger.info(
            'Generating in range',
            start_timestamp=start_dt.isoformat(),
            end_timestamp=end_dt.isoformat()
        )

        if skip_past:
            start_dt = skip_periods(
                start=start_dt,
                moment=datetime.now().astimezone(),
                duration=self._period_duration,
                ret_timestamp='last_past'
            )

        if start_dt >= end_dt:
            self._logger.info(
                'All timestamps are in past, nothing to generate'
            )
            return

        delta = np.timedelta64(self._period_duration)
        start = np.datetime64(to_naive(start_dt, self._timezone))
        end = np.datetime64(to_naive(end_dt, self._timezone))

        timestamps = self._generate_period_timeseries(
            start=start,
            size=self._period_size,
            duration=delta
        )
        if skip_past:
            # in case we are at period duration but all timestamps
            # are spaced in start of the period
            timestamps = get_future_slice(
                timestamps=timestamps,
                after=now64(self._timezone)
            )
            if timestamps.size == 0:
                self._logger.info(
                    'All timestamps are in past, nothing to generate'
                )

        timestamps = get_past_slice(
            timestamps=timestamps,
            before=end
        )

        while True:
            if timestamps.size != 0:
                self._buffer.mv_push(timestamps)

                if self._buffer.size >= size:
                    yield from self._buffer.read(size, partial=False)

            start += delta

            if start >= end:
                break

            timestamps = get_past_slice(
                timestamps=self._generate_period_timeseries(
                    start=start,
                    size=self._period_size,
                    duration=delta
                ),
                before=end
            )

        yield from self._buffer.read(size, partial=True)


class TimePatternsInputPlugin(InputPlugin[TimePatternsInputPluginConfig]):
    """Input plugin for merging timestamps from multiple
    `TimePatternInputPlugin` instances.
    """

    def __init__(
        self,
        config: TimePatternsInputPluginConfig,
        params: InputPluginParams
    ) -> None:
        super().__init__(config, params)

        self._logger.info('Loading time patterns')
        self._time_patterns = self._init_time_patterns(params)

    def _init_time_patterns(
        self,
        params: InputPluginParams
    ) -> list[TimePatternInputPlugin]:
        """Initialize time pattern specified in config.

        Parameters
        ----------
        params : InputPluginParams
            Input plugin parameters
        """
        time_patterns: list[TimePatternInputPlugin] = []
        for pattern_path in self._config.patterns:
            self._logger.info(
                'Initializing time pattern for configuration',
                file_path=pattern_path
            )
            try:
                with open(pattern_path) as f:
                    time_pattern_obj = yaml.load(f, yaml.SafeLoader)

                time_pattern = TimePatternConfig.model_validate(
                    obj=time_pattern_obj
                )
            except OSError as e:
                raise PluginConfigurationError(
                    'Failed to load time pattern configuration',
                    context=dict(
                        self.instance_info,
                        file_path=pattern_path,
                        reason=str(e)
                    )
                ) from None
            except yaml.error.YAMLError as e:
                raise PluginConfigurationError(
                    'Failed to parse time pattern configuration',
                    context=dict(
                        self.instance_info,
                        file_path=pattern_path,
                        reason=str(e)
                    )
                ) from None
            except ValidationError as e:
                raise PluginConfigurationError(
                    'Bad time pattern configuration structure',
                    context=dict(
                        self.instance_info,
                        file_path=pattern_path,
                        reason=str(e)
                    )
                ) from None

            try:
                time_pattern_plugin = TimePatternInputPlugin(
                    config=time_pattern,
                    params=params | {     # type: ignore
                        'ephemeral_name': (
                            f'{self.plugin_name} ({pattern_path})'
                        ),
                        'ephemeral_type': self.plugin_type
                    }
                )
            except PluginConfigurationError as e:
                raise PluginConfigurationError(
                    'Failed to initialize time pattern for configuration',
                    context=dict(
                        self.instance_info,
                        file_path=pattern_path,
                        reason=str(e)
                    )
                )

            time_patterns.append(time_pattern_plugin)

        return time_patterns

    def generate(
        self,
        size: int,
        skip_past: bool = True
    ) -> Iterator[NDArray[np.datetime64]]:
        merger = InputPluginsMerger(plugins=self._time_patterns)

        self._logger.info('Generating in time patterns range')

        yield from merger.iterate(size, skip_past, include_id=False)

    @property
    def count(self) -> int:
        """Count of time patterns."""
        return len(self._time_patterns)
