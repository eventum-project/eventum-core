from typing import TypedDict


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
