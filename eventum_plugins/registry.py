from dataclasses import dataclass

from eventum_plugins.enums import PluginType
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

    type : PluginType
        Type of the plugin
    """
    name: str
    cls: type
    config_cls: type
    type: PluginType


class PluginsRegistry(metaclass=Singleton):
    """Centralized registry of plugins. Plugins should be registered
    using this class via singleton object.
    """

    def __init__(self) -> None:
        self._plugins: dict[PluginType, dict[str, PluginInfo]] = {
            type: dict()
            for type in PluginType
        }

    def register_plugin(self, plugin_info: PluginInfo) -> None:
        """Register plugin in registry.

        Parameters
        ----------
        plugin_info : PluginInfo
            Information about plugin
        """
        self._plugins[plugin_info.type][plugin_info.name] = plugin_info

    def get_plugin_info(self, type: PluginType, name: str) -> PluginInfo:
        """Get information about plugin from registry.

        Parameters
        ----------
        type : PluginType
            Type of the plugin

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
        try:
            return self._plugins[type][name]
        except KeyError:
            raise ValueError('Plugin is not registered')

    def is_registered(self, type: PluginType, name: str) -> bool:
        """Check whether specified plugin is registered.

        Parameters
        ----------
        type : PluginType
            Type of the plugin

        name : str
            Plugin name

        Returns
        -------
        bool
            `True` if plugin is registered else `False`
        """
        return name in self._plugins[type]
