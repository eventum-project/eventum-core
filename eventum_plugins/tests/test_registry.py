import pytest

from eventum_plugins.locators import InputPluginLocator
from eventum_plugins.registry import PluginInfo, PluginsRegistry


def test_registry():
    locator = InputPluginLocator()

    assert not PluginsRegistry.is_registered(locator, 'test')

    with pytest.raises(ValueError):
        PluginsRegistry.get_plugin_info(locator, 'test')

    PluginsRegistry.register_plugin(
        PluginInfo(
            name='test',
            cls=object,
            config_cls=object,
            locator=locator
        )
    )

    assert PluginsRegistry.is_registered(locator, 'test')

    plugin_info = PluginsRegistry.get_plugin_info(locator, 'test')

    assert plugin_info.name == 'test'
    assert plugin_info.locator == locator
    assert plugin_info.cls is object
    assert plugin_info.config_cls is object


def test_plugin_registration():
    locator = InputPluginLocator()

    assert not PluginsRegistry.is_registered(locator, 'cron')

    from eventum_plugins.input.plugins.cron.config import CronInputPluginConfig
    from eventum_plugins.input.plugins.cron.plugin import CronInputPlugin

    assert PluginsRegistry.is_registered(locator, 'cron')

    plugin_info = PluginsRegistry.get_plugin_info(locator, 'cron')

    assert plugin_info.name == 'cron'
    assert (
        plugin_info.locator.get_root_package().__name__
        == locator.get_root_package().__name__
    )
    assert plugin_info.cls is CronInputPlugin
    assert plugin_info.config_cls is CronInputPluginConfig
