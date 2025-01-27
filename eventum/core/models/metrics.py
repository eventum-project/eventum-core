from typing import TypedDict

from eventum.plugins.event.base.metrics import EventPluginMetrics
from eventum.plugins.input.base.metrics import InputPluginMetrics
from eventum.plugins.output.base.metrics import OutputPluginMetrics


class PluginsMetrics(TypedDict):
    """Plugins metrics.

    Attributes
    ----------
    input : list[InputPluginMetrics]
        Input plugins metrics

    event : EventPluginMetrics
        Event plugin metrics

    output : list[OutputPluginMetrics]
        Output plugins metrics
    """
    input: list[InputPluginMetrics]
    event: EventPluginMetrics
    output: list[OutputPluginMetrics]


class CommonMetrics(TypedDict):
    """Common metrics.

    Attributes
    ----------
    started : str
        Start time of generator in ISO8601 format

    parameters : dict
        Model-dumped generator parameters
    """
    started: str
    parameters: dict


class Metrics(TypedDict):
    """Metrics of generator.

    Attributes
    ----------
    common: CommonMetrics
        Common metrics

    plugins: PluginsMetrics
        Plugins metrics
    """
    common: CommonMetrics
    plugins: PluginsMetrics
