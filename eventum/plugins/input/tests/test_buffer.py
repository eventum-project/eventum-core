import numpy as np

from eventum.plugins.input.buffer import Buffer


def test_add_v():
    buff = Buffer()

    buff.push(np.datetime64('now', 'us'))
    buff.push(np.datetime64('now', 'us'))
    buff.push(np.datetime64('now', 'us'))
    buff.push(np.datetime64('now', 'us'))

    assert buff.size == 4
    assert not list(buff.read(5, partial=False))

    buff.push(np.datetime64('now', 'us'))
    assert buff.size == 5

    ts_batches = list(buff.read(5, partial=False))
    assert buff.size == 0

    assert len(ts_batches) == 1
    assert len(ts_batches[0]) == 5


def test_add_v_many():
    buff = Buffer()

    for _ in range(6):
        buff.push(np.datetime64('now', 'us'))

    assert buff.size == 6

    for _ in range(4):
        buff.push(np.datetime64('now', 'us'))

    assert buff.size == 10

    ts_batches = list(buff.read(5, partial=False))
    assert buff.size == 0

    assert len(ts_batches) == 2
    assert len(ts_batches[0]) == 5 and len(ts_batches[0]) == 5


def test_add_v_with_remaining():
    buff = Buffer()

    for _ in range(6):
        buff.push(np.datetime64('now', 'us'))

    assert buff.size == 6

    ts_batches = list(buff.read(5, partial=False))

    assert buff.size == 1
    assert len(ts_batches) == 1
    assert len(ts_batches[0]) == 5


def test_add_v_partial():
    buff = Buffer()

    for _ in range(6):
        buff.push(np.datetime64('now', 'us'))

    assert buff.size == 6

    ts_batches = list(buff.read(5, partial=True))

    assert buff.size == 0
    assert len(ts_batches) == 2
    assert len(ts_batches[0]) == 5 and len(ts_batches[1]) == 1


def test_add_m():
    buff = Buffer()

    for _ in range(5):
        buff.m_push(np.datetime64('now', 'us'), 2)

    assert buff.size == 10

    ts_batches = list(buff.read(5, partial=False))

    assert buff.size == 0
    assert len(ts_batches) == 2
    assert len(ts_batches[0]) == 5 and len(ts_batches[1]) == 5


def test_add_m_partial():
    buff = Buffer()

    for _ in range(5):
        buff.m_push(np.datetime64('now', 'us'), 2)

    assert buff.size == 10

    ts_batches = list(buff.read(3, partial=False))

    assert buff.size == 1
    assert len(ts_batches) == 3
    assert (
        len(ts_batches[0]) == 3
        and len(ts_batches[1]) == 3
        and len(ts_batches[2]) == 3
    )

    ts_batches = list(buff.read(3, partial=True))
    assert buff.size == 0
    assert len(ts_batches) == 1
    assert len(ts_batches[0]) == 1


def test_add_mv():
    buff = Buffer()

    for _ in range(2):
        buff.mv_push(
            np.full(10, np.datetime64('now', 'us'), dtype='datetime64[us]')
        )

    assert buff.size == 20

    ts_batches = list(buff.read(5, partial=False))

    assert buff.size == 0
    assert len(ts_batches) == 4
    assert all(len(batch) == 5 for batch in ts_batches)


def test_add_mv_partial():
    buff = Buffer()

    for _ in range(2):
        buff.mv_push(
            np.full(10, np.datetime64('now', 'us'), dtype='datetime64[us]')
        )

    assert buff.size == 20

    ts_batches = list(buff.read(7, partial=True))

    assert buff.size == 0
    assert len(ts_batches) == 3
    assert (
        len(ts_batches[0]) == 7
        and len(ts_batches[1]) == 7
        and len(ts_batches[2]) == 6
    )


def test_add():
    buff = Buffer()

    buff.mv_push(
        np.full(10, np.datetime64('now', 'us'), dtype='datetime64[us]')
    )
    buff.m_push(np.datetime64('now', 'us'), 5)
    buff.push(np.datetime64('now', 'us'))
    buff.m_push(np.datetime64('now', 'us'), 5)

    assert buff.size == 21

    ts_batches = list(buff.read(7, partial=True))

    assert buff.size == 0
    assert len(ts_batches) == 3
    assert (
        len(ts_batches[0]) == 7
        and len(ts_batches[1]) == 7
        and len(ts_batches[2]) == 7
    )


def test_add_partial():
    buff = Buffer()

    buff.mv_push(
        np.full(10, np.datetime64('now', 'us'), dtype='datetime64[us]')
    )
    buff.m_push(np.datetime64('now', 'us'), 5)
    buff.push(np.datetime64('now', 'us'))
    buff.m_push(np.datetime64('now', 'us'), 5)

    assert buff.size == 21

    ts_batches = list(buff.read(10, partial=True))

    assert buff.size == 0
    assert len(ts_batches) == 3
    assert (
        len(ts_batches[0]) == 10
        and len(ts_batches[1]) == 10
        and len(ts_batches[2]) == 1
    )


def test_ordering():
    buff = Buffer()

    buff.mv_push(
        np.full(10, np.datetime64('now', 'us'), dtype='datetime64[us]')
    )
    buff.m_push(np.datetime64('now', 'us'), 5)
    buff.push(np.datetime64('now', 'us'))
    buff.m_push(np.datetime64('now', 'us'), 5)

    assert buff.size == 21

    ts_batches = list(buff.read(1, partial=False))
    timestamps = np.concatenate(ts_batches)

    assert timestamps.size == 21

    assert np.all(timestamps[:-1] <= timestamps[1:])
