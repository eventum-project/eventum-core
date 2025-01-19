from dataclasses import dataclass
from typing import Any, Iterable, Literal, assert_never, overload

from pydantic import ValidationError
from pytz import timezone

from eventum.core.models.config import PluginConfig, PluginConfigFields
from eventum.core.models.parameters.generator import GeneratorParameters
from eventum.plugins.event.base.plugin import EventPlugin, EventPluginParams
from eventum.plugins.exceptions import (PluginConfigurationError,
                                        PluginLoadError, PluginNotFoundError)
from eventum.plugins.input.base.plugin import InputPlugin, InputPluginParams
from eventum.plugins.loader import (load_event_plugin, load_input_plugin,
                                    load_output_plugin)
from eventum.plugins.output.base.plugin import OutputPlugin, OutputPluginParams
from eventum.utils.validation_prettier import prettify_validation_errors


class InitializationError(Exception):
    """Error during initialization."""

    def __init__(self, *args: object, context: dict[str, Any]) -> None:
        super().__init__(*args)

        self.context = context


@dataclass(frozen=True)
class InitializedPlugins:
    """Initialized plugins.

    Attributes
    ----------
    input : list[InputPlugin]
        List of initialized input plugins

    event : EventPlugin
        Initialized event plugin

    output : list[OutputPlugin]
        List of initialized output plugins
    """
    input: list[InputPlugin]
    event: EventPlugin
    output: list[OutputPlugin]


@overload
def init_plugin(
    name: str,
    type: Literal['input'],
    config: PluginConfigFields,
    params: InputPluginParams
) -> InputPlugin:
    ...


@overload
def init_plugin(
    name: str,
    type: Literal['event'],
    config: PluginConfigFields,
    params: EventPluginParams
) -> EventPlugin:
    ...


@overload
def init_plugin(
    name: str,
    type: Literal['output'],
    config: PluginConfigFields,
    params: OutputPluginParams
) -> OutputPlugin:
    ...


def init_plugin(
    name: str,
    type: Literal['input', 'event', 'output'],
    config: PluginConfigFields,
    params: InputPluginParams | EventPluginParams | OutputPluginParams
) -> InputPlugin | EventPlugin | OutputPlugin:
    """Initialize plugin.

    Parameters
    ----------
    name : str
        Name of plugin to use

    type : Literal['input', 'event', 'output']
        Type of plugin

    config : PluginConfigFields
        Config for plugin instance

    params : InputPluginParams | EventPluginParams | OutputPluginParams
        Parameters for plugin instance

    Returns
    -------
    InputPlugin | EventPlugin | OutputPlugin
        Initialized plugin

    Raises
    ------
    InitializationError
        If any error occurs during initializing
    """
    try:
        match type:
            case 'input':
                plugin_info = load_input_plugin(name=name)
            case 'event':
                plugin_info = load_event_plugin(name=name)
            case 'output':
                plugin_info = load_output_plugin(name=name)
            case t:
                assert_never(t)
    except PluginNotFoundError as e:
        raise InitializationError(
            'Plugin is not found',
            context=(e.context | dict(plugin_type=type))
        )
    except PluginLoadError as e:
        raise InitializationError(
            'Failed to load plugin',
            context=(e.context | dict(plugin_type=type))
        )

    PluginCls = plugin_info.cls
    ConfigCls = plugin_info.config_cls

    try:
        plugin_config = ConfigCls.model_validate(  # type: ignore[attr-defined]
            config
        )
    except ValidationError as e:
        raise InitializationError(
            'Invalid configuration for plugin',
            context=dict(
                plugin_name=name,
                plugin_type=type,
                plugin_id=params['id'],
                reason=prettify_validation_errors(e.errors())
            )
        )

    try:
        return PluginCls(config=plugin_config, params=params)
    except PluginConfigurationError as e:
        raise InitializationError(str(e), context=e.context)
    except Exception as e:
        raise InitializationError(
            'Unexpected error during plugin initialization',
            context=dict(
                plugin_name=name,
                plugin_type=type,
                plugin_id=params['id'],
                reason=str(e)
            )
        )


def init_plugins(
    input: Iterable[PluginConfig],
    event: PluginConfig,
    output: Iterable[PluginConfig],
    params: GeneratorParameters
) -> InitializedPlugins:
    """Initialize plugins.

    Parameters
    ----------
    input : Iterable[PluginConfig]
        Input plugin configurations

    event : PluginConfig
        Event plugin configuration

    output : Iterable[PluginConfig]
        Output plugin configurations

    params : GeneratorParameters
        Generators parameters that can be needed for plugins
        initialization (plugin params, e.g. timezone)

    Returns
    -------
    InitializedPlugins
        Initialized plugins

    Raises
    ------
    InitializationError
        If any error occurs during initializing
    """
    input_plugins: list[InputPlugin] = []
    for i, conf in enumerate(input):
        plugin_name, plugin_conf = next(iter(conf.items()))
        input_plugins.append(
            init_plugin(
                name=plugin_name,
                type='input',
                config=plugin_conf,
                params={'id': i, 'timezone': timezone(params.timezone)}
            )
        )

    plugin_name, plugin_conf = next(iter(event.items()))
    event_plugin = init_plugin(
        name=plugin_name,
        type='event',
        config=plugin_conf,
        params={'id': 1}
    )

    output_plugins: list[OutputPlugin] = []
    for i, conf in enumerate(output):
        plugin_name, plugin_conf = next(iter(conf.items()))
        output_plugins.append(
            init_plugin(
                name=plugin_name,
                type='output',
                config=plugin_conf,
                params={'id': i}
            )
        )

    return InitializedPlugins(
        input=input_plugins,
        event=event_plugin,
        output=output_plugins
    )
