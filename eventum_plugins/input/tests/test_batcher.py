import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

import numpy as np
import pytest
from pytz import timezone

from eventum_plugins.input.batcher import BatcherFullError, TimestampsBatcher


def test_valid_parameters():
    TimestampsBatcher()
    TimestampsBatcher(batch_size=100, batch_delay=None)
    TimestampsBatcher(batch_size=None, batch_delay=1)
    TimestampsBatcher(batch_size=100, batch_delay=1)
    TimestampsBatcher(scheduling=True, timezone=timezone('Europe/Moscow'))


def test_invalid_parameters():
    with pytest.raises(ValueError):
        TimestampsBatcher(batch_size=None, batch_delay=None)

    with pytest.raises(ValueError):
        TimestampsBatcher(batch_size=0)

    with pytest.raises(ValueError):
        TimestampsBatcher(batch_delay=0.000001)

    with pytest.raises(ValueError):
        TimestampsBatcher(batch_size=1000, queue_max_size=10)


@pytest.fixture
def timestamps():
    return np.full(
        1_000_000,
        np.datetime64('now', 'us')
    )


def test_size_batching(timestamps):
    batcher = TimestampsBatcher(batch_size=100_000)
    batcher.add(timestamps)
    batcher.close()

    batches = list(batcher.scroll())
    assert len(batches) == 10
    assert all([batch.size == 100_000 for batch in batches])


def test_uneven_size_batching(timestamps):
    batcher = TimestampsBatcher(batch_size=30_000)
    batcher.add(timestamps)
    batcher.close()

    batches = list(batcher.scroll())
    assert len(batches) == 34
    assert (
        all([batch.size == 30_000 for batch in batches[:-1]])
        and batches[-1].size == 10_000
    )


def test_accumulating_size_batching(timestamps):
    batcher = TimestampsBatcher(batch_size=5_000_000)
    for _ in range(10):
        batcher.add(timestamps)
    batcher.close()

    batches = list(batcher.scroll())
    assert len(batches) == 2
    assert all([batch.size == 5_000_000 for batch in batches])


def test_partial_accumulating_size_batching(timestamps):
    batcher = TimestampsBatcher(batch_size=5_000_000)
    for _ in range(3):
        batcher.add(timestamps)
    batcher.close()

    batches = list(batcher.scroll())
    assert len(batches) == 1
    assert batches[0].size == 3_000_000


def test_delay_batching():
    batcher = TimestampsBatcher(batch_size=None, batch_delay=0.1)

    def add_timestamps():
        timestamps = np.array([np.datetime64('now'), np.datetime64('now')])

        for _ in range(5):
            batcher.add(timestamps)

        time.sleep(0.12)
        batcher.add(timestamps)
        time.sleep(0.05)
        batcher.add(timestamps)

        batcher.close()

    batches = []
    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.submit(add_timestamps)

        for batch in batcher.scroll():
            batches.append(batch)

    assert len(batches) == 2
    assert len(batches[0]) == 10
    assert len(batches[1]) == 4


def test_delay_with_size_batching():
    batcher = TimestampsBatcher(batch_size=5, batch_delay=0.1)

    def add_timestamps():
        timestamps = np.array([np.datetime64('now'), np.datetime64('now')])

        for _ in range(5):
            batcher.add(timestamps)

        time.sleep(0.12)
        batcher.add(timestamps)
        time.sleep(0.05)
        batcher.add(timestamps)

        batcher.close()

    batches = []
    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.submit(add_timestamps)

        for batch in batcher.scroll():
            batches.append(batch)

    assert len(batches) == 3
    assert len(batches[0]) == 5
    assert len(batches[1]) == 5
    assert len(batches[2]) == 4


def test_delay_with_partial_size_batching():
    batcher = TimestampsBatcher(batch_size=12, batch_delay=0.1)

    def add_timestamps():
        timestamps = np.array([np.datetime64('now'), np.datetime64('now')])

        for _ in range(5):
            batcher.add(timestamps)

        time.sleep(0.12)
        batcher.add(timestamps)
        time.sleep(0.05)
        batcher.add(timestamps)

        batcher.close()

    batches = []
    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.submit(add_timestamps)

        for batch in batcher.scroll():
            batches.append(batch)

    assert len(batches) == 2
    assert len(batches[0]) == 10
    assert len(batches[1]) == 4


def test_delay_with_uneven_size_batching():
    batcher = TimestampsBatcher(batch_size=8, batch_delay=0.1)

    def add_timestamps():
        timestamps = np.array([np.datetime64('now'), np.datetime64('now')])

        for _ in range(5):
            batcher.add(timestamps)

        time.sleep(0.12)
        batcher.add(timestamps)
        time.sleep(0.05)
        batcher.add(timestamps)

        batcher.close()

    batches = []
    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.submit(add_timestamps)

        for batch in batcher.scroll():
            batches.append(batch)

    assert len(batches) == 3
    assert len(batches[0]) == 8
    assert len(batches[1]) == 2
    assert len(batches[2]) == 4


def test_carry_over_delay_with_uneven_size_batching():
    batcher = TimestampsBatcher(batch_size=8, batch_delay=0.1)

    def add_timestamps():
        timestamps = np.array([np.datetime64('now'), np.datetime64('now')])

        for _ in range(5):
            batcher.add(timestamps)
            time.sleep(0.02)

        time.sleep(0.07)
        batcher.add(timestamps)
        batcher.close()

    batches = []
    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.submit(add_timestamps)

        for batch in batcher.scroll():
            batches.append(batch)

    assert len(batches) == 2
    assert len(batches[0]) == 8
    assert len(batches[1]) == 4


@pytest.fixture
def timestamps_batch():
    return np.full(1_000, np.datetime64('now', 'us'))


def test_high_throughput_batching(timestamps_batch):
    batcher = TimestampsBatcher(batch_size=10_000, batch_delay=0.1)

    def add_timestamps():
        for _ in range(10_000):
            batcher.add(timestamps_batch)

        batcher.close()

    batches = []
    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.submit(add_timestamps)

        for batch in batcher.scroll():
            batches.append(batch)

    assert np.concatenate(batches).size == 10_000_000


def test_high_throughput_size_batching(timestamps_batch):
    batcher = TimestampsBatcher(batch_size=10_000, batch_delay=None)

    def add_timestamps():
        for _ in range(10_000):
            batcher.add(timestamps_batch)

        batcher.close()

    batches = []
    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.submit(add_timestamps)

        for batch in batcher.scroll():
            batches.append(batch)

    assert np.concatenate(batches).size == 10_000_000


def test_high_throughput_delay_batching(timestamps_batch):
    batcher = TimestampsBatcher(batch_size=None, batch_delay=1.0)

    def add_timestamps():
        for _ in range(10_000):
            batcher.add(timestamps_batch)

        batcher.close()

    batches = []
    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.submit(add_timestamps)

        for batch in batcher.scroll():
            batches.append(batch)

    assert np.concatenate(batches).size == 10_000_000


def test_queue_size():
    batcher = TimestampsBatcher(batch_size=10, queue_max_size=10)
    assert batcher.queue_max_size == 10
    assert batcher.queue_available_size == 10
    assert batcher.queue_current_size == 0

    timestamps = np.full(5, np.datetime64('now', 'us'))
    batcher.add(timestamps, block=False)

    assert batcher.queue_available_size == 5
    assert batcher.queue_current_size == 5

    timestamps = np.full(4, np.datetime64('now', 'us'))
    batcher.add(timestamps, block=False)

    assert batcher.queue_available_size == 1
    assert batcher.queue_current_size == 9

    with pytest.raises(BatcherFullError):
        batcher.add(timestamps, block=False)

    assert batcher.queue_available_size == 1
    assert batcher.queue_current_size == 9

    timestamps = np.full(1, np.datetime64('now', 'us'))
    batcher.add(timestamps, block=False)

    assert batcher.queue_available_size == 0
    assert batcher.queue_current_size == 10

    batcher.close()
    _ = list(batcher.scroll())

    assert batcher.queue_available_size == 10
    assert batcher.queue_current_size == 0


def test_queue_instant_overflow():
    batcher = TimestampsBatcher(batch_size=10, queue_max_size=10)
    timestamps = np.full(100, np.datetime64('now', 'us'))

    with pytest.raises(BatcherFullError):
        batcher.add(timestamps, block=False)


def test_blocking_queue_adding():
    batcher = TimestampsBatcher(
        batch_size=10,
        batch_delay=None,
        queue_max_size=10
    )

    def add_timestamps():
        timestamps = np.full(105, np.datetime64('now', 'us'))
        batcher.add(timestamps, block=True)
        batcher.close()

    batches = []
    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.submit(add_timestamps)

        for batch in batcher.scroll():
            batches.append(batch)

    assert len(batches) == 11
    assert all([batch.size == 10 for batch in batches[:-1]])
    assert batches[-1].size == 5


def test_size_batching_with_scheduling():
    batcher = TimestampsBatcher(
        batch_size=10,
        scheduling=True,
        timezone=timezone('UTC')
    )
    now = np.datetime64('now')
    timestamps = np.array(
        [now + np.timedelta64(i, 'ms') for i in range(0, 100)]
    )

    batcher.add(timestamps)
    batcher.close()

    batches = list(batcher.scroll())
    assert len(batches) == 10
    assert all([batch.size == 10 for batch in batches])


def test_delay_batching_with_scheduling():
    batcher = TimestampsBatcher(
        batch_size=None,
        batch_delay=0.1,
        scheduling=True,
        timezone=timezone('UTC')
    )
    now = np.datetime64('now')
    timestamps = np.array(
        [now + np.timedelta64(i, 'ms') for i in range(0, 100)]
    )

    batcher.add(timestamps)
    batcher.close()

    batches = list(batcher.scroll())
    assert len(batches) == 1
    assert batches[0].size == 100


def test_size_batching_with_scheduling_and_sparse_timestamps():
    batcher = TimestampsBatcher(
        batch_size=10,
        scheduling=True,
        timezone=timezone('UTC')
    )
    now = np.datetime64(datetime.now(UTC).replace(tzinfo=None))
    start = time.perf_counter()
    timestamps = np.array(
        [now + np.timedelta64(i, 'ms') for i in range(0, 1000, 10)]
    )
    assert timestamps.size == 100
    assert (timestamps[-1] - timestamps[0]) == np.timedelta64(990, 'ms')

    batcher.add(timestamps)
    batcher.close()

    assert batcher._past_timestamps_count < 100

    batches = list(batcher.scroll())
    end = time.perf_counter()

    assert len(batches) == 10
    assert all([batch.size == 10 for batch in batches])
    assert (end - start) >= 0.990


def test_delay_batching_with_scheduling_and_sparse_timestamps():
    batcher = TimestampsBatcher(
        batch_size=None,
        batch_delay=0.1,
        scheduling=True,
        timezone=timezone('UTC')
    )
    now = np.datetime64(datetime.now(UTC).replace(tzinfo=None))
    start = time.perf_counter()
    timestamps = np.array(
        [now + np.timedelta64(i, 'ms') for i in range(0, 1000, 10)]
    )
    assert timestamps.size == 100
    assert (timestamps[-1] - timestamps[0]) == np.timedelta64(990, 'ms')

    batcher.add(timestamps)
    batcher.close()

    assert batcher._past_timestamps_count < 100

    batches = list(batcher.scroll())
    end = time.perf_counter()

    assert 1 < len(batches) <= 11
    assert (end - start) >= 0.990


def test_size_and_delay_batching_with_scheduling_and_sparse_timestamps():
    batcher = TimestampsBatcher(
        batch_size=10,
        batch_delay=0.15,
        scheduling=True,
        timezone=timezone('UTC')
    )
    now = np.datetime64(datetime.now(UTC).replace(tzinfo=None))
    start = time.perf_counter()
    timestamps = np.array(
        [now + np.timedelta64(i, 'ms') for i in range(0, 990, 10)]
    )
    out_of_batch = np.array([now + np.timedelta64(1200, 'ms')])
    assert timestamps.size == 99
    assert (timestamps[-1] - timestamps[0]) == np.timedelta64(980, 'ms')

    batcher.add(timestamps)
    batcher.add(out_of_batch)
    batcher.close()

    assert batcher._past_timestamps_count < 100

    batches = list(batcher.scroll())
    end = time.perf_counter()

    assert len(batches) == 11
    assert all([batch.size == 10 for batch in batches[:-2]])
    assert batches[-2].size == 9
    assert batches[-1].size == 1
    assert (end - start) >= 1.2
