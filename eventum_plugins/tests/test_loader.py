from eventum_plugins.enums import PluginType
from eventum_plugins.input._base import InputPlugin, InputPluginConfig
from eventum_plugins.loader import (get_event_plugin_names,
                                    get_input_plugin_names,
                                    get_output_plugin_names, load_event_plugin,
                                    load_input_plugin, load_output_plugin)

# from eventum_plugins.event._base import InputPlugin
# from eventum_plugins.output._base import InputPlugin


def test_loading_input_plugin():
    for plugin_name in get_input_plugin_names():
        plugin_info = load_input_plugin(plugin_name)

        assert issubclass(plugin_info.cls, InputPlugin)
        assert issubclass(plugin_info.config_cls, InputPluginConfig)
        assert plugin_info.type == PluginType.INPUT


def test_loading_event_plugins():
    raise NotImplementedError


def test_loading_output_plugins():
    raise NotImplementedError
