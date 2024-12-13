import importlib
import inspect
from abc import ABC
from contextlib import contextmanager
from types import ModuleType
from typing import Any, Generic, Required, TypedDict, TypeVar, get_args

import structlog
from pydantic import RootModel

from eventum_plugins.base.config import PluginConfig
from eventum_plugins.exceptions import (PluginConfigurationError,
                                        PluginRegistrationError)
from eventum_plugins.registry import PluginInfo, PluginsRegistry

logger = structlog.stdlib.get_logger()


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
        plugin_type_package_name = '.'.join(module_parts[:-2])
    except IndexError:
        raise TypeError(
            'Cannot extract information from module named '
            f'"{class_module.__name__}"'
        ) from None

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
        with required_params():
            self._id = params['id']

        self._config = config

        self._logger = self._get_logger_with_context()

    def _get_logger_with_context(self) -> structlog.stdlib.BoundLogger:
        """Get logger with plugin instance context.

        Returns
        -------
        structlog.stdlib.BoundLogger
            Logger with context
        """
        return logger.bind(
            plugin_type=self.plugin_type,
            plugin_name=self.plugin_name,
            plugin_id=self.id
        )

    def __str__(self) -> str:
        return (
            f'<{self.plugin_name} {self.plugin_type} plugin [{self._id}]>'
        )

    def __init_subclass__(cls, register: bool = True, **kwargs: Any):
        super().__init_subclass__(**kwargs)

        log = logger.bind(plugin_class=cls.__name__)

        if not register:
            setattr(cls, '_plugin_name', '[unregistered]')
            setattr(cls, '_plugin_type', '[unregistered]')
            return

        log.info('Registering plugin')

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
            ) from None
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

        log.info(
            'Plugin successfully registered',
            plugin_type=registration_info['type'],
            plugin_name=registration_info['name'],
            plugin_config_class=config_cls.__name__,
        )

    @property
    def id(self) -> int:
        """ID of the plugin."""
        return self._id

    @property
    def plugin_name(self) -> str:
        """Canonical name of the plugin."""
        return getattr(self, '_plugin_name')

    def set_ephemeral_name(self, name: str) -> None:
        """Set ephemeral name for plugin.

        Parameters
        ----------
        name : str
            Name to set

        Notes
        -----
        This method can be helpful when plugin is not registered
        but it needs representable name for some reason
        """
        self._plugin_name = name

        # we should rebind logger since context is changed
        self._logger = self._get_logger_with_context()

    @property
    def plugin_type(self) -> str:
        """Type of the plugin."""
        return getattr(self, '_plugin_type')

    def set_ephemeral_type(self, type: str) -> None:
        """Set ephemeral type for plugin.

        Parameters
        ----------
        type : str
            Type to set

        Notes
        -----
        This method can be helpful when plugin is not registered
        but it needs representable type for some reason
        """
        self._plugin_type = type

        # we should rebind logger since context is changed
        self._logger = self._get_logger_with_context()
