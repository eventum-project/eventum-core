import pytest

import eventum_plugins.input.plugins as input_plugins
from eventum_plugins.registry import PluginInfo, PluginsRegistry


def test_registry():
    assert not PluginsRegistry.is_registered(input_plugins, 'test')

    with pytest.raises(ValueError):
        PluginsRegistry.get_plugin_info(input_plugins, 'test')

    PluginsRegistry.register_plugin(
        PluginInfo(
            name='test',
            cls=object,
            config_cls=object,
            package=input_plugins
        )
    )

    assert PluginsRegistry.is_registered(input_plugins, 'test')

    plugin_info = PluginsRegistry.get_plugin_info(input_plugins, 'test')

    assert plugin_info.name == 'test'
    assert plugin_info.package == input_plugins
    assert plugin_info.cls is object
    assert plugin_info.config_cls is object


def test_plugin_registration():
    assert not PluginsRegistry.is_registered(input_plugins, 'cron')

    from eventum_plugins.input.plugins.cron.config import CronInputPluginConfig
    from eventum_plugins.input.plugins.cron.plugin import CronInputPlugin

    assert PluginsRegistry.is_registered(input_plugins, 'cron')

    plugin_info = PluginsRegistry.get_plugin_info(input_plugins, 'cron')

    assert plugin_info.name == 'cron'
    assert plugin_info.package == input_plugins
    assert plugin_info.cls is CronInputPlugin
    assert plugin_info.config_cls is CronInputPluginConfig
