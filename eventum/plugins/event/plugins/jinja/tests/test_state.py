from multiprocessing import Process

import pytest

from eventum.plugins.event.plugins.jinja.state import (MultiProcessState,
                                                       SingleThreadState)


@pytest.fixture
def single_thread_state():
    return SingleThreadState()


@pytest.fixture
def multiprocess_state():
    return MultiProcessState()


def test_single_thread_state_set_get(single_thread_state: SingleThreadState):
    key = 'test_key'
    value = 'test_value'
    single_thread_state.set(key, value)
    assert single_thread_state.get(key) == value


def test_single_thread_state_update(single_thread_state: SingleThreadState):
    data = {'test_key1': 1, 'test_key2': 2}
    single_thread_state.update(data)
    assert single_thread_state.get('test_key1') == 1
    assert single_thread_state.get('test_key2') == 2


def test_single_thread_state_get_default(
    single_thread_state: SingleThreadState
):
    key = 'test_key'
    default = 'default_value'
    assert single_thread_state.get(key, default) == default


def test_single_thread_state_clear(
    single_thread_state: SingleThreadState
):
    key = 'test_key'
    value = 'test_value'
    single_thread_state.set(key, value)
    assert single_thread_state.get(key) == value
    single_thread_state.clear()
    assert single_thread_state.get(key, default=None) is None


def test_single_thread_state_as_dict(
    single_thread_state: SingleThreadState
):
    key = 'test_key'
    value = 'test_value'
    single_thread_state.set(key, value)
    assert single_thread_state.as_dict() == {key: value}


def test_multiprocess_state_set_get(
    multiprocess_state: MultiProcessState
):
    key = 'test_key'
    value = 'test_value'
    multiprocess_state.set(key, value)
    assert multiprocess_state.get(key) == value


def test_multiprocess_state_update(
    multiprocess_state: MultiProcessState
):
    data = {'test_key1': 1, 'test_key2': 2}
    multiprocess_state.update(data)
    assert multiprocess_state.get('test_key1') == 1
    assert multiprocess_state.get('test_key2') == 2


def test_multiprocess_state_get_default(
    multiprocess_state: MultiProcessState
):
    key = 'test_key!!!'
    default = 'default_value'
    assert multiprocess_state.get(key, default) == default


def test_multiprocess_state_get_for_update(
    multiprocess_state: MultiProcessState
):
    key = 'test_key'
    value = 'test_value'
    multiprocess_state.set(key, value)
    assert multiprocess_state.get_for_update(key) == value
    multiprocess_state.set(key, value + 'updated')


def test_multiprocess_state_cancel_update(
    multiprocess_state: MultiProcessState
):
    key = 'test_key'
    value = 'test_value'
    multiprocess_state.set(key, value)

    assert multiprocess_state.get_for_update(key) == value
    multiprocess_state.cancel_update()


def test_multiprocess_state_clear(
    multiprocess_state: MultiProcessState
):
    key = 'test_key'
    value = 'test_value'
    multiprocess_state.set(key, value)
    assert multiprocess_state.get(key) == value
    multiprocess_state.clear()
    assert multiprocess_state.get(key, default=None) is None


def test_multiprocess_state_as_dict(
    multiprocess_state: MultiProcessState
):
    key = 'test_key'
    value = 'test_value'
    multiprocess_state.set(key, value)
    assert multiprocess_state.as_dict() == {key: value}


def test_multiprocess_state_concurrent_access():
    def worker(key, value) -> None:
        state = MultiProcessState()
        state.set(key, value)

    state = MultiProcessState()
    state.clear()
    processes = []

    for i in range(5):
        process = Process(target=worker, args=(f'key_{i}', f'value_{i}'))
        processes.append(process)
        process.start()

    for process in processes:
        process.join()

    expected_state = {f'key_{i}': f'value_{i}' for i in range(5)}
    assert state.as_dict() == expected_state


def test_multiprocess_state_concurrent_access_same_key():
    def worker(key) -> None:
        state = MultiProcessState()
        v = state.get_for_update(key, 0)
        state.set(key, v + 1)

    state = MultiProcessState()
    processes = []

    for _ in range(5):
        process = Process(target=worker, args=('incrementing_key', ))
        processes.append(process)
        process.start()

    for process in processes:
        process.join()

    assert state.get('incrementing_key') == 5
