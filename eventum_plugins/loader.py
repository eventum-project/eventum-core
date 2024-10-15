import importlib
from functools import cache
from types import ModuleType

import eventum_plugins.event.plugins as event_plugins
import eventum_plugins.input.plugins as input_plugins
import eventum_plugins.output.plugins as output_plugins
from eventum_plugins.exceptions import PluginLoadError, PluginNotFoundError
from eventum_plugins.registry import PluginInfo, PluginsRegistry
from eventum_plugins.utils.package_utils import get_subpackage_names


def _construct_plugin_module_name(package: ModuleType, name: str) -> str:
    """Construct absolute name of module with plugin class definition.

    Parameters
    ----------
    package : ModuleType
        Parent package with plugins of specific type

    name : str
        Name of the plugin

    Returns
    -------
    str
        Absolute name of module
    """
    return f'{package.__name__}.{name}.plugin'


def _invoke_plugin(package: ModuleType, name: str) -> None:
    """Invoke plugin to trigger registration.

    Parameters
    ----------
    package : ModuleType
        Parent package with plugins of specific type

    name : str
        Name of the plugin

    Raises
    ------
    PluginNotFoundError
        If specified plugin is not found

    PluginLoadError
        If specified plugin is found but cannot be imported
    """
    try:
        importlib.import_module(_construct_plugin_module_name(package, name))
    except ModuleNotFoundError:
        raise PluginNotFoundError('Plugin not found')
    except ImportError as e:
        raise PluginLoadError(f'Error during importing plugin module: {e}')


def _load_plugin(package: ModuleType, name: str) -> PluginInfo:
    """Load specified plugin by importing plugin module, that in turn
    triggers registration of plugin in the registry. If plugin is
    presented in the registry, then importing is skipped.

    Parameters
    ----------
    package : ModuleType
        Parent package with plugins of specific type

    name : str
        Name of the plugin

    Returns
    -------
    PluginInfo
        Information of loaded plugin

    Raises
    ------
    PluginNotFoundError
        If specified plugin is not found

    PluginLoadError
        If specified plugin is found but cannot be loaded
    """
    if not PluginsRegistry.is_registered(package, name):
        _invoke_plugin(package, name)

    try:
        return PluginsRegistry.get_plugin_info(package, name)
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
        If specified plugin is not found

    PluginLoadError
        If plugin is found but cannot be loaded
    """
    return _load_plugin(input_plugins, name)


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
        If specified plugin is not found

    PluginLoadError
        If plugin is found but cannot be loaded
    """
    return _load_plugin(event_plugins, name)


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
        If specified plugin is not found

    PluginLoadError
        If plugin is found but cannot be loaded
    """
    return _load_plugin(output_plugins, name)


def get_input_plugin_names() -> list[str]:
    """Get names list of existing input plugins.

    Returns
    -------
    list[str]
        Names of existing input plugins
    """
    return get_subpackage_names(input_plugins)


def get_event_plugin_names() -> list[str]:
    """Get names list of existing event plugins.

    Returns
    -------
    list[str]
        Names of existing event plugins
    """
    return get_subpackage_names(event_plugins)


def get_output_plugin_names() -> list[str]:
    """Get names list of existing output plugins.

    Returns
    -------
    list[str]
        Names of existing output plugins
    """
    return get_subpackage_names(output_plugins)
