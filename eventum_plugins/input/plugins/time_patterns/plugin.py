import time
from datetime import datetime, timedelta
from typing import Any, Callable, Iterator, Unpack, assert_never

import numpy as np
from eventum_content_manager.manage import (ContentManagementError,
                                            load_time_pattern)
from numpy.typing import NDArray
from pydantic import ValidationError

from eventum_plugins.exceptions import (PluginConfigurationError,
                                        PluginRuntimeError)
from eventum_plugins.input.base.plugin import InputPlugin, InputPluginKwargs
from eventum_plugins.input.enums import TimeMode
from eventum_plugins.input.fields import TimeKeyword
from eventum_plugins.input.merger import InputPluginsLiveMerger
from eventum_plugins.input.plugins.time_patterns.config import (
    Distribution, RandomizerDirection, TimePatternConfig,
    TimePatternsInputPluginConfig)
from eventum_plugins.input.tools import normalize_versatile_daterange
from eventum_plugins.input.utils.array_utils import (get_past_slice,
                                                     merge_arrays)
from eventum_plugins.input.utils.time_utils import (now64, skip_periods,
                                                    timedelta64_to_seconds,
                                                    to_naive)


class TimePatternInputPlugin(
    InputPlugin,
    config_cls=TimePatternConfig,
    register=False
):
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

    def __init__(self, *, config: TimePatternConfig, **kwargs) -> None:
        super().__init__(config=config, **kwargs)

        self._config: TimePatternConfig
        self._randomizer_factors = self._generate_randomizer_factors(
            count=self._config.randomizer.sampling
        )

        mode = kwargs['mode']
        if (
            mode == TimeMode.SAMPLE
            and self._config.oscillator.end == TimeKeyword.NEVER.value
        ):
            raise PluginConfigurationError(
                f'End time must be finite for "{mode}" mode'
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
        value = int(self._config.oscillator.period)

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
        """Generate distribution of time points in the distribution for one
        period where each point is expressed as time from the beginning
        of the period.

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

    def _generate_sample(
        self,
        on_events: Callable[[NDArray[np.datetime64]], Any]
    ) -> None:
        start, end = normalize_versatile_daterange(
            start=self._config.oscillator.start,
            end=self._config.oscillator.end,
            timezone=self._timezone,
        )

        while start < end:
            timestamps = get_past_slice(
                timestamps=self._generate_period_timeseries(
                    start=np.datetime64(to_naive(start)),
                    size=self._period_size,
                    duration=np.timedelta64(self._period_duration)
                ),
                before=end
            )
            on_events(timestamps)

            start += self._period_duration

    def _generate_live(
        self,
        on_events: Callable[[NDArray[np.datetime64]], Any]
    ) -> None:
        start, end = normalize_versatile_daterange(
            start=self._config.oscillator.start,
            end=self._config.oscillator.end,
            timezone=self._timezone,
        )

        start = skip_periods(
            start=start,
            moment=datetime.now().astimezone(),
            duration=self._period_duration,
            ret_timestamp='last_past'
        )

        timestamps = self._generate_period_timeseries(
            start=np.datetime64(to_naive(start)),
            size=self._period_size,
            duration=np.timedelta64(self._period_duration)
        )

        while start < end:
            timestamps = get_past_slice(
                timestamps=self._generate_period_timeseries(
                    start=np.datetime64(to_naive(start)),
                    size=self._period_size,
                    duration=np.timedelta64(self._period_duration)
                ),
                before=end
            )

            # if period is last by condition but sliced array is empty
            if timestamps.size == 0:
                break

            now = now64(self._timezone)
            wait_seconds = timedelta64_to_seconds(timestamps[0] - now)

            if wait_seconds > 0:
                time.sleep(wait_seconds)

            on_events(timestamps)

            start += self._period_duration


class TimePatternsInputPlugin(
    InputPlugin,
    config_cls=TimePatternsInputPluginConfig
):
    """Input plugin for merging timestamps from multiple
    `TimePatternInputPlugin` instances.
    """

    def __init__(
        self,
        *,
        config: TimePatternsInputPluginConfig,
        **kwargs: Unpack[InputPluginKwargs]
    ) -> None:
        super().__init__(config=config, **kwargs)

        self._config: TimePatternsInputPluginConfig
        self._time_patterns = self._init_time_patterns(**kwargs)

    def _init_time_patterns(
        self,
        **kwargs: Unpack[InputPluginKwargs]
    ) -> list[TimePatternInputPlugin]:
        time_patterns: list[TimePatternInputPlugin] = []
        for config_path in self._config.configs:
            try:
                time_pattern_obj = load_time_pattern(path=config_path)
                time_pattern = TimePatternConfig.model_validate(
                    obj=time_pattern_obj
                )
            except ContentManagementError as e:
                raise PluginConfigurationError(
                    f'Failed to load time pattern "{config_path}": {e}'
                )
            except ValidationError as e:
                raise PluginConfigurationError(
                    f'Bad config structure for "{config_path}": {e}'
                )

            time_patterns.append(
                TimePatternInputPlugin(
                    config=time_pattern,
                    **kwargs
                )
            )

        return time_patterns

    @property
    def count(self) -> int:
        """Count of time patterns."""
        return len(self._time_patterns)

    def _generate_sample(
        self,
        on_events: Callable[[NDArray[np.datetime64]], Any]
    ) -> None:
        samples: list[NDArray[np.datetime64]] = []
        for plugin in self._time_patterns:
            samples.append(
                np.concatenate(list(plugin.generate()))
            )

        on_events(merge_arrays(samples))

    def _generate_live(
        self,
        on_events: Callable[[NDArray[np.datetime64]], Any]
    ) -> None:
        try:
            plugins = InputPluginsLiveMerger(
                plugins=self._time_patterns,
                target_delay=self._batcher.batch_delay,
                batch_size=None
            )
        except ValidationError as e:
            raise PluginRuntimeError(
                f'Cannot initialize merger for time patterns: {e}'
            )

        for batch in plugins.generate():
            on_events(batch)
