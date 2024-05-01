from eventum.core.models.time_pattern_config import (
    Distribution, MultiplierConfig, OscillatorConfig, RandomizerConfig,
    RandomizerDirection, SpreaderConfig, TimePatternConfig, TimeUnit,
    UniformDistributionParameters)
from eventum.core.plugins.input.time_patterns import TimePatternInputPlugin


def test_sample():
    out = []
    TimePatternInputPlugin(
        config=TimePatternConfig(
            label='Test',
            oscillator=OscillatorConfig(
                period=1,
                unit=TimeUnit.SECONDS,
                start='now',
                end='+10s'
            ),
            multiplier=MultiplierConfig(ratio=10),
            randomizer=RandomizerConfig(
                deviation=0,
                direction=RandomizerDirection.MIXED
            ),
            spreader=SpreaderConfig(
                distribution=Distribution.UNIFORM,
                parameters=UniformDistributionParameters(low=0, high=1)
            )
        )
    ).sample(on_event=out.append)

    assert len(out) == 100


def test_live():
    out = []
    TimePatternInputPlugin(
        config=TimePatternConfig(
            label='Test',
            oscillator=OscillatorConfig(
                period=1,
                unit=TimeUnit.SECONDS,
                start='+1s',
                end='+1s'
            ),
            multiplier=MultiplierConfig(ratio=10),
            randomizer=RandomizerConfig(
                deviation=0,
                direction=RandomizerDirection.MIXED
            ),
            spreader=SpreaderConfig(
                distribution=Distribution.UNIFORM,
                parameters=UniformDistributionParameters(low=0, high=1)
            )
        )
    ).live(on_event=out.append)
    assert len(out) == 10
