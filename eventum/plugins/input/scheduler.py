import time
from typing import Iterator

import numpy as np
from pytz import BaseTzInfo

from eventum.plugins.input.batcher import TimestampsBatcher
from eventum.plugins.input.protocols import (
    IdentifiedTimestamps, SupportsIdentifiedTimestampsIterate)
from eventum.plugins.input.utils.time_utils import (now64,
                                                    timedelta64_to_seconds)


class BatchScheduler(SupportsIdentifiedTimestampsIterate):
    """Scheduler of timestamp batches. Scheduler iterates over batches
    of timestamps and does not yield them immediately, but it waits
    until current time reaches the last timestamps in the batch.

    Parameters
    ----------
    batcher : TimestampsBatcher
        Timestamps batcher

    timezone : BaseTzInfo, default=pytz.timezone('UTC')
        Timezone of timestamps in batches, used to track current time
    """

    def __init__(
        self,
        batcher: TimestampsBatcher,
        timezone: BaseTzInfo
    ) -> None:
        self._batcher = batcher
        self._timezone = timezone

    def iterate(
        self,
        skip_past: bool = True
    ) -> Iterator[IdentifiedTimestamps]:
        for array in self._batcher.iterate(skip_past=skip_past):
            now = now64(self._timezone)
            latest_ts: np.datetime64 = array['timestamp'][-1]
            delta = latest_ts - now

            seconds = timedelta64_to_seconds(timedelta=delta)

            if seconds > 0:
                time.sleep(seconds)

            yield array
