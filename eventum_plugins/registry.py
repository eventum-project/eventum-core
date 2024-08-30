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

    def register_plugin(
        self,
        type: PluginType,
        name: str,
        cls: type,
        config_cls: type
    ) -> None:
        """Register plugin in registry.

        Parameters
        ----------
        type : PluginType
            Type of the plugin

        name : str
            Plugin name

        cls : type
            Plugin class

        config_cls : type
            Class of config used to configure plugin
        """
        self._plugins[type][name] = PluginInfo(
            name=name,
            type=type,
            cls=cls,
            config_cls=config_cls
        )

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
