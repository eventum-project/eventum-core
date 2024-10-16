
import importlib
import inspect
from abc import ABC

from eventum_plugins.exceptions import PluginRegistrationError
from eventum_plugins.registry import PluginInfo, PluginsRegistry


class Plugin(ABC):
    """Base class for all plugins.

    Notes
    -----
    All subclasses of this class is considered as implemented plugins
    if inheritance parameter `register` is set to `True`. Implemented
    plugins are automatically registered in `PluginsRegistry`.

    Other Parameters
    ----------------
    config_cls : type
        Model class of config used by plugin

    register : bool, default=True
        Whether to register class as implemented plugin
    """

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

        PluginsRegistry.register_plugin(
            PluginInfo(
                name=plugin_name,
                cls=cls,
                config_cls=config_cls,
                package=package
            )
        )
