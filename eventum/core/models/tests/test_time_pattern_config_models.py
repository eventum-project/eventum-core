from datetime import datetime, time, timedelta

import pytest
from pydantic import ValidationError

from eventum.core.models.time_pattern_config import (
    BetaDistributionParameters, Distribution, MultiplierConfig,
    OscillatorConfig, RandomizerConfig, RandomizerDirection, SpreaderConfig,
    TimePatternConfig, TimeUnit, TriangularDistributionParameters,
    UniformDistributionParameters)


def test_oscillator_config_with_time():
    OscillatorConfig(
        period=1,
        unit=TimeUnit.SECONDS,
        start=time(hour=12, minute=0),
        end=time(hour=18, minute=0)
    )


def test_oscillator_config_with_datetime():
    OscillatorConfig(
        period=1,
        unit=TimeUnit.SECONDS,
        start=datetime.now(),
        end=datetime.now() + timedelta(days=1)
    )


def test_oscillator_config_with_time_keywords():
    OscillatorConfig(
        period=1,
        unit=TimeUnit.SECONDS,
        start='now',
        end='never'
    )


def test_oscillator_config_with_relative_time():
    OscillatorConfig(
        period=1,
        unit=TimeUnit.SECONDS,
        start='+1h',
        end='+2h'
    )


def test_oscillator_config_with_invalid_period():
    with pytest.raises(ValidationError):
        OscillatorConfig(
            period=0,
            unit=TimeUnit.SECONDS,
            start='now',
            end='never'
        )
    with pytest.raises(ValidationError):
        OscillatorConfig(
            period=-1,
            unit=TimeUnit.SECONDS,
            start='now',
            end='never'
        )


def test_oscillator_config_with_invalid_time_range():
    with pytest.raises(ValidationError):
        OscillatorConfig(
            period=1,
            unit=TimeUnit.SECONDS,
            start='in a hour',
            end='after two days'
        )


def test_multiplier_config():
    MultiplierConfig(ratio=1)


def test_multiplier_config_with_invalid_ratio():
    with pytest.raises(ValidationError):
        MultiplierConfig(ratio=0)

    with pytest.raises(ValidationError):
        MultiplierConfig(ratio=-1)


def test_randomizer_config():
    RandomizerConfig(deviation=0.3, direction=RandomizerDirection.MIXED)


def test_randomizer_config_with_invalid_deviation():
    with pytest.raises(ValidationError):
        RandomizerConfig(deviation=1.5, direction=RandomizerDirection.MIXED)

    with pytest.raises(ValidationError):
        RandomizerConfig(deviation=-3, direction=RandomizerDirection.MIXED)


def test_beta_distribution_parameters():
    BetaDistributionParameters(a=1, b=1)


def test_beta_distribution_parameters_with_invalid_arguments():
    with pytest.raises(ValidationError):
        BetaDistributionParameters(a=1, b=-1)

    with pytest.raises(ValidationError):
        BetaDistributionParameters(a=-50, b=-10)


def test_triangular_distribution_parameters():
    TriangularDistributionParameters(left=0, mode=0.5, right=1)
    TriangularDistributionParameters(left=0.2, mode=0.4, right=0.6)

    TriangularDistributionParameters(left=0, mode=0.5, right=0.5)
    TriangularDistributionParameters(left=0, mode=1, right=1)

    TriangularDistributionParameters(left=0.5, mode=0.5, right=1)
    TriangularDistributionParameters(left=0, mode=0, right=1)


def test_triangular_distribution_parameters_with_invalid_arguments():
    with pytest.raises(ValidationError):
        TriangularDistributionParameters(left=0, mode=0, right=0)

    with pytest.raises(ValidationError):
        TriangularDistributionParameters(left=0.5, mode=0.5, right=0.5)

    with pytest.raises(ValidationError):
        TriangularDistributionParameters(left=1, mode=1, right=1)

    with pytest.raises(ValidationError):
        TriangularDistributionParameters(left=0.4, mode=0.2, right=0.6)

    with pytest.raises(ValidationError):
        TriangularDistributionParameters(left=-3, mode=0, right=3)


def test_uniform_distribution_parameters():
    UniformDistributionParameters(low=0, high=1)
    UniformDistributionParameters(low=0.3, high=0.7)


def test_uniform_distribution_parameters_with_invalid_arguments():
    with pytest.raises(ValidationError):
        UniformDistributionParameters(low=0.1, high=2)

    with pytest.raises(ValidationError):
        UniformDistributionParameters(low=-0.5, high=0.8)

    with pytest.raises(ValidationError):
        UniformDistributionParameters(low=0.4, high=0.2)


def test_spreader_config():
    SpreaderConfig(
        distribution=Distribution.UNIFORM,
        parameters=UniformDistributionParameters(low=0, high=1)
    )
    SpreaderConfig(
        distribution=Distribution.TRIANGULAR,
        parameters=TriangularDistributionParameters(left=0, mode=0.5, right=1)
    )
    SpreaderConfig(
        distribution=Distribution.BETA,
        parameters=BetaDistributionParameters(a=1, b=1)
    )


def test_spreader_config_with_inconsistent_arguments():
    with pytest.raises(ValidationError):
        SpreaderConfig(
            distribution=Distribution.BETA,
            parameters=UniformDistributionParameters(low=0, high=1)
        )


def test_time_pattern_config():
    TimePatternConfig(
        label='Test time pattern',
        oscillator=OscillatorConfig(
            period=1,
            unit=TimeUnit.SECONDS,
            start='now',
            end='never'
        ),
        multiplier=MultiplierConfig(ratio=1),
        randomizer=RandomizerConfig(
            deviation=0.3,
            direction=RandomizerDirection.MIXED
        ),
        spreader=SpreaderConfig(
            distribution=Distribution.UNIFORM,
            parameters=UniformDistributionParameters(low=0, high=1)
        )
    )


def test_time_pattern_config_with_empty_label():
    with pytest.raises(ValidationError):
        TimePatternConfig(
            label='',
            oscillator=OscillatorConfig(
                period=1,
                unit=TimeUnit.SECONDS,
                start='now',
                end='never'
            ),
            multiplier=MultiplierConfig(ratio=1),
            randomizer=RandomizerConfig(
                deviation=0.3,
                direction=RandomizerDirection.MIXED
            ),
            spreader=SpreaderConfig(
                distribution=Distribution.UNIFORM,
                parameters=UniformDistributionParameters(low=0, high=1)
            )
        )
