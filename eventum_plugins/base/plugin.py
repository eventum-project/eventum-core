
import inspect
from abc import ABC

from eventum_plugins.enums import PluginType
from eventum_plugins.exceptions import PluginError
from eventum_plugins.registry import PluginsRegistry


class Plugin(ABC):
    """Base class for all plugins.

    Notes
    -----
    All subclasses of this class is considered as implemented plugins
    if inheritance parameter `base` is set to `False` and `register` is
    set to `True`. Implemented plugins are automatically registered in
    `PluginsRegistry` via `__init_subclass__`.

    Other Parameters
    ----------------
    Parameters that can be used in inheritance:

    config_cls : type
        Model class of config used by plugin

    register : bool, default=True
        Whether to register class as implemented plugin (actual only if
        `base` is set to `False`)

    base : bool, default=False
        Whether to dismiss subclass initialization for intermediate
        class that is used as base class representing category of
        plugins
    """

    def __init_subclass__(
        cls,
        config_cls: type,
        register: bool = True,
        base: bool = False,
        **kwargs
    ):
        super().__init_subclass__(**kwargs)

        if base:
            return

        class_module = inspect.getmodule(cls)
        if class_module is None:
            raise PluginError(
                'Cannot inspect module of plugin class definition'
            )

        if class_module.__name__ == '__main__':
            raise PluginError(
                'Plugin can be imported only from external module'
            )

        try:
            # expected structure:
            # eventum_plugins.<plugins_type>.plugins.<plugins_name>.plugin
            module_parts = class_module.__name__.split('.')
            plugin_name = module_parts[-2]
            plugin_type_name = module_parts[-4]
            plugin_type = PluginType(plugin_type_name)
        except IndexError:
            raise PluginError(
                f'Cannot extract plugin name from "{class_module.__name__}"'
            )
        except ValueError:
            raise PluginError(
                f'Cannot extract plugin type from "{class_module.__name__}"'
            )

        cls.name = property(
            lambda _: plugin_name,
            doc="Name of plugin"
        )
        cls.config_cls = property(
            lambda _: config_cls,
            doc="Class of plugin config"
        )

        if register:
            PluginsRegistry().register_plugin(
                type=plugin_type,
                name=plugin_name,
                cls=cls,
                config_cls=config_cls
            )
