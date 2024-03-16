import sys
from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError
from datetime import date, datetime, time, timedelta
from heapq import merge
from queue import Empty, Queue
from time import perf_counter, sleep
from typing import Any, Callable, Sequence, assert_never

import numpy as np

from eventum.core import settings
from eventum.core.models.time_pattern_config import (RandomizerDirection,
                                                     TimeKeyword,
                                                     TimePatternConfig)
from eventum.core.plugins.input.base import (InputPluginConfigurationError,
                                             InputPluginRuntimeError,
                                             LiveInputPlugin,
                                             SampleInputPlugin)
from eventum.utils.timeseries import get_future_slice


class EndTimeReaching(Exception):
    """Internal `TimePatternInputPlugin` exception to designate that
    end of live interval is reached.
    """


class TimePatternInputPlugin(LiveInputPlugin, SampleInputPlugin):
    """Input plugin for generating events with consistent pattern of
    distribution in time.
    """

    _PERFORMANCE_TEST_SAMPLE_SIZE = 100000

    def __init__(self, config: TimePatternConfig) -> None:
        self._config = config
        self._randomizer_factors = self._get_randomizer_factors()
        self._performance_testing = False

    def _get_randomizer_factors(self, size: int = 1000) -> np.ndarray:
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
    def _period_duration(self) -> timedelta:
        """Get duration of one period."""
        key = self._config.oscillator.unit.value
        value = self._config.oscillator.period

        return timedelta(**{key: value})

    @property
    def _period_size(self) -> int:
        """Number of time points in period. Each time the property
        is accessed the value can be different due to randomizer effect.
        """
        if self._performance_testing:
            return self._PERFORMANCE_TEST_SAMPLE_SIZE
        else:
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
        low = self._config.spreader.parameters.low      # type: ignore
        high = self._config.spreader.parameters.high    # type: ignore

        return list(
            np.sort(np.random.uniform(low, high, size))
            * duration  # type: ignore
        )

    def _get_beta_distribution(self) -> list[timedelta]:
        """Helper for `_get_distribution` implementing beta
        distribution.
        """
        size = self._period_size
        duration = self._period_duration
        a = self._config.spreader.parameters.a          # type: ignore
        b = self._config.spreader.parameters.b          # type: ignore

        return list(
            np.sort(np.random.beta(a, b, size))
            * duration  # type: ignore
        )

    def _get_triangular_distribution(self) -> list[timedelta]:
        """Helper for `_get_distribution` implementing triangular
        distribution.
        """
        size = self._period_size
        duration = self._period_duration

        left = self._config.spreader.parameters.left    # type: ignore
        mode = self._config.spreader.parameters.mode    # type: ignore
        right = self._config.spreader.parameters.right  # type: ignore

        return list(
            np.sort(np.random.triangular(left, mode, right, size))
            * duration  # type: ignore
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
        now = datetime.now()

        match self._config.oscillator.start:
            case datetime() as val:
                start = val
            case timedelta() as val:
                start = now + val
            case time() as val:
                start = datetime.combine(date.today(), val)
            case TimeKeyword.NOW:
                start = now
            case TimeKeyword.NEVER as val:
                raise InputPluginRuntimeError(
                    f'Value of "start" cannot be "{val}"'
                )
            case val:
                assert_never(val)

        match self._config.oscillator.end:
            case datetime() as val:
                end = val
            case timedelta() as val:
                end = now + val
            case time() as val:
                end = datetime.combine(date.today(), val)
            case TimeKeyword.NOW:
                end = now
            case TimeKeyword.NEVER:
                end = datetime(year=9999, month=12, day=31)
            case val:
                assert_never(val)

        start = start.astimezone()
        end = end.astimezone()

        if start >= end:
            raise InputPluginRuntimeError(
                '"start" time must be earlier than "end" time'
            )

        return (start, end)

    def sample(self, on_event: Callable[[datetime], Any]) -> None:
        start, end = self._get_normalized_interval_bounds()

        while start < end:
            for timestamp in self._get_period_timeseries(start):
                if timestamp < end:
                    on_event(timestamp)
                else:
                    break

            start += self._period_duration

    def live(self, on_event: Callable[[datetime], Any]) -> None:
        # TODO check lag and raise warning (e.g detected 5 seconds delay ...)
        def publish_period_thread(timestamps: list[datetime]) -> None:
            now = datetime.now().astimezone()

            for timestamp in timestamps:
                if timestamp >= end:
                    raise EndTimeReaching

                wait_seconds = (timestamp - now).total_seconds()

                if wait_seconds > settings.AHEAD_PUBLICATION_SECONDS >= 0.0:
                    sleep(wait_seconds)
                    now = datetime.now().astimezone()

                on_event(timestamp)

        def prepare_period_thread(start: datetime) -> list[datetime]:
            return self._get_period_timeseries(start)

        actual_eps = self._test_actual_eps()
        required_eps = self._get_required_eps()

        if actual_eps < required_eps:
            raise InputPluginRuntimeError(
                'Not enough performance to produce distributions in time: '
                f'actual EPS is {round(actual_eps)} but {round(required_eps)} '
                'is required'
            )

        start, end = self._get_normalized_interval_bounds()
        now = datetime.now().astimezone()

        if now >= end:
            return

        if now > start:
            skip_periods = (now - start) // self._period_duration
            start += self._period_duration * skip_periods

        timestamps = self._get_period_timeseries(start)

        now = datetime.now().astimezone()
        if start < now:
            timestamps = get_future_slice(timestamps=timestamps, now=now)

        with ThreadPoolExecutor(max_workers=2) as pool:
            while start < end:
                next_start = start + self._period_duration

                prepare_task = pool.submit(prepare_period_thread, next_start)
                publish_task = pool.submit(publish_period_thread, timestamps)

                try:
                    publish_task.result()
                except EndTimeReaching:
                    try:
                        prepare_task.result(timeout=0)
                    except TimeoutError:
                        pass
                    finally:
                        return

                timestamps = prepare_task.result()

                start += self._period_duration

    def get_avg_eps(self) -> float:
        avg_count = self._config.multiplier.ratio
        seconds = self._period_duration.total_seconds()
        return avg_count / seconds

    def _get_required_eps(self) -> float:
        match self._config.randomizer.direction:
            case RandomizerDirection.INCREASE:
                max_count = (
                    self._config.multiplier.ratio
                    * self._config.randomizer.deviation
                )
            case _:
                max_count = self._config.multiplier.ratio

        seconds = self._period_duration.total_seconds()
        return max_count / seconds * settings.REQUIRED_EPS_RESERVE_RATIO

    def _test_actual_eps(self) -> float:
        self._performance_testing = True
        now = datetime.now().astimezone()

        start = perf_counter()
        self._get_period_timeseries(start=now)
        end = perf_counter()

        seconds = end - start
        self._performance_testing = False

        return self._PERFORMANCE_TEST_SAMPLE_SIZE / seconds


class TimePatternPoolInputPlugin(LiveInputPlugin, SampleInputPlugin):
    """Input plugin for combining multiple `TimePatternInputPlugin`
    instances.
    """

    def __init__(self, configs: Sequence[TimePatternConfig]) -> None:
        self._configs = configs
        self._size = len(configs)

        if self._size == 0:
            raise InputPluginConfigurationError(
                'Cannot create pool from empty list of configs'
            )

        self._time_patterns = [
            TimePatternInputPlugin(config) for config in self._configs
        ]

    def sample(self, on_event: Callable[[datetime], Any]) -> None:
        samples = []

        for pattern in self._time_patterns:
            sample = []
            pattern.sample(on_event=lambda ts: sample.append(ts))
            samples.append(sample)

        for ts in merge(*samples):
            on_event(ts)

    def live(self, on_event: Callable[[datetime], Any]) -> None:
        queues: list[Queue] = []
        tasks: list[Future] = []

        with ThreadPoolExecutor(max_workers=self._size) as pool:
            for pattern in self._time_patterns:
                queue: Queue = Queue(maxsize=-1)
                tasks.append(pool.submit(pattern.live, queue.put_nowait))
                queues.append(queue)

            while tasks:
                latest_timestamp = datetime.now().astimezone()
                overhead_seconds = sys.getswitchinterval() * self._size
                sleep(settings.AHEAD_PUBLICATION_SECONDS + overhead_seconds)

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

                for ts in merge(*batches):
                    on_event(ts)

                for i, (task, queue) in enumerate(zip(tasks, queues)):
                    if task.done() and queue.empty():
                        # get result is necessary to propagate exceptions
                        tasks.pop(i).result()
                        queues.pop(i)
