from typing import Annotated, Any, TypeAlias

from pydantic import BaseModel, Field, field_validator

from eventum.plugins.loader import (get_event_plugin_names,
                                    get_input_plugin_names,
                                    get_output_plugin_names)

INPUT_PLUGIN_NAMES = set(get_input_plugin_names())
EVENT_PLUGIN_NAMES = set(get_event_plugin_names())
OUTPUT_PLUGIN_NAMES = set(get_output_plugin_names())

PluginConfigFields: TypeAlias = dict[str, Any]

PluginConfig: TypeAlias = Annotated[
    dict[str, PluginConfigFields],
    Field(min_length=1, max_length=1)
]


class GeneratorConfig(BaseModel, frozen=True, extra='forbid'):
    """Configuration of generator.

    Attributes
    ----------
    input : list[PluginConfig]
        List of input plugin configurations

    event : PluginConfig
        Event plugin configuration

    output : list[PluginConfig]
        List of output plugin configurations
    """
    input: list[PluginConfig] = Field(min_length=1)
    event: PluginConfig
    output: list[PluginConfig] = Field(min_length=1)

    @field_validator('input')
    def validate_input_plugin_names(
        cls,
        v: list[PluginConfig]
    ) -> list[PluginConfig]:
        for plugin_config in v:
            for key in plugin_config.keys():
                if key not in INPUT_PLUGIN_NAMES:
                    raise ValueError(f'Unknown input plugin "{key}"')

        return v

    @field_validator('event')
    def validate_event_plugin_names(
        cls,
        v: PluginConfig
    ) -> PluginConfig:
        for key in v.keys():
            if key not in EVENT_PLUGIN_NAMES:
                raise ValueError(f'Unknown event plugin "{key}"')

        return v

    @field_validator('output')
    def validate_output_plugin_names(
        cls,
        v: list[PluginConfig]
    ) -> list[PluginConfig]:

        for plugin_config in v:
            for key in plugin_config.keys():
                if key not in OUTPUT_PLUGIN_NAMES:
                    raise ValueError(f'Unknown output plugin "{key}"')

        return v
