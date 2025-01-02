# type: ignore
import os
from datetime import datetime

import pytest

from eventum.plugins.event.plugins.replay.config import ReplayEventPluginConfig
from eventum.plugins.event.plugins.replay.plugin import ReplayEventPlugin
from eventum.plugins.exceptions import PluginConfigurationError

STATIC_DIR = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    'static'
)


def test_plugin_substitution_with_format():
    plugin = ReplayEventPlugin(
        config=ReplayEventPluginConfig(
            path=os.path.join(STATIC_DIR, 'example.log'),
            timestamp_pattern=r'\[(?P<timestamp>.*?)\]',
            timestamp_format='%Y'
        ),
        params={'id': 1}
    )

    events = []
    now = datetime.now().astimezone()
    for _ in range(10):
        events.extend(
            plugin.produce(
                params={
                    'timestamp': now,
                    'tags': ('a', )
                }
            )
        )

    year = now.year
    assert events == [
        f'127.0.0.1 - - [{year}] "GET /index.html HTTP/1.1" 200 1024',
        f'127.0.0.1 - - [{year}] "POST /form HTTP/1.1" 201 512',
        f'192.168.1.1 - - [{year}] "GET /about.html HTTP/1.1" 200 2048',
        f'10.0.0.1 - - [{year}] "DELETE /resource HTTP/1.1" 403 256',
        f'127.0.0.1 - - [{year}] "PUT /api/data HTTP/1.1" 500 0',
        f'192.168.1.1 - - [{year}] "GET /home HTTP/1.1" 200 128',
        f'10.0.0.1 - - [{year}] "PATCH /update HTTP/1.1" 204 64',
        f'127.0.0.1 - - [{year}] "OPTIONS /info HTTP/1.1" 200 16',
        f'192.168.1.1 - - [{year}] "HEAD /check HTTP/1.1" 200 8',
        f'10.0.0.1 - - [{year}] "TRACE /trace HTTP/1.1" 500 128'
    ]


def test_plugin_substitution_with_default_format():
    plugin = ReplayEventPlugin(
        config=ReplayEventPluginConfig(
            path=os.path.join(STATIC_DIR, 'example.log'),
            timestamp_pattern=r'\[(?P<timestamp>.*?)\]',
        ),
        params={'id': 1}
    )

    events = []

    now = datetime.now().astimezone()
    for _ in range(10):
        events.extend(
            plugin.produce(
                params={
                    'timestamp': now,
                    'tags': ('a', )
                }
            )
        )

    ts = now.isoformat()
    assert events == [
        f'127.0.0.1 - - [{ts}] "GET /index.html HTTP/1.1" 200 1024',
        f'127.0.0.1 - - [{ts}] "POST /form HTTP/1.1" 201 512',
        f'192.168.1.1 - - [{ts}] "GET /about.html HTTP/1.1" 200 2048',
        f'10.0.0.1 - - [{ts}] "DELETE /resource HTTP/1.1" 403 256',
        f'127.0.0.1 - - [{ts}] "PUT /api/data HTTP/1.1" 500 0',
        f'192.168.1.1 - - [{ts}] "GET /home HTTP/1.1" 200 128',
        f'10.0.0.1 - - [{ts}] "PATCH /update HTTP/1.1" 204 64',
        f'127.0.0.1 - - [{ts}] "OPTIONS /info HTTP/1.1" 200 16',
        f'192.168.1.1 - - [{ts}] "HEAD /check HTTP/1.1" 200 8',
        f'10.0.0.1 - - [{ts}] "TRACE /trace HTTP/1.1" 500 128'
    ]


def test_plugin_substitution_with_missing_group():
    plugin = ReplayEventPlugin(
        config=ReplayEventPluginConfig(
            path=os.path.join(STATIC_DIR, 'example.log'),
            timestamp_pattern=r'\[(?P<ts>.*?)\]',
        ),
        params={'id': 1}
    )

    events = plugin.produce(
        params={
            'timestamp': datetime.now().astimezone(),
            'tags': ('a', )
        }
    )

    assert events == [
        '127.0.0.1 - - [01/Dec/2023:12:34:56 +0000] "GET /index.html HTTP/1.1" 200 1024'    # noqa
    ]


def test_plugin_repeat():
    plugin = ReplayEventPlugin(
        config=ReplayEventPluginConfig(
            path=os.path.join(STATIC_DIR, 'example.log'),
            timestamp_pattern=r'\[(?P<timestamp>.*?)\]',
            repeat=True
        ),
        params={'id': 1}
    )

    events = []
    now = datetime.now().astimezone()
    for _ in range(15):
        events.extend(
            plugin.produce(
                params={
                    'timestamp': now,
                    'tags': ('a', )
                }
            )
        )

    ts = now.isoformat()
    assert events == [
        f'127.0.0.1 - - [{ts}] "GET /index.html HTTP/1.1" 200 1024',
        f'127.0.0.1 - - [{ts}] "POST /form HTTP/1.1" 201 512',
        f'192.168.1.1 - - [{ts}] "GET /about.html HTTP/1.1" 200 2048',
        f'10.0.0.1 - - [{ts}] "DELETE /resource HTTP/1.1" 403 256',
        f'127.0.0.1 - - [{ts}] "PUT /api/data HTTP/1.1" 500 0',
        f'192.168.1.1 - - [{ts}] "GET /home HTTP/1.1" 200 128',
        f'10.0.0.1 - - [{ts}] "PATCH /update HTTP/1.1" 204 64',
        f'127.0.0.1 - - [{ts}] "OPTIONS /info HTTP/1.1" 200 16',
        f'192.168.1.1 - - [{ts}] "HEAD /check HTTP/1.1" 200 8',
        f'10.0.0.1 - - [{ts}] "TRACE /trace HTTP/1.1" 500 128',
        f'127.0.0.1 - - [{ts}] "GET /index.html HTTP/1.1" 200 1024',
        f'127.0.0.1 - - [{ts}] "POST /form HTTP/1.1" 201 512',
        f'192.168.1.1 - - [{ts}] "GET /about.html HTTP/1.1" 200 2048',
        f'10.0.0.1 - - [{ts}] "DELETE /resource HTTP/1.1" 403 256',
        f'127.0.0.1 - - [{ts}] "PUT /api/data HTTP/1.1" 500 0'
    ]


def test_plugin_substitution_with_bad_regex():
    with pytest.raises(PluginConfigurationError):
        ReplayEventPlugin(
            config=ReplayEventPluginConfig(
                path=os.path.join(STATIC_DIR, 'example.log'),
                timestamp_pattern=r'\[(?P<timestamp>[.*?)\]',
            ),
            params={'id': 1}
        )


def test_plugin_missing_file():
    with pytest.raises(PluginConfigurationError):
        ReplayEventPlugin(
            config=ReplayEventPluginConfig(
                path=os.path.join(STATIC_DIR, 'unexistent.log'),
                timestamp_pattern=r'\[(?P<timestamp>.*?)\]',
            ),
            params={'id': 1}
        )
