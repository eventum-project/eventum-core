import pytest
from eventum_plugins.input.sample import SampleInputConfig, SampleInputPlugin
from pytz import timezone

from eventum_core.processes.input.runner import (InputPluginRunner,
                                                 UnsupportedTimeModeError)
from eventum_core.settings import TimeMode


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

    timestamps = []
    runner.run(on_event=timestamps.append)

    assert len(timestamps) == 10


def test_runner_with_improper_mode(plugin):
    with pytest.raises(UnsupportedTimeModeError):
        InputPluginRunner(
            plugin=plugin,
            time_mode=TimeMode.LIVE,
            name='sample'
        )
