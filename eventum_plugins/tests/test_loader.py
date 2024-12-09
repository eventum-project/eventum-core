from pydantic import RootModel

import eventum_plugins.event.plugins as event_plugins
import eventum_plugins.input.plugins as input_plugins
import eventum_plugins.output.plugins as output_plugins
from eventum_plugins.event.base.config import EventPluginConfig
from eventum_plugins.event.base.plugin import EventPlugin
from eventum_plugins.input.base.config import InputPluginConfig
from eventum_plugins.input.base.plugin import InputPlugin
from eventum_plugins.loader import (get_event_plugin_names,
                                    get_input_plugin_names,
                                    get_output_plugin_names, load_event_plugin,
                                    load_input_plugin, load_output_plugin)
from eventum_plugins.output.base.config import OutputPluginConfig
from eventum_plugins.output.base.plugin import OutputPlugin


def test_loading_input_plugin():
    plugin_names = get_input_plugin_names()

    assert plugin_names

    for plugin_name in plugin_names:
        plugin_info = load_input_plugin(plugin_name)

        assert plugin_info.name == plugin_name
        assert plugin_info.package == input_plugins
        assert issubclass(plugin_info.cls, InputPlugin)
        assert (
            issubclass(plugin_info.config_cls, InputPluginConfig)
            or issubclass(plugin_info.config_cls, RootModel)
        )


def test_loading_event_plugins():
    plugin_names = get_event_plugin_names()

    assert plugin_names

    for plugin_name in plugin_names:
        plugin_info = load_event_plugin(plugin_name)

        assert plugin_info.name == plugin_name
        assert plugin_info.package == event_plugins
        assert issubclass(plugin_info.cls, EventPlugin)
        assert (
            issubclass(plugin_info.config_cls, EventPluginConfig)
            or issubclass(plugin_info.config_cls, RootModel)
        )


def test_loading_output_plugins():
    plugin_names = get_output_plugin_names()

    assert plugin_names

    for plugin_name in plugin_names:
        plugin_info = load_output_plugin(plugin_name)

        assert plugin_info.name == plugin_name
        assert plugin_info.package == output_plugins
        assert issubclass(plugin_info.cls, OutputPlugin)
        assert (
            issubclass(plugin_info.config_cls, OutputPluginConfig)
            or issubclass(plugin_info.config_cls, RootModel)
        )
