import importlib

from eventum_plugins.exceptions import PluginLoadError, PluginNotFoundError
from eventum_plugins.registry import PluginInfo, PluginsRegistry, PluginType
from eventum_plugins.utils.modules import get_module_names

INPUT_PLUGINS_PACKAGE = 'eventum_plugins.input'
EVENT_PLUGINS_PACKAGE = 'eventum_plugins.event'
OUTPUT_PLUGINS_PACKAGE = 'eventum_plugins.output'


def _load_plugin(
    type: PluginType,
    name: str,
    registry: PluginsRegistry
) -> PluginInfo:
    """Load specified plugin by importing plugin module, that in
    turns triggers external logic for plugin registration in the
    provided `registry`. Return plugin's class in final. If plugin
    already loaded (it is present in `registry`), then its class
    returned immediately without import. If plugin cannot be found
    then `PluginNotFoundError` is raised, otherwise `PluginLoadError`
    is raised for any other error.
    """
    if not registry.is_registered(type, name):
        try:
            importlib.import_module(name=f'eventum_plugins.{type}.{name}')
        except ModuleNotFoundError:
            raise PluginNotFoundError('Plugin not found')
        except ImportError as e:
            raise PluginLoadError(f'Error during importing plugin module: {e}')

    try:
        return registry.get_plugin_info(type, name)
    except ValueError:
        raise PluginLoadError(
            'Plugin was imported but was not found in registry'
        )


def load_input_plugin(name: str) -> PluginInfo:
    """Load specified input plugin and return its type."""
    return _load_plugin(PluginType.INPUT, name, PluginsRegistry())


def load_event_plugin(name: str) -> PluginInfo:
    """Load specified event plugin and return its type."""
    return _load_plugin(PluginType.EVENT, name, PluginsRegistry())


def load_output_plugin(name: str) -> PluginInfo:
    """Load specified output plugin and return its type."""
    return _load_plugin(PluginType.OUTPUT, name, PluginsRegistry())


def get_input_plugin_names() -> list[str]:
    """Get names list of existing input plugins."""
    names = get_module_names(INPUT_PLUGINS_PACKAGE)
    return [name for name in names if not name.startswith('_')]


def get_event_plugin_names() -> list[str]:
    """Get names list of existing event plugins."""
    names = get_module_names(EVENT_PLUGINS_PACKAGE)
    return [name for name in names if not name.startswith('_')]


def get_output_plugin_names() -> list[str]:
    """Get names list of existing output plugins."""
    names = get_module_names(OUTPUT_PLUGINS_PACKAGE)
    return [name for name in names if not name.startswith('_')]
