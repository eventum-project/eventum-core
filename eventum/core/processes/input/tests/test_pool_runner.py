import pytest
from eventum.plugins.input.sample import SampleInputConfig, SampleInputPlugin
from pytz import timezone

from eventum_core.processes.input.pool_runner import InputPluginPoolRunner
from eventum_core.processes.input.runner import InputPluginRunner
from eventum_core.settings import TimeMode


@pytest.fixture
def plugins():
    return [
        SampleInputPlugin(
            config=SampleInputConfig(count=5),
            tz=timezone('UTC')
        ),
        SampleInputPlugin(
            config=SampleInputConfig(count=10),
            tz=timezone('UTC')
        ),
        SampleInputPlugin(
            config=SampleInputConfig(count=15),
            tz=timezone('UTC')
        ),
    ]


@pytest.fixture
def plugin_runners(plugins):
    return [
        InputPluginRunner(
            plugin=plugin,
            time_mode=TimeMode.SAMPLE,
            name='sample'
        )
        for plugin in plugins
    ]


def test_pool_runner(plugin_runners):
    pool = InputPluginPoolRunner(runners=plugin_runners)

    id_timestamp_pairs = []
    results = []

    pool.run(
        on_event=(
            lambda timestamp, id:
            id_timestamp_pairs.append((timestamp, id))
        ),
        on_done=(
            lambda id, future:
            results.append((id, future.result()))
        )
    )

    timestamp_ids = [id for _, id in id_timestamp_pairs]
    result_ids = [id for id, _ in results]

    assert len(id_timestamp_pairs) == 30
    assert timestamp_ids.count(0) == 5
    assert timestamp_ids.count(1) == 10
    assert timestamp_ids.count(2) == 15

    assert len(results) == 3
    assert result_ids.count(0) == 1
    assert result_ids.count(1) == 1
    assert result_ids.count(2) == 1


def test_pool_runner_with_errors(plugin_runners):
    pool = InputPluginPoolRunner(runners=plugin_runners)

    def raise_error(*_):
        raise RuntimeError

    errors = []
    ids = []

    def handle_errors(id, future):
        try:
            future.result()
        except RuntimeError as e:
            errors.append(e)
            ids.append(id)

    pool.run(
        on_event=raise_error,
        on_done=handle_errors
    )

    assert ids.count(0) == 1
    assert ids.count(1) == 1
    assert ids.count(2) == 1

    assert len(errors) == 3
    assert len(ids) == 3

    assert all(map(lambda e: isinstance(e, RuntimeError), errors))
