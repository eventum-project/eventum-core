import sys
from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError
from datetime import datetime, time, timedelta
from enum import StrEnum
from heapq import merge
from queue import Empty, Queue
from time import perf_counter, sleep
from typing import Annotated, Any, Callable, TypeAlias, assert_never

import numpy as np
from eventum_content_manager.manage import (ContentManagementError,
                                            load_time_pattern)
from numpy.typing import NDArray
from pydantic import AfterValidator, Field, ValidationError, model_validator
from pytz.tzinfo import BaseTzInfo

from eventum_plugins.input.base import (InputPluginBaseConfig,
                                        InputPluginConfigurationError,
                                        InputPluginRuntimeError,
                                        LiveInputPlugin, PerformanceError,
                                        SampleInputPlugin)
from eventum_plugins.utils.numpy_time import get_now, timedelta_to_seconds
from eventum_plugins.utils.relative_time import parse_relative_time
from eventum_plugins.utils.timeseries import get_future_slice, get_past_slice


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


def _check_relative_time(obj: Any) -> str:
    if isinstance(obj, str):
        parse_relative_time(obj)

    return obj


RelativeTime = Annotated[str, AfterValidator(_check_relative_time)]


class OscillatorConfig(InputPluginBaseConfig, frozen=True):
    period: int = Field(..., ge=1)
    unit: TimeUnit
    start: time | datetime | TimeKeyword | RelativeTime
    end: time | datetime | TimeKeyword | RelativeTime


class MultiplierConfig(InputPluginBaseConfig, frozen=True):
    ratio: int = Field(..., ge=1)


class RandomizerConfig(InputPluginBaseConfig, frozen=True):
    deviation: float = Field(..., ge=0, le=1)
    direction: RandomizerDirection


class BetaDistributionParameters(InputPluginBaseConfig, frozen=True):
    a: float = Field(..., ge=0)
    b: float = Field(..., ge=0)


class TriangularDistributionParameters(InputPluginBaseConfig, frozen=True):
    left: float = Field(..., ge=0, lt=1)
    mode: float = Field(..., ge=0, le=1)
    right: float = Field(..., gt=0, le=1)

    @model_validator(mode='after')
    def validate_points(self):
        if (
            self.left <= self.mode <= self.right
            and not (self.left == self.mode == self.right)
        ):
            return self
        raise ValueError(
            'Values do not comply "left <= mode <= right" condition'
        )


class UniformDistributionParameters(InputPluginBaseConfig, frozen=True):
    low: float = Field(..., ge=0, lt=1)
    high: float = Field(..., gt=0, le=1)

    @model_validator(mode='after')
    def validate_points(self):
        if self.low < self.high:
            return self
        raise ValueError(
            'Values do not comply "low < high" condition'
        )


DistributionParameters: TypeAlias = (
    UniformDistributionParameters |
    TriangularDistributionParameters |
    BetaDistributionParameters
)


class SpreaderConfig(InputPluginBaseConfig, frozen=True):
    _DISTRIBUTION_PARAMETERS_MAP = {
        Distribution.UNIFORM: UniformDistributionParameters,
        Distribution.TRIANGULAR: TriangularDistributionParameters,
        Distribution.BETA: BetaDistributionParameters
    }

    distribution: Distribution
    parameters: DistributionParameters

    @model_validator(mode='after')
    def validate_parameters_model(self):
        if self.distribution not in self._DISTRIBUTION_PARAMETERS_MAP:
            raise NotImplementedError

        expected_model = self._DISTRIBUTION_PARAMETERS_MAP[self.distribution]

        if isinstance(self.parameters, expected_model):
            return self

        raise ValueError(
            f'Improper parameters model for "{self.distribution}" distribution'
        )


class TimePatternConfig(InputPluginBaseConfig, frozen=True):
    label: str = Field(..., min_length=1)
    oscillator: OscillatorConfig
    multiplier: MultiplierConfig
    randomizer: RandomizerConfig
    spreader: SpreaderConfig


class TimePatternsInputConfig(InputPluginBaseConfig, frozen=True):
    configs: tuple[str, ...] = Field(..., min_length=1)


class TimePatternInputPlugin(LiveInputPlugin, SampleInputPlugin):
    """Input plugin for generating events with specific pattern of
    distribution in time.
    """

    class EndTimeReaching(Exception):
        """Internal `TimePatternInputPlugin` exception to designate that
        end of live interval is reached.
        """

    _PERFORMANCE_TEST_SAMPLE_SIZE = 100000
    _REQUIRED_EPS_RESERVE_RATIO = 1.15
    PUBLISH_PRECISION_SECONDS = 0.01

    def __init__(self, config: TimePatternConfig, tz: BaseTzInfo) -> None:
        self._config = config
        self._tz = tz
        self._randomizer_factors = self._generate_randomizer_factors()

    def _generate_randomizer_factors(
        self,
        size: int = 1000
    ) -> NDArray[np.float64]:
        """Get sample of factors for multiply them on size for
        randomizer effect.
        """
        match self._config.randomizer.direction:
            case RandomizerDirection.DECREASE:
                return np.random.uniform(
                    low=(1 - self._config.randomizer.deviation),
                    high=1,
                    size=size
                )
            case RandomizerDirection.INCREASE:
                return np.random.uniform(
                    low=1,
                    high=(1 + self._config.randomizer.deviation),
                    size=size
                )
            case RandomizerDirection.MIXED:
                return np.random.uniform(
                    low=(1 - self._config.randomizer.deviation),
                    high=(1 + self._config.randomizer.deviation),
                    size=size
                )
            case direction:
                assert_never(direction)

    @property
    def _period_duration(self) -> np.timedelta64:
        """Get duration of one period."""
        unit = self._config.oscillator.unit.value
        value = int(self._config.oscillator.period)

        return np.timedelta64(timedelta(**{unit: value}))

    @property
    def _period_size(self) -> int:
        """Number of time points in period. Each time the property
        is accessed the value can be different due to randomizer effect.
        """
        return int(
            self._config.multiplier.ratio
            * np.random.choice(self._randomizer_factors)
        )

    def _get_distribution(
        self,
        size: int,
        duration: np.timedelta64
    ) -> NDArray[np.timedelta64]:
        """Compute list of time points in the distribution for one
        period where each point is expressed as time from the beginning
        of the period.
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

    def _get_period_timeseries(
        self,
        start: np.datetime64,
        size: int,
        duration: np.timedelta64
    ) -> NDArray[np.datetime64]:
        """Compute list of datetimes in the distribution for one
        period from `start` with specified `duration` and `size`.
        """
        return self._get_distribution(size, duration) + start

    def _get_normalized_interval_bounds(
        self,
        allow_never_end: bool = True
    ) -> tuple[np.datetime64, np.datetime64]:
        """Get absolute timestamps converting `start` and `end` values
        from config.
        """
        now = datetime.now(self._tz)
        never = datetime(year=9999, month=12, day=31)

        match self._config.oscillator.start:
            case datetime() as val:
                if val.tzinfo:
                    start = val.astimezone(self._tz)
                else:
                    start = val
            case time() as val:
                start = datetime.combine(now.today(), val)
            case TimeKeyword.NOW:
                start = now
            case TimeKeyword.NEVER as val:
                raise InputPluginRuntimeError(
                    f'Value of "start" cannot be "{val}"'
                )
            case str() as val:
                start = now + parse_relative_time(val)
            case val:
                assert_never(val)

        match self._config.oscillator.end:
            case datetime() as val:
                if val.tzinfo:
                    end = val.astimezone(self._tz)
                else:
                    end = val
            case time() as val:
                end = datetime.combine(now.today(), val)
            case TimeKeyword.NOW:
                end = now
            case TimeKeyword.NEVER:
                end = never
            case str() as val:
                end = start + parse_relative_time(val)
            case val:
                assert_never(val)

        if end is never and not allow_never_end:
            raise InputPluginRuntimeError(
                f'Value "{TimeKeyword.NEVER}" for "end" parameter '
                'is not allowed here'
            )

        start = start.replace(tzinfo=None)
        end = end.replace(tzinfo=None)

        if start >= end:
            raise InputPluginRuntimeError(
                '"start" time must be earlier than "end" time'
            )

        return (np.datetime64(start), np.datetime64(end))

    def _get_required_eps(self) -> float:
        """Get required eps for performance check."""

        match self._config.randomizer.direction:
            case RandomizerDirection.INCREASE:
                max_count = (
                    self._config.multiplier.ratio
                    * self._config.randomizer.deviation
                )
            case _:
                max_count = self._config.multiplier.ratio

        seconds = timedelta_to_seconds(self._period_duration)
        return float(max_count / seconds * self._REQUIRED_EPS_RESERVE_RATIO)

    def _test_actual_eps(self) -> float:
        """Compute actual eps for performance check."""

        start = perf_counter()
        self._get_period_timeseries(
            start=get_now(tz=self._tz),
            size=self._PERFORMANCE_TEST_SAMPLE_SIZE,
            duration=self._period_duration
        )
        seconds = perf_counter() - start

        return self._PERFORMANCE_TEST_SAMPLE_SIZE / seconds

    def _check_performance(self) -> None:
        """Check if actual performance is enough to run plugin in live
        mode. If it's not `PerformanceError` is raised.
        """
        actual_eps = self._test_actual_eps()
        required_eps = self._get_required_eps()

        if actual_eps < required_eps:
            raise PerformanceError(
                'Not enough performance to produce distributions in time: '
                f'actual EPS is {round(actual_eps)} but {round(required_eps)} '
                'is required'
            )

    def sample(self, on_event: Callable[[np.datetime64], Any]) -> None:
        start, end = self._get_normalized_interval_bounds(
            allow_never_end=False
        )

        while start < end:
            for timestamp in get_past_slice(
                timestamps=self._get_period_timeseries(
                    start=start,
                    size=self._period_size,
                    duration=self._period_duration
                ),
                before=end
            ):
                on_event(timestamp)

            start += self._period_duration

    def live(self, on_event: Callable[[np.datetime64], Any]) -> None:
        self._check_performance()

        start, end = self._get_normalized_interval_bounds()

        now = get_now(tz=self._tz)
        if now >= end:
            return

        if now > start:
            skip_periods = (now - start) // self._period_duration
            start += self._period_duration * skip_periods

        timestamps = self._get_period_timeseries(
            start=start,
            size=self._period_size,
            duration=self._period_duration
        )

        now = get_now(tz=self._tz)
        if start < now:
            timestamps = get_future_slice(timestamps=timestamps, after=now)

        # thread worker definitions

        def publish_period_thread(
            timestamps: NDArray[np.datetime64]
        ) -> None:
            now = get_now(tz=self._tz)

            for timestamp in timestamps:
                if timestamp >= end:
                    raise self.EndTimeReaching

                wait_seconds = timedelta_to_seconds(timestamp - now)

                if wait_seconds > self.PUBLISH_PRECISION_SECONDS:
                    sleep(wait_seconds)     # type: ignore
                    now = get_now(tz=self._tz)

                on_event(timestamp)

        def prepare_period_thread(
            start: np.datetime64
        ) -> NDArray[np.datetime64]:
            return self._get_period_timeseries(
                start=start,
                size=self._period_size,
                duration=self._period_duration
            )

        with ThreadPoolExecutor(max_workers=2) as executor:
            while start < end:
                next_start = start + self._period_duration

                prepare_task = executor.submit(
                    prepare_period_thread, next_start
                )
                publish_task = executor.submit(
                    publish_period_thread, timestamps
                )

                try:
                    publish_task.result()
                except self.EndTimeReaching:
                    try:
                        prepare_task.result(timeout=0)
                    except TimeoutError:
                        pass
                    finally:
                        return

                timestamps = prepare_task.result()

                start += self._period_duration


class TimePatternPoolInputPlugin(LiveInputPlugin, SampleInputPlugin):
    """Input plugin for combining multiple `TimePatternInputPlugin`
    plugins.
    """

    def __init__(
        self,
        config: TimePatternsInputConfig,
        tz: BaseTzInfo
    ) -> None:
        self._tz = tz
        time_patterns: list[TimePatternInputPlugin] = []

        for config_path in config.configs:
            try:
                time_pattern_obj = load_time_pattern(path=config_path)
                time_pattern = TimePatternConfig.model_validate(
                    obj=time_pattern_obj
                )
            except ContentManagementError as e:
                raise InputPluginConfigurationError(
                    f'Failed to load time pattern "{config_path}": {e}'
                )
            except ValidationError as e:
                raise InputPluginConfigurationError(
                    f'Bad config structure for "{config_path}": {e}'
                )

            time_patterns.append(
                TimePatternInputPlugin(
                    config=time_pattern,
                    tz=self._tz
                )
            )

        self._time_patterns: tuple[TimePatternInputPlugin, ...] = tuple(
            time_patterns
        )
        self._size = len(self._time_patterns)

    def sample(self, on_event: Callable[[np.datetime64], Any]) -> None:
        samples = []

        for pattern in self._time_patterns:
            sample = []
            pattern.sample(on_event=lambda ts: sample.append(ts))
            samples.append(sample)

        for ts in merge(*samples):
            on_event(ts)

    def live(self, on_event: Callable[[np.datetime64], Any]) -> None:
        queues: list[Queue[np.datetime64]] = []
        tasks: list[Future] = []

        with ThreadPoolExecutor(max_workers=self._size) as executor:
            for pattern in self._time_patterns:
                queue: Queue[np.datetime64] = Queue()
                tasks.append(
                    executor.submit(pattern.live, queue.put)
                )
                queues.append(queue)

            while tasks:
                latest_timestamp = get_now(tz=self._tz)

                # wait until each time pattern published its past events
                sleep(
                    TimePatternInputPlugin.PUBLISH_PRECISION_SECONDS
                    + sys.getswitchinterval() * self._size
                )

                batches = []
                for queue in queues:
                    batch = []

                    while True:
                        try:
                            timestamp = queue.get_nowait()
                            batch.append(timestamp)
                            if timestamp >= latest_timestamp:
                                break
                        except Empty:
                            break

                    batches.append(batch)

                for timestamp in merge(*batches):
                    on_event(timestamp)

                for i, (task, queue) in enumerate(zip(tasks, queues)):
                    if task.done() and queue.empty():
                        # get result to propagate exceptions
                        tasks[i].result()

                        tasks[i] = None     # type: ignore[call-overload]
                        queues[i] = None    # type: ignore[call-overload]

                tasks = [task for task in tasks if task is not None]
                queues = [queue for queue in queues if queue is not None]


PLUGIN_CLASS = TimePatternPoolInputPlugin
CONFIG_CLASS = TimePatternsInputConfig
