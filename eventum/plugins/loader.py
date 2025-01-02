import importlib
import pkgutil
from functools import cache
from types import ModuleType

import eventum.plugins.event.plugins as event_plugins
import eventum.plugins.input.plugins as input_plugins
import eventum.plugins.output.plugins as output_plugins
from eventum.plugins.exceptions import PluginLoadError, PluginNotFoundError
from eventum.plugins.registry import PluginInfo, PluginsRegistry


def _get_subpackage_names(package: ModuleType) -> list[str]:
    """Get subpackage names of specified package.

    Parameters
    ----------
    package : ModuleType
        Package to inspect

    Returns
    -------
    list[str]
        List of subpackage names

    Raises
    ------
    ValueError
        If specified package is not a package
    """
    if not hasattr(package, '__path__'):
        raise ValueError(f'"{package.__name__}" is not a package') from None

    return [
        module.name
        for module in pkgutil.iter_modules(package.__path__)
        if module.ispkg
    ]


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
        raise PluginNotFoundError(
            'Plugin not found',
            context=dict(plugin_name=name)
        )
    except ImportError as e:
        raise PluginLoadError(
            'Error during importing plugin module',
            context=dict(reason=str(e), plugin_name=name)
        )


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
            'Plugin was imported but was not found in registry',
            context=dict(plugin_name=name)
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
    return _get_subpackage_names(input_plugins)


def get_event_plugin_names() -> list[str]:
    """Get names list of existing event plugins.

    Returns
    -------
    list[str]
        Names of existing event plugins
    """
    return _get_subpackage_names(event_plugins)


def get_output_plugin_names() -> list[str]:
    """Get names list of existing output plugins.

    Returns
    -------
    list[str]
        Names of existing output plugins
    """
    return _get_subpackage_names(output_plugins)
