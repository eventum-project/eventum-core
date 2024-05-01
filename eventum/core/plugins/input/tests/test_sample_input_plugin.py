import pytest

from eventum.core.plugins.input.base import InputPluginConfigurationError
from eventum.core.plugins.input.sample import SampleInputPlugin


def test_sample_mode():
    out = []
    SampleInputPlugin(count=100).sample(on_event=out.append)

    assert len(out) == 100
    assert len(set(out)) == 1


def test_improper_configuration():
    with pytest.raises(InputPluginConfigurationError):
        SampleInputPlugin(count=0)

    with pytest.raises(InputPluginConfigurationError):
        SampleInputPlugin(count=-10)
