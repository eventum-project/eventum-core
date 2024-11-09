
import importlib
import inspect
from abc import ABC
from typing import Any, Required, TypedDict, Unpack

from eventum_plugins.exceptions import PluginRegistrationError
from eventum_plugins.registry import PluginInfo, PluginsRegistry


class PluginKwargs(TypedDict):
    """Arguments for plugin configuration.

    Attributes
    ----------
    config : Any
        Configuration for the plugin

    id : int
        Numeric plugin identifier
    """
    config: Any
    id: Required[int]


class Plugin(ABC):
    """Base class for all plugins.

    Parameters
    ----------
    **kwargs : Unpack[PluginKwargs]
        Arguments for plugin configuration (see `PluginKwargs`)

    Other Parameters
    ----------------
    config_cls : type
        Model class of config used by plugin

    register : bool, default=True
        Whether to register class as implemented plugin

    Notes
    -----
    All subclasses of this class is considered as implemented plugins
    if inheritance parameter `register` is set to `True`. Implemented
    plugins are automatically registered in `PluginsRegistry`.
    """

    def __init__(self, **kwargs: Unpack[PluginKwargs]) -> None:
        self._config = kwargs['config']
        self._id = kwargs['id']

    def __str__(self) -> str:
        # plugin_name attribute is set during class initialization
        return (
            f'{self._plugin_name}-{self._id}'   # type: ignore[attr-defined]
        )

    def __init_subclass__(
        cls,
        config_cls: type,
        register: bool = True,
        **kwargs
    ):
        super().__init_subclass__(**kwargs)

        if not register:
            return

        class_module = inspect.getmodule(cls)
        if class_module is None:
            raise PluginRegistrationError(
                'Cannot inspect module of plugin class definition'
            )

        if class_module.__name__ == '__main__':
            raise PluginRegistrationError(
                'Plugin can be imported only from external module'
            )

        try:
            # expected structure for plugin name:
            # eventum_plugins.<plugin_type>.plugins.<plugin_name>.plugin
            module_parts = class_module.__name__.split('.')
            plugin_name = module_parts[-2]
            plugin_type_package_name = '.'.join(module_parts[:-2])
        except IndexError:
            raise PluginRegistrationError(
                'Cannot resolve plugin module name or plugin parent package '
                f'name for module named "{class_module.__name__}"'
            )

        try:
            package = importlib.import_module(plugin_type_package_name)
        except ImportError as e:
            raise PluginRegistrationError(
                'Cannot import parent package of plugin '
                f'for module named "{class_module.__name__}": {e}'
            )

        setattr(cls, '_plugin_name', plugin_name)

        PluginsRegistry.register_plugin(
            PluginInfo(
                name=plugin_name,
                cls=cls,
                config_cls=config_cls,
                package=package
            )
        )

    @property
    def id(self) -> int:
        """ID of the plugin."""
        return self._id

    @property
    def plugin_name(self) -> str:
        """Canonical name of the plugin."""
        return self._plugin_name    # type: ignore[attr-defined]
