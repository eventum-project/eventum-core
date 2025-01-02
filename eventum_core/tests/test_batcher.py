import time

from eventum_core.batcher import Batcher


def test_batcher_size_condition():
    bucket = []
    with Batcher(size=10, timeout=0.1, callback=bucket.append) as batcher:
        for i in range(100):
            batcher.add(i)

    assert len(bucket) == 10

    for batch in bucket:
        assert len(batch) == 10


def test_batcher_timeout_condition():
    bucket = []
    with Batcher(size=100, timeout=0.01, callback=bucket.append) as batcher:
        for i in range(10):
            batcher.add(i)
            time.sleep(0.05)

    assert len(bucket) == 10

    for batch in bucket:
        assert len(batch) == 1


def test_batcher_ordering():
    bucket = []
    with Batcher(size=100, timeout=1, callback=bucket.append) as batcher:
        for i in range(100):
            batcher.add(i)

    flattened_bucket = []
    for batch in bucket:
        flattened_bucket.extend(batch)

    flattened_bucket == list(range(100))
