from dataclasses import dataclass

from eventum_plugins.locators import PluginLocator


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


class PluginsRegistry:
    """Centralized registry of plugins. All plugins should be
    registered using this class to be visible and accessible via
    loader.
    """

    _registry: dict[str, dict[str, PluginInfo]] = dict()

    @classmethod
    def register_plugin(cls, plugin_info: PluginInfo) -> None:
        """Register plugin in registry.

        Parameters
        ----------
        plugin_info : PluginInfo
            Information about plugin
        """
        location = plugin_info.locator.get_root_package().__name__

        if location not in cls._registry:
            cls._registry[location] = dict()

        cls._registry[location][plugin_info.name] = plugin_info

    @classmethod
    def get_plugin_info(cls, locator: PluginLocator, name: str) -> PluginInfo:
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
            return cls._registry[plugin_location][name]
        except KeyError:
            raise ValueError('Plugin is not registered')

    @classmethod
    def is_registered(cls, locator: PluginLocator, name: str) -> bool:
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
        return location in cls._registry and name in cls._registry[location]
