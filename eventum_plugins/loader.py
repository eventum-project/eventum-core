import importlib
from functools import cache

from eventum_plugins.exceptions import PluginLoadError, PluginNotFoundError
from eventum_plugins.registry import PluginInfo, PluginsRegistry, PluginType
from eventum_plugins.utils.package_utils import get_subpackage_names

INPUT_PLUGINS_PACKAGE = 'eventum_plugins.input.plugins'
EVENT_PLUGINS_PACKAGE = 'eventum_plugins.event.plugins'
OUTPUT_PLUGINS_PACKAGE = 'eventum_plugins.output.plugins'


def _load_plugin(
    type: PluginType,
    name: str,
    registry: PluginsRegistry
) -> PluginInfo:
    """Load specified plugin by importing plugin module, that in
    turns triggers external logic for plugin registration in the
    provided `registry`. If plugin already loaded (it is presented
    in `registry`), then importing part is skipped.

    Parameters
    ----------
    type : PluginType
        Type of the plugin

    name : str
        Name of the plugin

    registry : PluginsRegistry
        Registry that handles plugins registration and stores
        required information

    Returns
    -------
    PluginInfo
        Information of loaded plugin

    Raises
    ------
    PluginNotFoundError
        If plugin cannot be found

    PluginLoadError
        If plugin is found but cannot be loaded
    """
    if not registry.is_registered(type, name):
        try:
            importlib.import_module(
                name=f'eventum_plugins.{type}.plugins.{name}.plugin'
            )
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


@cache
def load_input_plugin(name: str) -> PluginInfo:
    """Load specified input plugin and return information about it.

    Parameters
    ----------
    name : str
        Name of the plugin

    Returns
    -------
    PluginInfo
        Information about plugin

    Raises
    ------
    PluginNotFoundError
        If plugin cannot be found

    PluginLoadError
        If plugin is found but cannot be loaded
    """
    return _load_plugin(PluginType.INPUT, name, PluginsRegistry())


@cache
def load_event_plugin(name: str) -> PluginInfo:
    """Load specified event plugin and return information about it.

    Parameters
    ----------
    name : str
        Name of the plugin

    Returns
    -------
    PluginInfo
        Information about plugin

    Raises
    ------
    PluginNotFoundError
        If plugin cannot be found

    PluginLoadError
        If plugin is found but cannot be loaded
    """
    return _load_plugin(PluginType.EVENT, name, PluginsRegistry())


@cache
def load_output_plugin(name: str) -> PluginInfo:
    """Load specified output plugin and return information about it.

    Parameters
    ----------
    name : str
        Name of the plugin

    Returns
    -------
    PluginInfo
        Information about plugin

    Raises
    ------
    PluginNotFoundError
        If plugin cannot be found

    PluginLoadError
        If plugin is found but cannot be loaded
    """
    return _load_plugin(PluginType.OUTPUT, name, PluginsRegistry())


@cache
def get_input_plugin_names() -> list[str]:
    """Get names list of existing input plugins.

    Returns
    -------
    list[str]
        Names of existing input plugins
    """
    return get_subpackage_names(INPUT_PLUGINS_PACKAGE)


@cache
def get_event_plugin_names() -> list[str]:
    """Get names list of existing event plugins.

    Returns
    -------
    list[str]
        Names of existing event plugins
    """
    return get_subpackage_names(EVENT_PLUGINS_PACKAGE)


@cache
def get_output_plugin_names() -> list[str]:
    """Get names list of existing output plugins.

    Returns
    -------
    list[str]
        Names of existing output plugins
    """
    return get_subpackage_names(OUTPUT_PLUGINS_PACKAGE)
