import importlib

import pytest

import eventum.plugins.input.plugins as input_plugins
from eventum.plugins.registry import PluginInfo, PluginsRegistry


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


def test_registry_clearing():
    PluginsRegistry.register_plugin(
        PluginInfo(
            name='test',
            cls=object,
            config_cls=object,
            package=input_plugins
        )
    )

    assert PluginsRegistry.is_registered(input_plugins, 'test')

    PluginsRegistry.clear()

    assert not PluginsRegistry.is_registered(input_plugins, 'test')


def test_plugin_registration():
    PluginsRegistry.clear()

    assert not PluginsRegistry.is_registered(input_plugins, 'cron')

    import eventum.plugins.input.plugins.cron.config as config
    import eventum.plugins.input.plugins.cron.plugin as plugin
    importlib.reload(plugin)

    assert PluginsRegistry.is_registered(input_plugins, 'cron')

    plugin_info = PluginsRegistry.get_plugin_info(input_plugins, 'cron')

    assert plugin_info.name == 'cron'
    assert plugin_info.package == input_plugins
    assert plugin_info.cls is plugin.CronInputPlugin
    assert plugin_info.config_cls is config.CronInputPluginConfig
