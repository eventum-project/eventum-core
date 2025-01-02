import os
from datetime import datetime

import pytest

from eventum_plugins.event.plugins.script.config import ScriptEventPluginConfig
from eventum_plugins.event.plugins.script.plugin import ScriptEventPlugin
from eventum_plugins.exceptions import (PluginConfigurationError,
                                        PluginRuntimeError)

STATIC_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'static'
)


def test_plugin_one_event():
    plugin = ScriptEventPlugin(
        config=ScriptEventPluginConfig(
            path=os.path.join(STATIC_DIR, 'one_event.py')
        ),
        params={'id': 1}
    )

    ts = datetime.now().astimezone()
    tags = ('tag1', 'tag2')
    events = plugin.produce(
        params={
            'timestamp': ts,
            'tags': tags
        }
    )

    assert events == [f'{ts.isoformat()}, {tags}']


def test_plugin_events_list():
    plugin = ScriptEventPlugin(
        config=ScriptEventPluginConfig(
            path=os.path.join(STATIC_DIR, 'events_list.py')
        ),
        params={'id': 1}
    )

    ts = datetime.now().astimezone()
    tags = ('tag1', 'tag2')
    events = plugin.produce(
        params={
            'timestamp': ts,
            'tags': tags
        }
    )

    assert events == [ts.isoformat(), *tags]


def test_plugin_missing_function():
    with pytest.raises(PluginConfigurationError):
        ScriptEventPlugin(
            config=ScriptEventPluginConfig(
                path=os.path.join(STATIC_DIR, 'missing_function.py')
            ),
            params={'id': 1}
        )


def test_plugin_exception_in_definition():
    with pytest.raises(PluginConfigurationError):
        ScriptEventPlugin(
            config=ScriptEventPluginConfig(
                path=os.path.join(STATIC_DIR, 'exception_in_definition.py')
            ),
            params={'id': 1}
        )


def test_plugin_exception_in_function():
    plugin = ScriptEventPlugin(
        config=ScriptEventPluginConfig(
            path=os.path.join(
                STATIC_DIR, 'exception_in_function.py')
        ),
        params={'id': 1}
    )

    with pytest.raises(PluginRuntimeError):
        plugin.produce(
            params={
                'timestamp': datetime.now().astimezone(),
                'tags': ('tag1', 'tag2')
            }
        )


def test_plugin_unexistent_file():
    with pytest.raises(PluginConfigurationError):
        ScriptEventPlugin(
            config=ScriptEventPluginConfig(
                path=os.path.join(STATIC_DIR, 'abcdefg.py')
            ),
            params={'id': 1}
        )
