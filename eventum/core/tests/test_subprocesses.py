

from datetime import datetime
from multiprocessing import Event, Process, Queue, TimeoutError, Value

import numpy as np

from eventum.core.models.application_config import (JinjaEventConfig,
                                                    SampleInputConfig,
                                                    TemplateConfig,
                                                    TemplatePickingMode)
from eventum.core.models.time_mode import TimeMode
from eventum.core.plugins.output.null import NullOutputPlugin
from eventum.core.settings import EVENTS_BATCH_TIMEOUT, OUTPUT_BATCH_TIMEOUT
from eventum.core.subprocesses import (start_event_subprocess,
                                       start_input_subprocess,
                                       start_output_subprocess)


def test_input_subprocess():
    queue = Queue()
    is_done = Event()

    proc_input = Process(
        target=start_input_subprocess,
        args=(
            {'sample': SampleInputConfig(count=10)},
            TimeMode.SAMPLE,
            queue,
            is_done
        )
    )
    proc_input.start()

    try:
        is_done.wait(timeout=EVENTS_BATCH_TIMEOUT + 1)
    except TimeoutError:
        proc_input.terminate()
        raise AssertionError('Long subprocess execution')

    assert is_done.is_set()
    assert not queue.empty()

    batch = queue.get()
    stop_signal = queue.get()

    assert len(batch) == 10
    assert stop_signal is None

    proc_input.join()


def test_event_subprocess():
    input_queue = Queue()
    event_queue = Queue()
    is_done = Event()

    proc_event = Process(
        target=start_event_subprocess,
        args=(
            JinjaEventConfig(
                params={},
                samples={},
                mode=TemplatePickingMode.ALL,
                templates={
                    'test': TemplateConfig(template='tests/test.json.jinja')
                }
            ),
            input_queue,
            event_queue,
            is_done
        )
    )

    proc_event.start()
    input_queue.put(np.array([datetime.now().isoformat()] * 10))
    input_queue.put(None)

    try:
        is_done.wait(timeout=OUTPUT_BATCH_TIMEOUT + 1)
    except TimeoutError:
        proc_event.terminate()
        raise AssertionError('Long subprocess execution')

    assert is_done.is_set()
    assert not event_queue.empty()

    total_events = 0
    while True:
        batch = event_queue.get()
        if batch is None:
            break
        total_events += len(batch)

    assert total_events == 10

    proc_event.join()


def test_output_subprocess():
    event_queue = Queue()
    processed_event = Value('Q', 0)
    is_done = Event()

    proc_output = Process(
        target=start_output_subprocess,
        args=(
            {'null': NullOutputPlugin()},
            event_queue,
            processed_event,
            is_done
        )
    )

    proc_output.start()
    event_queue.put(np.array(['rendered event\n'] * 10))
    event_queue.put(None)

    try:
        is_done.wait(timeout=1)
    except TimeoutError:
        proc_output.terminate()
        raise AssertionError('Long subprocess execution')

    assert is_done.is_set()
    assert processed_event.value == 10

    proc_output.join()
