from dataclasses import dataclass

from eventum_plugins.locators import PluginLocator
from eventum_plugins.utils.metaclasses import Singleton


@dataclass(frozen=True)
class PluginInfo:
    """Plugin information for a registration.

    Attributes
    ----------
    name : str
        Plugin name

    cls : type
        Plugin class

    config_cls : type
        Class of config used to configure plugin

    locator : PluginLocator
        Locator of the plugin
    """
    name: str
    cls: type
    config_cls: type
    locator: PluginLocator


class PluginsRegistry(metaclass=Singleton):
    """Centralized registry of plugins. Plugins should be registered
    using this class via singleton object.
    """

    def __init__(self) -> None:
        self._registry: dict[str, dict[str, PluginInfo]] = dict()

    def register_plugin(self, plugin_info: PluginInfo) -> None:
        """Register plugin in registry.

        Parameters
        ----------
        plugin_info : PluginInfo
            Information about plugin
        """
        location = plugin_info.locator.get_root_package().__name__

        if location not in self._registry:
            self._registry[location] = dict()

        self._registry[location][plugin_info.name] = plugin_info

    def get_plugin_info(self, locator: PluginLocator, name: str) -> PluginInfo:
        """Get information about plugin from registry.

        Parameters
        ----------
        locator : PluginLocator
            Locator of the plugin

        name : str
            Plugin name

        Returns
        -------
        PluginInfo
            Information about plugin

        Raises
        ------
        ValueError
            If specified plugin is not found in registry
        """
        plugin_location = locator.get_root_package().__name__
        try:
            return self._registry[plugin_location][name]
        except KeyError:
            raise ValueError('Plugin is not registered')

    def is_registered(self, locator: PluginLocator, name: str) -> bool:
        """Check whether specified plugin is registered.

        Parameters
        ----------
        locator : PluginLocator
            Locator of the plugin

        name : str
            Plugin name

        Returns
        -------
        bool
            `True` if plugin is registered else `False`
        """
        location = locator.get_root_package().__name__
        return location in self._registry and name in self._registry[location]
