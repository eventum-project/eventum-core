from eventum.plugins.base.metrics import PluginMetrics


class InputPluginMetrics(PluginMetrics):
    """Input plugin metrics.

    Attributes
    ----------
    created : int
        Number of created events
    """
    created: int
