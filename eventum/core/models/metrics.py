from typing import TypeAlias, TypedDict


class PluginMetrics(TypedDict):
    """Plugin metrics.

    Attributes
    ----------
    name : str
        Name of the plugin

    id : int
        ID of the plugin

    configuration : dict
        Model-dumped plugin configuration
    """
    name: str
    id: int
    configuration: dict


class InputPluginMetrics(PluginMetrics):
    """Input plugin metrics.

    Attributes
    ----------
    created : int
        Number of created events
    """
    created: int


class EventPluginMetrics(PluginMetrics):
    """Event plugin metrics.

    Attributes
    ----------
    produced : int
        Number of produced events

    produce_failed : int
        Number unsuccessfully produced events
    """
    produced: int
    produce_failed: int


class JinjaEventPluginStateMetrics(TypedDict):
    """Jinja event plugin state metrics.

    Attributes
    ----------
    locals : dict[str, dict]
        Local states

    shared : dict
        Shared state

    globals : dict
        Global state
    """
    locals: dict[str, dict]
    shared: dict
    globals: dict


class JinjaEventPluginMetrics(EventPluginMetrics):
    """Jinja event plugin metrics.

    Attributes
    ----------
    state : JinjaEventPluginStateMetrics
        Jinja event plugin state metrics
    """
    state: JinjaEventPluginStateMetrics


class OutputPluginMetrics(PluginMetrics):
    """Output plugin metrics.

    Attributes
    ----------
    format_failed : int
        Number of unsuccessfully formatted events

    write_failed : int
        Number of unsuccessfully written events

    written : int
        Number of written events
    """
    format_failed: int
    write_failed: int
    written: int


class InputMetrics(TypedDict):
    """Input metrics.

    Attributes
    ----------
    plugins : list[InputPluginMetrics]
        List of input plugin metrics
    """
    plugins: list[InputPluginMetrics]


EventPluginMetricsT: TypeAlias = (
    EventPluginMetrics | JinjaEventPluginMetrics
)


class EventMetrics(TypedDict):
    """Event metrics.

    Attributes
    ----------
    plugin : EventPluginMetricsT
        Event plugin metrics
    """
    plugin: EventPluginMetricsT


class OutputMetrics(TypedDict):
    """Output metrics.

    Attributes
    ----------
    plugins : list[OutputPluginMetrics]
        List of output plugin metrics
    """
    plugins: list[OutputPluginMetrics]


class Metrics(TypedDict):
    """Metrics of generator.

    Attributes
    ----------
    started : str
        Start time of generator in ISO8601 format

    parameters : dict
        Model-dumped generator parameters

    input : InputMetrics
        Input metrics

    event : EventMetrics
        Event metrics

    output : OutputMetrics
        Output metrics
    """
    started: str
    parameters: dict
    input: InputMetrics
    event: EventMetrics
    output: OutputMetrics
