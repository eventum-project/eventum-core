
import importlib
import inspect
from abc import ABC
from contextlib import contextmanager
from types import ModuleType
from typing import Any, Generic, Required, TypedDict, TypeVar, get_args

from pydantic import RootModel

from eventum_plugins.base.config import PluginConfig
from eventum_plugins.exceptions import (PluginConfigurationError,
                                        PluginRegistrationError)
from eventum_plugins.registry import PluginInfo, PluginsRegistry


class _PluginRegistrationInfo(TypedDict):
    """Information of plugin for registration.

    Attributes
    ----------
    name : str
        Name of the plugin

    type : str
        Plugin type (i.e. parent package name)

    package : ModuleType
        Parent package containing plugin package
    """
    name: str
    type: str
    package: ModuleType


def _inspect_plugin(plugin_cls: type) -> _PluginRegistrationInfo:
    """Inspect plugin to get registration info.

    Parameters
    ----------
    plugin_cls : type
        Class of the plugin to inspect

    Returns
    -------
    _PluginRegistrationInfo
        Information for plugin registration

    Raises
    ------
    TypeError
        If provided class cannot be inspected
    """
    class_module = inspect.getmodule(plugin_cls)
    if class_module is None:
        raise TypeError('Cannot get module of plugin class definition')

    if class_module.__name__ == '__main__':
        raise TypeError('Plugin can be used only as external module')

    try:
        # expected structure for extraction:
        # eventum_plugins.<plugin_type>.plugins.<plugin_name>.plugin
        module_parts = class_module.__name__.split('.')
        plugin_name = module_parts[-2]
        plugin_type = module_parts[-4]
        plugin_type_package_name = '.'.join(module_parts[:-3])
    except IndexError:
        raise TypeError(
            'Cannot resolve plugin module name or plugin parent package '
            f'name for module named "{class_module.__name__}"'
        )

    try:
        package = importlib.import_module(plugin_type_package_name)
    except ImportError as e:
        raise TypeError(
            'Cannot import parent package of plugin '
            f'for module named "{class_module.__name__}": {e}'
        )

    return _PluginRegistrationInfo(
        name=plugin_name,
        type=plugin_type,
        package=package
    )


class PluginParams(TypedDict):
    """Parameters for plugin.

    Attributes
    ----------
    id : int
        Numeric plugin identifier
    """
    id: Required[int]


@contextmanager
def required_params():
    """Context manager for handling missing keys in plugin parameters.

    Raises
    ------
    PluginConfigurationError
        If `KeyError` is raised
    """
    try:
        yield
    except KeyError as e:
        raise PluginConfigurationError(
            f'Missing required parameter: {e}'
        ) from None


config_T = TypeVar('config_T', bound=(PluginConfig | RootModel))
params_T = TypeVar('params_T', bound=PluginParams)


class Plugin(ABC, Generic[config_T, params_T]):
    """Base class for all plugins.

    Parameters
    ----------
    config : config_T
        Configuration for the plugin

    params : params_T
        Parameters for plugin (see `PluginParams`)

    Other Parameters
    ----------------
    register : bool, default=True
        Whether to register class as complete plugin

    Notes
    -----
    All subclasses of this class is considered as complete plugins
    if inheritance parameter `register` is set to `True`. Complete
    plugins are automatically registered in `PluginsRegistry`.
    """

    def __init__(self, config: config_T, params: params_T) -> None:
        self._config = config

        with required_params():
            self._id = params['id']

    def __str__(self) -> str:
        return (
            f'<{self.plugin_name} {self.plugin_type} plugin [{self.id}]>'
        )

    def __init_subclass__(cls, register: bool = True, **kwargs: Any):
        super().__init_subclass__(**kwargs)

        if not register:
            return

        try:
            registration_info = _inspect_plugin(cls)
        except TypeError as e:
            raise PluginRegistrationError(f'Unable to inspect plugin: {e}')

        setattr(cls, '_plugin_name', registration_info['name'])
        setattr(cls, '_plugin_type', registration_info['type'])

        try:
            (config_cls, *_) = get_args(
                cls.__orig_bases__[0]   # type: ignore[attr-defined]
            )
        except ValueError:
            raise PluginRegistrationError(
                'Generic parameters must be specified'
            )
        except Exception as e:
            raise PluginRegistrationError(
                f'Unable to define config class: {e}'
            )

        if isinstance(config_cls, TypeVar):
            raise PluginRegistrationError(
                'Config class cannot have generic type'
            )

        PluginsRegistry.register_plugin(
            PluginInfo(
                name=registration_info['name'],
                cls=cls,
                config_cls=config_cls,
                package=registration_info['package']
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

    @property
    def plugin_type(self) -> str:
        """Type of the plugin."""
        return self._plugin_type    # type: ignore[attr-defined]
