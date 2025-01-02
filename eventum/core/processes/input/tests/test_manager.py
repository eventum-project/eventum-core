from multiprocessing import Queue

from eventum_core.plugins_connector import InputConfigMapping
from eventum_core.processes.input.manager import ExitCode, InputProcessManager
from eventum_core.settings import Settings, TimeMode


def test_manager():
    queue = Queue()

    manager = InputProcessManager(
        config=[
            InputConfigMapping(sample={'count': 5}),
            InputConfigMapping(sample={'count': 10}),
            InputConfigMapping(sample={'count': 15})
        ],
        settings=Settings(events_batch_size=1),
        time_mode=TimeMode.SAMPLE,
        downstream_queue=queue
    )

    assert manager.get_plugin_names() == ['sample'] * 3

    manager.start()
    manager.join()

    assert not manager.is_alive()
    assert manager.exit_code == ExitCode.SUCCESS.value

    assert not queue.empty()

    queue.put(None)

    timestamps = []

    while True:
        batch = queue.get()
        if batch is None:
            break
        timestamps.extend(batch)

    assert len(timestamps) == 30
