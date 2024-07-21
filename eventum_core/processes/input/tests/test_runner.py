import pytest
from eventum_core.processes.input.runner import (InputPluginRunner,
                                                 UnsupportedTimeModeError)
from eventum_core.settings import TimeMode
from eventum_plugins.input.sample import SampleInputConfig, SampleInputPlugin
from pytz import timezone


@pytest.fixture
def plugin():
    return SampleInputPlugin(
        config=SampleInputConfig(count=10),
        tz=timezone('UTC')
    )


def test_runner(plugin):
    runner = InputPluginRunner(
        plugin=plugin,
        time_mode=TimeMode.SAMPLE,
        name='sample'
    )

    events = []
    runner.run(on_event=events.append)

    assert len(events) == 10


def test_runner_with_improper_mode(plugin):
    with pytest.raises(UnsupportedTimeModeError):
        InputPluginRunner(
            plugin=plugin,
            time_mode=TimeMode.LIVE,
            name='sample'
        )
