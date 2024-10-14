import eventum_plugins.input.plugins as input_plugins
from eventum_plugins.input.base.config import InputPluginConfig
from eventum_plugins.input.base.plugin import InputPlugin
from eventum_plugins.loader import get_input_plugin_names, load_input_plugin


def test_loading_input_plugin():
    plugin_names = get_input_plugin_names()

    assert plugin_names

    for plugin_name in plugin_names:
        plugin_info = load_input_plugin(plugin_name)

        assert plugin_info.name == plugin_name
        assert plugin_info.package == input_plugins
        assert issubclass(plugin_info.cls, InputPlugin)
        assert issubclass(plugin_info.config_cls, InputPluginConfig)


# TODO: implement
# def test_loading_event_plugins():
#     raise NotImplementedError


# TODO: implement
# def test_loading_output_plugins():
#     raise NotImplementedError
