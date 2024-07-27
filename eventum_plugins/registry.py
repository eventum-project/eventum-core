from dataclasses import dataclass
from eventum_plugins.enums import PluginType
from eventum_plugins.metaclasses import Singleton


@dataclass(frozen=True)
class PluginInfo:
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
            type.value: dict()
            for type in PluginType
        }

    def register_plugin(
        self,
        type: PluginType,
        name: str,
        cls: type,
        config_cls: type
    ) -> None:
        """Register plugin in registry."""
        self._plugins[type][name] = PluginInfo(
            name=name,
            type=type,
            cls=cls,
            config_cls=config_cls
        )

    def get_plugin_info(self, type: PluginType, name: str) -> PluginInfo:
        """Get plugin info from registry. Raise `ValueError` if
        specified plugin is not registered.
        """
        try:
            return self._plugins[type][name]
        except KeyError:
            raise ValueError('Plugin is not registered')

    def is_registered(self, type: PluginType, name: str) -> bool:
        """Check whether specified plugin is registered."""
        return name in self._plugins[type]
