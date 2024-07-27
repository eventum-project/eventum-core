from eventum_plugins.registry import PluginsRegistry
from eventum_plugins.enums import PluginType
import pytest


def test_registry():
    reg = PluginsRegistry()

    assert not reg.is_registered(PluginType.INPUT, 'test')

    with pytest.raises(ValueError):
        reg.get_plugin_info(PluginType.INPUT, 'test')

    reg.register_plugin(PluginType.INPUT, 'test', object, object)

    assert reg.is_registered(PluginType.INPUT, 'test')

    plugin_info = reg.get_plugin_info(PluginType.INPUT, 'test')

    assert plugin_info.name == 'test'
    assert plugin_info.type == PluginType.INPUT
    assert plugin_info.cls is object
    assert plugin_info.config_cls is object


def test_plugin_registration():
    reg = PluginsRegistry()

    assert not reg.is_registered(PluginType.INPUT, 'cron')

    from eventum_plugins.input.cron import (CronInputPlugin,
                                            CronInputPluginConfig)

    assert reg.is_registered(PluginType.INPUT, 'cron')

    plugin_info = reg.get_plugin_info(PluginType.INPUT, 'cron')

    assert plugin_info.name == 'cron'
    assert plugin_info.type == PluginType.INPUT
    assert plugin_info.cls is CronInputPlugin
    assert plugin_info.config_cls is CronInputPluginConfig
