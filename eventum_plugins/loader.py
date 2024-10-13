import importlib
from functools import cache

from eventum_plugins.exceptions import PluginLoadError, PluginNotFoundError
from eventum_plugins.locators import (EventPluginLocator, InputPluginLocator,
                                      OutputPluginLocator, PluginLocator)
from eventum_plugins.registry import PluginInfo, PluginsRegistry
from eventum_plugins.utils.package_utils import get_subpackage_names

input_plugin_locator = InputPluginLocator()
event_plugin_locator = EventPluginLocator()
output_plugin_locator = OutputPluginLocator()


def _construct_plugin_module_name(locator: PluginLocator, name: str) -> str:
    """Construct absolute name of module with plugin class definition.

    Parameters
    ----------
    locator : PluginLocator
        Locator of the plugin

    name : str
        Name of the plugin

    Returns
    -------
    str
        Absolute name of module
    """
    return f'{locator.get_root_package().__name__}.{name}.plugin'


def _trigger_plugin_registration(locator: PluginLocator, name: str) -> None:
    """Trigger plugin registration by importing it.

    Parameters
    ----------
    locator : PluginLocator
        Locator of the plugin

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
        importlib.import_module(_construct_plugin_module_name(locator, name))
    except ModuleNotFoundError:
        raise PluginNotFoundError('Plugin not found')
    except ImportError as e:
        raise PluginLoadError(f'Error during importing plugin module: {e}')


def _load_plugin(
    locator: PluginLocator,
    name: str,
    registry: PluginsRegistry
) -> PluginInfo:
    """Load specified plugin by importing plugin module, that in
    turn must trigger registration of plugin in the provided registry.
    If plugin is already loaded (it is presented in registry), then
    importing is skipped.

    Parameters
    ----------
    locator : PluginLocator
        Locator of the plugin

    name : str
        Name of the plugin

    registry : PluginsRegistry
        Registry that handles plugin registration and stores
        required information

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
    if not registry.is_registered(locator, name):
        _trigger_plugin_registration(locator, name)

    try:
        return registry.get_plugin_info(locator, name)
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
    return _load_plugin(input_plugin_locator, name, PluginsRegistry())


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
    return _load_plugin(event_plugin_locator, name, PluginsRegistry())


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
    return _load_plugin(output_plugin_locator, name, PluginsRegistry())


def get_input_plugin_names() -> list[str]:
    """Get names list of existing input plugins.

    Returns
    -------
    list[str]
        Names of existing input plugins
    """
    return get_subpackage_names(input_plugin_locator.get_root_package())


def get_event_plugin_names() -> list[str]:
    """Get names list of existing event plugins.

    Returns
    -------
    list[str]
        Names of existing event plugins
    """
    return get_subpackage_names(event_plugin_locator.get_root_package())


def get_output_plugin_names() -> list[str]:
    """Get names list of existing output plugins.

    Returns
    -------
    list[str]
        Names of existing output plugins
    """
    return get_subpackage_names(output_plugin_locator.get_root_package())
