
from typing import TypedDict

from eventum.core.models.metrics import EventPluginMetrics


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
