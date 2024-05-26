import os

import pytest
from freezegun import freeze_time
from pydantic import ValidationError
from pytz import timezone

from eventum_plugins.input.base import InputPluginConfigurationError
from eventum_plugins.input.time_patterns import (TimePatternPoolInputPlugin,
                                                 TimePatternsInputConfig)

STATIC_FILES_DIR = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    'static'
)


def test_valid_config():
    TimePatternsInputConfig(
        configs=tuple(
            os.path.join(STATIC_FILES_DIR, 'time_pattern_valid.yml'),
        )
    )


def test_invalid_config():
    with pytest.raises(ValidationError):
        TimePatternsInputConfig(
            configs=tuple()
        )


def test_invalid_config_structure():
    config = TimePatternsInputConfig(
        configs=tuple(
            os.path.join(STATIC_FILES_DIR, 'time_pattern_invalid.yml'),
        )
    )
    with pytest.raises(InputPluginConfigurationError):
        TimePatternPoolInputPlugin(config=config, tz=timezone('UTC'))


def test_time_pattern_sample():
    config = TimePatternsInputConfig(
        configs=tuple([
            os.path.join(STATIC_FILES_DIR, 'time_pattern_valid.yml')
        ])
    )
    plugin = TimePatternPoolInputPlugin(config=config, tz=timezone('UTC'))

    events = []

    with freeze_time('2024-01-01T00:00:00.000Z', tz_offset=0):
        plugin.sample(on_event=events.append)

    assert len(events) == 1000


def test_time_pattern_live():
    config = TimePatternsInputConfig(
        configs=tuple([
            os.path.join(STATIC_FILES_DIR, 'time_pattern_valid.yml')
        ])
    )
    plugin = TimePatternPoolInputPlugin(config=config, tz=timezone('UTC'))

    events = []

    with freeze_time('2024-01-01T00:00:00.000Z', tz_offset=0, tick=True):
        plugin.live(on_event=events.append)

    assert 0 < len(events) <= 1000
