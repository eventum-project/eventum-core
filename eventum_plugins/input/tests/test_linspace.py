from datetime import datetime

import pytest
from numpy import datetime64
from pydantic import ValidationError
from pytz import timezone

from eventum_plugins.input.linspace import (LinspaceInputConfig,
                                            LinspaceInputPlugin)


def test_valid_config():
    LinspaceInputConfig(
        start=datetime.fromisoformat('2024-01-01T00:00:00.000Z'),
        end=datetime.fromisoformat('2025-01-01T00:00:00.000Z'),
        count=10,
        endpoint=True
    )


def test_invalid_config():
    with pytest.raises(ValidationError):
        LinspaceInputConfig(
            start=datetime.fromisoformat('2025-01-01T00:00:00.000Z'),
            end=datetime.fromisoformat('2024-01-01T00:00:00.000Z'),
            count=10,
            endpoint=True
        )


@pytest.mark.parametrize(
    ('start', 'end', 'count', 'endpoint', 'expected'),
    [
        ('2024-01-01T00:00:00.000Z', '2024-01-01T00:00:03.000Z', 3, False, [
            datetime64(datetime.fromisoformat('2024-01-01T00:00:00.000')),
            datetime64(datetime.fromisoformat('2024-01-01T00:00:01.000')),
            datetime64(datetime.fromisoformat('2024-01-01T00:00:02.000')),
        ]),
        ('2024-01-01T00:00:00.000Z', '2024-01-01T00:00:01.000Z', 5, True, [
            datetime64(datetime.fromisoformat('2024-01-01T00:00:00.000')),
            datetime64(datetime.fromisoformat('2024-01-01T00:00:00.250')),
            datetime64(datetime.fromisoformat('2024-01-01T00:00:00.500')),
            datetime64(datetime.fromisoformat('2024-01-01T00:00:00.750')),
            datetime64(datetime.fromisoformat('2024-01-01T00:00:01.000')),
        ]),
    ]
)
def test_linspace_sample(start, end, count, endpoint, expected):
    config = LinspaceInputConfig(
        start=datetime.fromisoformat(start),
        end=datetime.fromisoformat(end),
        count=count,
        endpoint=endpoint
    )

    plugin = LinspaceInputPlugin(config=config, tz=timezone('UTC'))

    events = []
    plugin.sample(on_event=events.append)

    assert events == expected
