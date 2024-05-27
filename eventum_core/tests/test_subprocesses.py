

import time
from datetime import datetime
from multiprocessing import Event, Process, Queue, TimeoutError, Value

import numpy as np
from eventum_plugins.event.jinja import (JinjaEventConfig, TemplateConfig,
                                         TemplatePickingMode)
from eventum_plugins.input.sample import SampleInputConfig
from jinja2 import DictLoader

from eventum_core.app import TimeMode
from eventum_core.plugins_connector import InputConfigMapping
from eventum_core.settings import Settings
from eventum_core.subprocesses import (start_event_subprocess,
                                       start_input_subprocess,
                                       start_output_subprocess)


def test_input_subprocess():
    queue = Queue()
    is_done = Event()

    proc_input = Process(
        target=start_input_subprocess,
        args=(
            InputConfigMapping(sample=SampleInputConfig(count=10)),
            Settings(events_batch_timeout=0),
            TimeMode.SAMPLE,
            queue,
            is_done
        )
    )
    proc_input.start()

    try:
        is_done.wait(timeout=1)
    except TimeoutError:
        proc_input.terminate()
        raise AssertionError('Long subprocess execution')

    # IPC sleep
    time.sleep(0.5)

    assert not queue.empty()

    elements = []
    while True:
        batch = queue.get(timeout=0.1)

        if batch is None:
            break

        elements.extend(batch)

    assert len(elements) == 10

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
                    'test': TemplateConfig(template='test.jinja')
                }
            ),
            DictLoader({'test.jinja': '{{ timestamp }}'}),
            Settings(timestamp_field_name='timestamp', output_batch_timeout=0),
            input_queue,
            event_queue,
            is_done
        )
    )

    proc_event.start()
    input_queue.put(np.array([datetime.now().isoformat()] * 10))
    input_queue.put(None)

    try:
        is_done.wait(timeout=1)
    except TimeoutError:
        proc_event.terminate()
        raise AssertionError('Long subprocess execution')

    # IPC sleep
    time.sleep(0.5)

    assert not event_queue.empty()

    total_events = 0
    while True:
        batch = event_queue.get(timeout=0.1)

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
            [],
            Settings(),
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

    # IPC sleep
    time.sleep(0.5)

    assert processed_event.value == 10

    proc_output.join()
