from eventum.core.plugins.input.sample import SampleInputPlugin


def test_sample_mode():
    out = []
    SampleInputPlugin(count=100).sample(on_event=out.append)

    assert len(out) == 100
