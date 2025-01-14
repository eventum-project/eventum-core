import time
from datetime import timedelta
from typing import Iterator

import numpy as np
from pytz import timezone
from pytz.tzinfo import BaseTzInfo

from eventum.plugins.input.protocols import (
    IdentifiedTimestamps, SupportsIdentifiedTimestampsIterate)
from eventum.plugins.input.utils.time_utils import now64


class TimestampsBatcher:
    """Batcher of timestamps.

    Attributes
    ----------
    MIN_BATCH_SIZE : int
        Minimum batch size that can be configured for batcher

    MIN_BATCH_DELAY : float
        Minimum batch delay that can be configured for batcher

    Parameters
    ----------
    source : InputPluginsMerger
        Source of timestamp arrays

    batch_size : int | None, default=100_000
        Maximum size of producing batches, not limited if value is
        `None`, cannot be  less than `MIN_BATCH_SIZE` attribute

    batch_delay: float | None, default=None
        Maximum time (in seconds) for single batch to accumulate
        incoming timestamps, not limited if value is `None`, cannot be
        less then `MIN_BATCH_DELAY` attribute

    scheduling : bool, default=False
        Whether to respect timestamp values and publish them according
        to real time

    timezone : BaseTzInfo, default=pytz.timezone('UTC')
        Timezone of incoming timestamps, used to track current time
        when `scheduling` parameter is set to `True`

    Raises
    ------
    ValueError
        If some parameter is out of allowed range
    """

    MIN_BATCH_SIZE = 1
    MIN_BATCH_DELAY = 0.1

    def __init__(
        self,
        source: SupportsIdentifiedTimestampsIterate,
        batch_size: int | None = 100_000,
        batch_delay: float | None = None,
        scheduling: bool = False,
        timezone: BaseTzInfo = timezone('UTC'),
    ) -> None:
        if batch_size is None and batch_delay is None:
            raise ValueError(
                'Parameters `batch_size` and `batch_delay` '
                'cannot be both `None`'
            )

        if (
            batch_size is not None
            and not self.MIN_BATCH_SIZE <= batch_size
        ):
            raise ValueError(
                'Parameter `batch_size` must be greater or equal to'
                f'{self.MIN_BATCH_SIZE}'
            )

        if batch_delay is not None and batch_delay < self.MIN_BATCH_DELAY:
            raise ValueError(
                'Parameter `batch_delay` must be greater or equal to '
                f'{self.MIN_BATCH_DELAY}'
            )

        self._batch_size = batch_size
        self._batch_delay = batch_delay
        self._scheduling = scheduling
        self._timezone = timezone

        self._source = source

    def iterate(
        self,
        skip_past: bool = True
    ) -> Iterator[IdentifiedTimestamps]:
        """Iterate over batches.

        Parameters
        ----------
        skip_past : bool, default=True
            Wether to skip past timestamps before starting iteration

        Yields
        ------
        TimestampIdArray
            Timestamp batch
        """
        if self._scheduling:
            for batch in self._collect_batch(skip_past=skip_past):
                now = now64(self._timezone)
                latest_ts = batch[-1]

                if latest_ts < now:
                    time.sleep(now - latest_ts)

                yield batch
        else:
            yield from self._collect_batch(skip_past=skip_past)

    def _collect_batch(
        self,
        skip_past: bool
    ) -> Iterator[IdentifiedTimestamps]:
        """Collect batch.

        Parameters
        ----------
        skip_past : bool
            Wether to skip past timestamps before starting iteration

        Yields
        ------
        TimestampIdArray
            Timestamp batch
        """
        read_size = self._batch_size or 10_000

        if self._batch_delay is None:
            yield from self._source.iterate(
                size=read_size,
                skip_past=skip_past
            )
        else:
            delta = np.timedelta64(timedelta(seconds=self._batch_delay), 'us')
            iterator = iter(
                self._source.iterate(size=read_size, skip_past=skip_past)
            )
            to_concatenate: list[IdentifiedTimestamps] = []
            prev_array: IdentifiedTimestamps | None = None

            current_size = 0
            cutoff_timestamp: np.datetime64 | None = None

            while True:
                if prev_array is None:
                    try:
                        array = next(iterator)
                    except StopIteration:
                        break
                else:
                    array = prev_array
                    prev_array = None

                if cutoff_timestamp is None:
                    cutoff_timestamp = array['timestamp'][0] + delta

                cutoff_index = -1

                # check batch delay
                if cutoff_timestamp < array['timestamp'][-1]:
                    cutoff_index = np.searchsorted(
                        a=array['timestamp'],
                        v=cutoff_timestamp,          # type: ignore[assignment]
                        side='right'
                    )
                elif cutoff_timestamp == array['timestamp'][-1]:
                    cutoff_index = array.size

                # check batch size
                if (
                    self._batch_size is not None
                    and (current_size + array.size) >= self._batch_size
                ):
                    index = self._batch_size - current_size
                    if cutoff_index == -1:
                        cutoff_index = index
                    else:
                        cutoff_index = min(cutoff_index, index)

                # process cutoff index
                if cutoff_index == -1:
                    to_concatenate.append(array)
                    current_size += array.size
                else:
                    left_part = array[:cutoff_index]
                    right_part = array[cutoff_index:]

                    if left_part.size > 0:
                        to_concatenate.append(left_part)

                    if right_part.size > 0:
                        prev_array = right_part

                    yield np.concatenate(to_concatenate)
                    to_concatenate.clear()
                    current_size = 0
                    cutoff_timestamp = None

            if to_concatenate:
                yield np.concatenate(to_concatenate)
